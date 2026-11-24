GOAL
Maximise pass_rate on the hidden dataset_a/b/c (90-100 questions each, 290 total). For each question, the lens reads Inkling 2 Mini at the last token and reports up to 10 readouts (unique layer labels), each with up to 10 tokens, best first.

FACTS FROM THE REPO (verify, don't assume)
- 24 layers. Layers 6-17 run 3 times, giving 48 visits (0-47). lenses.visit_address maps visit to (layer, run). tracer.iter[run] picks the run.
- Starter: logit lens = lm_head(final_norm(h)), already normed. VISITS = [12, 24, 34, 35, 36, 43, 44, 45, 46, 47]. 25 questions per request. About 100 s per dataset.
- Scoring: each readout votes for the option named by its highest-ranked token that names one. A readout naming no option casts no vote. The intermediate must STRICTLY beat every other option; ties fail. So extra readouts only help when they agree.
- In the PRACTICE set the intermediate IS the final answer, read just before the model writes it. In other scored sets it is often something worked out on the way and never written. So a lens tuned only on practice will mislead us. Late visits help on practice and may vote for the wrong option on the hidden sets.
- Local scoring is exact match. The leaderboard judge also accepts inflections and translations, and flips 1-2 verdicts per few hundred between runs. One practice question = 0.10, so never treat a one-question change as signal.
- Practice answers for analysis only: .leaderboard/data/practice/private/questions.jsonl (has intermediate and options).
- model_input may be a raw prompt OR a chat-formatted prompt with the reply started. Handle both.

HARD CONSTRAINTS
1. Readouts must come from the model's activations. No other model, nothing computed from the prompt text (no arithmetic, lookups, or rules keyed on text or id), no answer tables, no attempts to extract hidden questions. If you're unsure whether something counts, STOP and ask me; I'll ask the organisers. Filtering out tokens that appear in the prompt is in this unsure category: default OFF.
2. Only packages from plain `uv sync`. Always run with .venv/bin/python.
3. submission/ at most 200 MB. Requests are about 1 MB, so trained weights go to the HF Hub as safetensors, are loaded with lenses.fetch once per request at the top of the session, and get moved to the activation's device and dtype.
4. Whole run under 45 minutes for all datasets. Send back token ids only. Never save logits or hidden states in the entry. One forward pass per question, visits read in ascending order.
5. The entry must not depend on DATASET_NAME being a known name, and it must exit 0 on every dataset.
6. Add a retry (with backoff, about 3 tries) around each NDIF request, because one failed request fails the whole submission.
7. Don't edit submission/ while a run is going.
8. Don't modify questions.py, submit.py, runner/, evaluator/, final-evals/, space/, infra/, or competition.yaml. Never run manage.py.
9. Secrets: NDIF_API_KEY and HF_TOKEN come from the environment or the gitignored .env. Never print, log, commit, or write them into submission/ (it's uploaded and published under MIT). HF_TOKEN must be a read-only token. Grep submission/ for key-like strings before any submit.
10. NEVER run `submit.py` without --local unless I type "submit". There's one submission per 2 hours, and a failed one still uses the attempt.

GATES (stop and report after each, tables first)

Gate 0: Baseline
- .venv/bin/python submit.py --local
- Report: pass rate, wall time, and a per-question table (id | type | intermediate | options | which visits voted for what | pass/fail), using .leaderboard/data/practice/private/questions.jsonl.
- Say which practice question types fail (athlete, landmark, musician, arith, dayafter, daybefore, monthafter) and give your best guess why, from the readouts.

Gate 1: Our own question sets (the most important gate)
- Write 3 dev sets of about 60-100 questions each, in the same jsonl format (id, model_input, read_position = last index, read_token) plus our own intermediate and 4 distractors:
  (a) practice-like: the intermediate is the answer about to be written.
  (b) latent two-hop: the intermediate is never written, e.g. "The sport played by the team <athlete> plays for is called" with intermediate = team; "The capital of the country where <landmark> is, is" with intermediate = country; translation hops; simple arithmetic where the intermediate is a partial result.
  (c) mixed formats: raw prompt vs chat format.
  Distractors should include the final answer and an entity from the prompt.
- Keep only questions where the model gets the final answer right (check with a forward pass on NDIF, no generation). Split 70/30 into train and held-out.
- Build a local judge proxy: case-insensitive, strip whitespace and punctuation, simple plural and inflection handling, and the exact voting rule above. Report exact-match and proxy scores.
- Run the starter on each set the way AGENTS.md shows (cd submission; DATASET_NAME=... ../.venv/bin/python main.py).

Gate 2: Visit sweep
- For each dev question, read all 48 visits (over several requests if needed) and record the rank of the intermediate and the final answer at each visit.
- Report, per set: at which visits the intermediate peaks, how loop runs 1/2/3 of the same layer compare, and where the final answer takes over.
- Greedy-search the best visit subset (1-10) for maximum proxy pass rate on train, then check it on held-out. Report it per set, not just overall. Pick a subset that is robust across (a) and (b), not one that's best on (a) alone.

Gate 3: Lens improvements (keep only what wins on held-out, across sets)
a) Token cleanup that uses only model output: drop whitespace or punctuation-only tokens, and dedupe tokens that are the same word with and without a leading space.
b) Tuned lens: per chosen visit, an affine translator (bf16, low-rank if d×d is too big) trained to map that visit's hidden state to final-layer logits (KL), on activations collected from NDIF on generic public text from HF, never our dev questions. Save only the needed visits at the last few positions. Publish to an HF repo I'll name (ask me), and load with lenses.fetch. Report the file size and fetch time.
c) Contrast: mid-visit logits minus a scaled copy of the last-visit logits, to lift latent intermediates. Expect this to hurt set (a), so report per set.
d) Loop pooling: average the 3 runs of a layer as one readout vs separate readouts.
For each variant: proxy pass rate per set (held-out), practice exact-match, seconds per question, size.

Gate 4: Submission candidate
- Freeze the best config. Then:
  - run --local twice;
  - run it once with QUESTIONS_PER_REQUEST below 10 so the between-request code runs;
  - run it on all 3 of our dev sets via main.py;
  - project the runtime for 290 questions with 30% margin;
  - check size under 200 MB, the secret grep, and the validator (one JSON line per id, 1-10 readouts, unique layers, tokens ≤64 chars).
- Write submission/README.md explaining the method plainly (it will be public).
- STOP and give me the config, the numbers and the exact command. Before my first submission, remind me that submitting agrees to publishing under MIT, and ask me for a team name (2-40 chars).

REPORTING
- Only numbers from runs you actually did, with the command and output path. Say clearly when something failed.
- Keep notes/results.md with: variant | visits | proxy (a/b/c held-out) | practice exact | s/question | size.
- Keep reports short: tables first, then open questions for me.
