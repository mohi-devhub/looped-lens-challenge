"""Compare token-structure read positions on the original practice model inputs."""

import argparse
import json
import string
import time
import unicodedata
from collections import Counter
from pathlib import Path

import nnsight
import torch
from nnsight import TransformersModel
from transformers import AutoTokenizer

from judge_proxy import read_questions, score as proxy_score
from lens_eval import evaluate
from practice_rank_sweep import MODEL_ID, ROOT, candidate_ids, lenses


POSITIONS = ("P0", "P1", "P2")
VISIT_SETS = {
    "starter": (12, 24, 34, 35, 36, 43, 44, 45, 46, 47),
    "late": (43, 44, 45, 46, 47),
    "mid-late": (24, 35, 36, 43, 44, 45),
}


def positions(ids, read_position, special_ids):
    assert read_position == len(ids) - 1
    p1 = read_position
    while p1 > 0 and ids[p1] in special_ids:
        p1 -= 1
    return read_position, p1, max(0, p1 - 1)


def excluded_token_ids(tokenizer):
    # Keep the current entry's output filter fixed across the position variants.
    excluded = set(tokenizer.all_special_ids)
    for token_id, token in enumerate(tokenizer.batch_decode([[i] for i in range(len(tokenizer))])):
        text = token.strip()
        if text.startswith("<|") and text.endswith("|>") or all(
            char.isspace() or char in string.punctuation or unicodedata.category(char).startswith("P") for char in text
        ):
            excluded.add(token_id)
    return torch.tensor(sorted(excluded), dtype=torch.long)


def sweep(model, addresses, inputs, excluded_ids, vocabulary_size):
    best = []
    with model.session(remote=True):
        for ids, read_positions, match_ids, literal_ids in inputs:
            with model.trace({"input_ids": ids, "attention_mask": torch.ones_like(ids)}) as tracer:
                per_visit = []
                for layer, run in addresses:
                    for _ in tracer.iter[run]:
                        hidden = lenses.layers(model)[layer].input[0]
                        per_position = []
                        for position in read_positions:
                            scores = lenses.logit_lens(model, hidden[position]).float()
                            targets = match_ids.to(scores.device)
                            highest, index = scores[targets].max(dim=0)
                            literal_highest = scores[literal_ids.to(scores.device)].max()
                            ranks = torch.stack(((scores > highest).sum() + 1,
                                                 (scores > literal_highest).sum() + 1,
                                                 targets[index])).cpu()
                            reportable = scores[:vocabulary_size]
                            reportable.index_fill_(0, excluded_ids.to(scores.device), float("-inf"))
                            per_position.append((ranks, reportable.topk(10).indices.cpu(), scores.numel()))
                        per_visit.append(per_position)
            best.append(per_visit)
        nnsight.save(best)
    return best


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def tally(questions, results):
    summary = dict(passed=0, tied=0, no_votes=0, outvoted=0, wrong_votes=0)
    for result in results:
        q = questions[result["id"]]
        votes = Counter(result["layer_votes"].values())
        gold = votes.pop(q["intermediate"], 0)
        competitor = max(votes.values(), default=0)
        summary["wrong_votes"] += votes.total()
        if result["pass"]:
            assert gold > competitor
            summary["passed"] += 1
        elif competitor == 0:
            assert gold == 0
            summary["no_votes"] += 1
        elif gold == competitor:
            summary["tied"] += 1
        else:
            assert gold < competitor
            summary["outvoted"] += 1
    return summary


def score_configs(questions, rows, output):
    summaries = []
    for visit_set, visits in VISIT_SETS.items():
        assert len(set(visits)) == len(visits)
        for position in (*POSITIONS, "mixed"):
            by_visit = {visit: position for visit in visits}
            if position == "mixed":
                by_visit = {visit: "P0" if visit < 45 else "P1" for visit in visits}
                assert set(by_visit.values()) == {"P0", "P1"}
            name = f"{visit_set}-{position}"
            readouts = [
                {"id": row["id"], "readouts": [
                    {"layer": visit, "tokens": row["positions"][by_visit[visit]]["visits"][visit]["tokens"]}
                    for visit in visits
                ]}
                for row in rows
            ]
            config_dir = output / name
            evaluate(readouts, name=name, model="string-match", questions=questions, out_dir=config_dir)
            exact = [json.loads(line) for line in (config_dir / "results.jsonl").read_text().split("\n") if line]
            proxy = list(proxy_score(questions, readouts))
            assert all(row["status"] == "judged" for row in exact) and not any("reason" in row for row in proxy)
            write_jsonl(config_dir / "proxy.jsonl", proxy)
            record = {"config": name, "positions_by_visit": by_visit,
                      "exact": tally(questions, exact), "proxy": tally(questions, proxy)}
            summaries.append(record)
            print(record, flush=True)
    write_jsonl(output / "config_scores.jsonl", summaries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    questions = read_questions(ROOT / ".leaderboard/data/practice/private/questions.jsonl")
    nnsight.register(lenses)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = TransformersModel(MODEL_ID)
    special_ids = set(tokenizer.all_special_ids)
    matching, literal = candidate_ids(tokenizer, {q["intermediate"] for q in questions.values()})
    excluded_ids = excluded_token_ids(tokenizer)
    addresses = [lenses.visit_address(model.config.text_config, visit) for visit in range(48)]

    def decode(token_id):
        return tokenizer.decode([token_id]) or tokenizer.convert_ids_to_tokens(token_id)

    inputs = []
    rows = []
    for q in questions.values():
        ids = tokenizer.encode(q["model_input"], add_special_tokens=False)
        selected = positions(ids, q["read_position"], special_ids)
        assert decode(ids[selected[0]]) == q["read_token"], q["id"]
        metadata = {name: {"index": index, "token_id": ids[index], "token": decode(ids[index]), "visits": []}
                    for name, index in zip(POSITIONS, selected)}
        print(q["id"], " ".join(f"{name}[{item['index']}]={item['token']!r}" for name, item in metadata.items()), flush=True)
        target = q["intermediate"]
        inputs.append((torch.tensor([ids]), selected, torch.tensor(matching[target]), torch.tensor(literal[target])))
        rows.append({"id": q["id"], "intermediate": target, "positions": metadata})

    started = time.monotonic()
    best = sweep(model, addresses, inputs, excluded_ids, len(tokenizer))
    assert len(best) == len(rows)
    for row, per_visit in zip(rows, best):
        assert len(per_visit) == len(addresses)
        for visit, per_position in enumerate(per_visit):
            assert len(per_position) == len(POSITIONS)
            for name, (ranks, top, logit_count) in zip(POSITIONS, per_position):
                rank, literal_rank, best_form_id = ranks.tolist()
                row["positions"][name]["visits"].append({
                    "visit": visit, "rank": rank, "literal_rank": literal_rank,
                    "best_form": decode(best_form_id), "tokens": [decode(token_id) for token_id in top.tolist()],
                })
        row["logit_count"] = logit_count

    write_jsonl(output / "ranks.jsonl", rows)
    print(f"Wrote {output / 'ranks.jsonl'} in {time.monotonic() - started:.2f} s", flush=True)
    score_configs(questions, rows, output)


if __name__ == "__main__":
    main()
