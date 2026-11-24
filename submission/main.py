"""The starter submission: read one dataset of questions with a logit lens, on NDIF.

The leaderboard starts this file once per dataset, with these environment variables set:

    DATASET_NAME   the dataset's name
    DATASET_PATH   a directory holding questions.jsonl, the questions to read (see questions.py)
    OUTPUT_DIR     where readouts.jsonl goes
    MODEL_ID       the model being read
    NDIF_API_KEY, NDIF_HOST, HF_TOKEN   your credentials; nnsight and huggingface_hub read them

For each question the lens reads the model at one token position, at up to ten layer visits of
its choosing, and reports the ten tokens it finds most likely at each. To submit your own lens:
write a function that turns the state entering a layer visit into what your lens says about it
(lenses.py), call it in the trace where ``lenses.logit_lens`` is called, and choose the visits
it reads.
"""

import os
import string
import time
import unicodedata
from itertools import chain

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

VISITS = [1, 13, 14, 16, 25, 26, 44]
TOP = 10  # tokens reported per visit
CANDIDATES = 128  # filtered token IDs available to refill a readout
QUESTIONS_PER_REQUEST = 25  # one NDIF request runs this many forward passes

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


def deduplicated_readouts(tokenizer, per_visit):
    seen = set()
    readouts = []
    for visit, (top, candidates) in zip(VISITS, per_visit):
        tokens = []
        selected_ids = set()
        for token_id in chain(top.tolist(), candidates.tolist()):
            if token_id in selected_ids:
                continue
            token = questions.token_strings(tokenizer, [token_id])[0]
            if token.strip().casefold() in seen:
                continue
            tokens.append(token)
            selected_ids.add(token_id)
            if len(tokens) == TOP:
                break
        seen.update(token.strip().casefold() for token in tokens)
        readouts.append({"layer": visit, "tokens": tokens})
    return readouts


nnsight.register(lenses)  # the lens functions run on NDIF, so they are shipped with each request
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
vocabulary_size = len(tokenizer)
excluded_ids = excluded_token_ids(tokenizer)
items = questions.load(tokenizer)
model = TransformersModel(MODEL_ID)
# Each visit as (layer, which of that layer's runs): what the trace below asks NDIF for.
addresses = [lenses.visit_address(model.config.text_config, visit) for visit in VISITS]

readouts = {}
for start in range(0, len(items), QUESTIONS_PER_REQUEST):
    batch = items[start : start + QUESTIONS_PER_REQUEST]
    inputs = [(torch.tensor([item.ids]), item.position) for item in batch]

    # One request runs one forward pass per question and saves only token IDs.
    for attempt in range(1, 4):
        best = []
        try:
            with model.session(remote=True):
                for ids, position in inputs:
                    with model.trace({"input_ids": ids, "attention_mask": torch.ones_like(ids)}) as tracer:
                        per_visit = []
                        for layer, run in addresses:
                            for _ in tracer.iter[run]:
                                h = lenses.layers(model)[layer].input[0, position]
                                scores = lenses.logit_lens(model, h).float()[:vocabulary_size]
                                scores.index_fill_(0, excluded_ids.to(scores.device), float("-inf"))
                                per_visit.append((scores.topk(TOP).indices.cpu(), scores.topk(CANDIDATES).indices.cpu()))
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
        readouts[item.id] = deduplicated_readouts(tokenizer, per_visit)
    print(f"{questions.DATASET}: read {min(start + QUESTIONS_PER_REQUEST, len(items))} of {len(items)} questions", flush=True)

questions.write(items, readouts)
print(f"{questions.DATASET}: wrote {len(readouts)} questions at visits {VISITS}")
