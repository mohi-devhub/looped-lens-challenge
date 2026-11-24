"""Read one dataset with a tuned lens at the starter visits on NDIF.

The leaderboard starts this file once per dataset, with these environment variables set:

    DATASET_NAME   the dataset's name
    DATASET_PATH   a directory holding questions.jsonl, the questions to read (see questions.py)
    OUTPUT_DIR     where readouts.jsonl goes
    MODEL_ID       the model being read
    NDIF_API_KEY, NDIF_HOST   used by nnsight for remote execution

At each visit, translate the state at the supplied read position, project it through the
model's final norm and output head, and report the ten highest-scoring eligible tokens.
"""

import json
import os
import string
import time
import unicodedata
from pathlib import Path

import nnsight
import torch
from httpx import HTTPError
from nnsight import TransformersModel
from nnsight.intervention.backends.remote import RemoteError
from transformers import AutoTokenizer
from websocket import WebSocketException

import lenses
import questions

MODEL_ID = os.environ["MODEL_ID"]

VISITS = [12, 24, 34, 35, 36, 43, 44, 45, 46, 47]
TOP = 10  # tokens reported per visit
QUESTIONS_PER_REQUEST = 25  # one NDIF request runs this many forward passes
WEIGHTS = json.loads(Path(__file__).with_name("tuned-weights.json").read_text())

assert VISITS == sorted(set(VISITS)) and len(VISITS) <= questions.MAX_LAYERS, VISITS


def excluded_token_ids(tokenizer):
    excluded = set(tokenizer.all_special_ids)
    tokens = tokenizer.batch_decode([[token_id] for token_id in range(len(tokenizer))])
    for token_id, token in enumerate(tokens):
        text = token.strip()
        if text.startswith("<|") and text.endswith("|>"):
            excluded.add(token_id)
        elif all(char.isspace() or char in string.punctuation or unicodedata.category(char).startswith("P")
                 for char in text):
            excluded.add(token_id)
    return torch.tensor(sorted(excluded), dtype=torch.long)


nnsight.register(lenses)  # the lens functions run on NDIF, so they are shipped with each request
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
vocabulary_size = len(tokenizer)
excluded_ids = excluded_token_ids(tokenizer)
items = questions.load(tokenizer)
model = TransformersModel(MODEL_ID)
# Each visit as (layer, which of that layer's runs): what the trace below asks NDIF for.
addresses = [(visit, *lenses.visit_address(model.config.text_config, visit)) for visit in VISITS]

readouts = {}
for start in range(0, len(items), QUESTIONS_PER_REQUEST):
    batch = items[start : start + QUESTIONS_PER_REQUEST]
    inputs = [(torch.tensor([item.ids]), item.position) for item in batch]

    # One request: everything in this block runs on NDIF, one forward pass per question. Only
    # the ten best token ids per visit come back.
    for attempt in range(1, 4):
        best = []
        try:
            with model.session(remote=True):
                weights = lenses.fetch(WEIGHTS["repository"], WEIGHTS["filename"],
                                       revision=WEIGHTS["revision"])
                translators = {visit: (weights[f"{visit}.down"], weights[f"{visit}.up"], weights[f"{visit}.bias"])
                               for visit, _, _ in addresses}
                for ids, position in inputs:
                    with model.trace({"input_ids": ids, "attention_mask": torch.ones_like(ids)}) as tracer:
                        per_visit = []
                        for visit, layer, run in addresses:
                            for _ in tracer.iter[run]:
                                h = lenses.layers(model)[layer].input[0, position]
                                scores = lenses.tuned_logit_lens(model, h, translators, visit).float()[:vocabulary_size]
                                scores.index_fill_(0, excluded_ids.to(scores.device), float("-inf"))
                                per_visit.append(scores.topk(TOP).indices.cpu())
                    best.append(per_visit)
                nnsight.save(best)
        except (RemoteError, HTTPError, WebSocketException, OSError) as error:
            if attempt == 3:
                raise
            delay = 2 ** attempt
            print(f"NDIF attempt {attempt} failed ({type(error).__name__}). Retrying in {delay}s.", flush=True)
            time.sleep(delay)
        else:
            break

    for item, per_visit in zip(batch, best):
        readouts[item.id] = [{"layer": visit, "tokens": questions.token_strings(tokenizer, token_ids.tolist())} for visit, token_ids in zip(VISITS, per_visit)]
    print(f"{questions.DATASET}: read {min(start + QUESTIONS_PER_REQUEST, len(items))} of {len(items)} questions", flush=True)

questions.write(items, readouts)
print(f"{questions.DATASET}: wrote {len(readouts)} questions at visits {VISITS}")
