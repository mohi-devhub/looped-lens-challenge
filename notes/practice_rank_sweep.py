"""Measure starter logit-lens ranks on the public practice set."""

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import nnsight
import torch
from nnsight import TransformersModel
from transformers import AutoTokenizer

from judge_proxy import normalize, token_key

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "submission"))
import lenses

MODEL_ID = "thinkingmachines/Inkling-2-Mini"
COMPUTATION_TYPES = {"arith", "dayafter", "daybefore", "monthafter"}
TRANSLATIONS = {
    "hockey": "hóquei хоккей хоккея 冰球 アイスホッケー 하키 हॉकी ฮอกกี้ الهوكي",
    "golf": "golfe гольф гольфа 高尔夫 高爾夫 ゴルフ 골프 गोल्फ กอล์ฟ الغولف الجولف",
    "Australia": "Australie Australien Austrália Avustralya Австралия Австралии Австралию 澳大利亚 澳大利亞 澳洲 オーストラリア 호주 오스트레일리아 ऑस्ट्रेलिया أستراليا استراليا ออสเตรเลีย",
    "Poland": "Polen Pologne Polonia Polónia Polônia Polonya Polska Polski Polskę Польша Польши Польше 波兰 波蘭 ポーランド 폴란드 पोलैंड بولندا โปแลนด์",
    "banjo": "banyo банджо 班卓 班卓琴 バンジョー 밴조 बैंजो البانجو แบนโจ",
    "guitar": "guitare Gitarre guitarra chitarra gitaar gitara gitar violão гитара гитаре гитару гитары 吉他 ギター 기타 गिटार الغيتار الجيتار กีตาร์",
}


def candidate_ids(tokenizer, targets):
    english_keys = defaultdict(list)
    extra_keys = defaultdict(list)
    for target in targets:
        english_keys[token_key(target)].append(target)
        for form in TRANSLATIONS.get(target, "").split():
            extra_keys[token_key(form)].append(target)

    matching = {target: [] for target in targets}
    literal = {target: [] for target in targets}
    literals = {target.casefold(): target for target in targets}
    for first in range(0, len(tokenizer), 4096):
        ids = range(first, min(first + 4096, len(tokenizer)))
        for token_id, word in zip(ids, tokenizer.batch_decode([[i] for i in ids])):
            key = token_key(word)
            for target in set(english_keys.get(key, ())) | set(extra_keys.get(key, ())):
                matching[target].append(token_id)
            if target := literals.get(word.strip().casefold()):
                literal[target].append(token_id)
    assert all(matching.values()) and all(literal.values())
    return matching, literal


def sweep(model, addresses, inputs):
    best = []
    with model.session(remote=True):
        for ids, position, match_ids, literal_ids in inputs:
            with model.trace({"input_ids": ids, "attention_mask": torch.ones_like(ids)}) as tracer:
                per_visit = []
                for layer, run in addresses:
                    for _ in tracer.iter[run]:
                        h = lenses.layers(model)[layer].input[0, position]
                        scores = lenses.logit_lens(model, h).float()
                        matching_scores = scores[match_ids.to(scores.device)]
                        highest, index = matching_scores.max(dim=0)
                        literal_highest = scores[literal_ids.to(scores.device)].max()
                        ranks = torch.stack(((scores > highest).sum() + 1,
                                             (scores > literal_highest).sum() + 1,
                                             match_ids.to(scores.device)[index])).cpu()
                        per_visit.append((ranks, scores.topk(100).indices.cpu(), scores.numel()))
            best.append(per_visit)
        nnsight.save(best)
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = ROOT / ".leaderboard/data/practice/private/questions.jsonl"
    questions = [json.loads(line) for line in path.read_text().split("\n") if line.strip()]

    nnsight.register(lenses)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = TransformersModel(MODEL_ID)
    targets = {question["intermediate"] for question in questions}
    matching, literal = candidate_ids(tokenizer, targets)

    def decode(token_id):
        if token_id >= len(tokenizer):
            return f"<unused:{token_id}>"
        return tokenizer.decode([token_id]) or tokenizer.convert_ids_to_tokens(token_id)

    forms = {target: [decode(i) for i in matching[target]] for target in sorted(targets)}
    (args.output_dir / "matched_forms.json").write_text(json.dumps(forms, ensure_ascii=False, indent=2) + "\n")
    addresses = [lenses.visit_address(model.config.text_config, visit) for visit in range(48)]

    for mode in ("practice", "raw"):
        selected = questions if mode == "practice" else [q for q in questions if q["groups"]["kind"] in COMPUTATION_TYPES]
        inputs = []
        for q in selected:
            text = q["model_input" if mode == "practice" else "prompt"]
            ids = tokenizer.encode(text, add_special_tokens=False)
            position = len(ids) - 1
            if mode == "practice":
                assert position == q["read_position"] and decode(ids[position]) == q["read_token"], q["id"]
            target = q["intermediate"]
            inputs.append((torch.tensor([ids]), position, torch.tensor(matching[target]), torch.tensor(literal[target])))

        started = time.monotonic()
        print(f"Measuring {len(inputs)} {mode} inputs at {len(addresses)} visits", flush=True)
        best = sweep(model, addresses, inputs)
        assert len(best) == len(selected)
        output = args.output_dir / f"ranks-{mode}.jsonl"
        with output.open("w") as out:
            for q, (ids, position, _, _), per_visit in zip(selected, inputs, best):
                assert len(per_visit) == len(addresses), q["id"]
                visits = []
                for visit, (ranks, top, vocabulary_size) in enumerate(per_visit):
                    rank, literal_rank, match_id = ranks.tolist()
                    visits.append({"visit": visit, "rank": rank, "literal_rank": literal_rank,
                                   "best_form": decode(match_id), "top_100": [decode(i) for i in top.tolist()]})
                row = {"id": q["id"], "intermediate": q["intermediate"],
                       "read_token": decode(ids[0, position].item()), "read_position": position,
                       "logit_count": vocabulary_size, "visits": visits}
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {output} in {time.monotonic() - started:.2f} s", flush=True)


if __name__ == "__main__":
    main()
