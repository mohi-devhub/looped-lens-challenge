# Lens results

## Leaderboard history

| Entry | Pass rate | Change and takeaway |
| --- | ---: | --- |
| Starter | 0.6619 | The plain logit lens used ten visits at P0 and set the reference score. |
| v0.1 | 0.6411 | Keeping only visits 43–47 with token filtering and retries cost 2.08 leaderboard points despite tying the starter in the dev sweep. |
| v0.2a | 0.6096 | Visit 44 alone led the local comparison and scored lowest on the leaderboard, exposing the dev-set mismatch. |
| v0.5 | 0.6800 | The plain logit lens kept all ten starter visits and added token filtering and retries, producing the best recorded score, 1.81 percentage points above the starter. |

## Local run index

| Variant | Visits | Proxy (a/b/c held-out) | Practice exact | s/question | Size |
| --- | --- | --- | --- | --- | --- |
| Starter logit lens | 12, 24, 34, 35, 36, 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 4.16 (wall time) | 9,404 bytes of source |
| Starter logit lens (session rerun) | 12, 24, 34, 35, 36, 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 4.58 (wall time) | 9,404 bytes of source |
| Starter with token filtering | 12, 24, 34, 35, 36, 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 2.79 (wall time) | 10,205 bytes of source |
| Calibration v0.1 | 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 4.61 (wall time) | 5,232-byte ZIP |
| Proposed v0.2, filtered with cross-visit deduplication | 1, 13, 14, 16, 25, 26, 44 | 44.00% / 48.28% / 73.08% | — | — | — |
| v0.2a, filtered | 44 | 44.00% / 44.83% / 69.23% | 6/10 | 3.04 (dev wall time) | 5,173-byte ZIP |
| v0.2b, filtered with cross-visit deduplication | 1, 13, 14, 16, 25, 26, 44 | 44.00% / 44.83% / 73.08% | 6/10 | 4.27 (dev wall time) | 5,476-byte ZIP |

## Gate 0

`uv sync` succeeded. The initial `.venv/bin/python submit.py --local` attempt
exited with code 1 after 42.98 seconds of wall time. NDIF rejected the first
practice request with HTTP 401 because the API key was missing.

The rerun with the key from the gitignored `.env` exited 0 after 41.63 seconds
of wall time. Both questions in each of athlete, landmark, and musician passed.
The one question in each of arith, dayafter, daybefore, and monthafter received
zero votes and failed.

The initial attempt log is `.leaderboard/gate-0-baseline.log`. The rerun console
log is `.leaderboard/gate-0-rerun.log`. The rerun wrote
`.leaderboard/outputs/practice/readouts.jsonl`. The exact-match question and
visit breakdown is in `.leaderboard/gate-0-exact-breakdown/comparison.jsonl`,
using the answers from `.leaderboard/data/practice/private/questions.jsonl`.

### Session rerun

`.venv/bin/python submit.py --local` exited 0 in 45.76 seconds of wall time.
The NDIF key came from the gitignored `.env`, and `LENS_EVAL_JUDGE=string-match`
selected the same judge used in the earlier baseline. Athlete, landmark, and
musician passed both questions each. Arith, dayafter, daybefore, and monthafter
received zero votes each. Their late readouts primarily surfaced task words such
as `arithmetic`, `week`, and `calendar`. Visit 47 ranked the thinking delimiter
first on all four. Daybefore surfaced `суббота` (Saturday) at visit 36, which
fell outside the exact-match judge's English option matching.

- [Console log](../.leaderboard/gate-0-session-rerun.log)
- [Readouts](../.leaderboard/gate-0-session-breakdown/submissions.jsonl)
- [Exact-match votes](../.leaderboard/gate-0-session-breakdown/results.jsonl)

## Gate 0.5

| Variant | Practice exact | Practice proxy |
| --- | --- | --- |
| Original Gate 0 readouts | 6/10 | 6/10 |
| Special, punctuation-only and whitespace-only tokens filtered | 6/10 | 6/10 |

`.venv/bin/python notes/practice_rank_sweep.py --output-dir .leaderboard/gate-0-5`
measured all 48 starter logit-lens visits for the 10 practice inputs and 4 raw
controls in 77.26 seconds. A rank is one plus the count of logits strictly above
the highest-scoring recognized single-token form in the 200,058-token output.
The files also record literal ranks and the top 100 tokens. The aliases cover
the surface forms listed in the matched vocabulary file.

The best ranks on the four chat inputs were 16 at visit 22 for arithmetic, 14
at visit 36 for day-after, 7 at visit 36 for day-before, and 106 at visit 43 for
month-after. Both weekday peaks were `суббота`. All ten chat inputs ended in
`<|message_model|>` and visit 47 put `<|content_thinking|>` first on each. Reading
at the final `.` of the raw prompt raised the four best ranks to 4, 1, 6, and 2.
The raw controls change both the wrapper and the read position.

`.venv/bin/python submit.py --local` with token filtering exited 0 in 27.86
seconds. `.venv/bin/python notes/judge_proxy.py` re-scored both saved readout
files against the practice answers. The day-before question tied under the
proxy, with a Friday vote at visit 24 and a Saturday vote at visit 36.

- [Sweep log](../.leaderboard/gate-0-5/sweep.log)
- [Chat ranks](../.leaderboard/gate-0-5/ranks-practice.jsonl) and [raw ranks](../.leaderboard/gate-0-5/ranks-raw.jsonl)
- [Matched vocabulary forms](../.leaderboard/gate-0-5/matched_forms.json)
- [Filtered run log](../.leaderboard/gate-0-5/filtered-local.log) and [readouts](../.leaderboard/gate-0-5/exact-filtered/submissions.jsonl)
- [Original proxy votes](../.leaderboard/gate-0-5/proxy-baseline.jsonl) and [filtered proxy votes](../.leaderboard/gate-0-5/proxy-filtered.jsonl)

## Gate 0.6

`.venv/bin/python notes/practice_position_sweep.py --output-dir .leaderboard/gate-0-6`
exited 0 in 40.95 seconds. It read all 48 visits at three positions in one
forward pass per original practice input. All ten decoded as P0
`<|message_model|>`, P1 `.`, and P2 ` word`. P0 reproduced the Gate 0.5 ranks
and the current filtered starter readouts exactly. Ranks used all 200,058
logits, and scoring used the current output filter.

| Position | Starter exact / proxy | Late exact / proxy | Mid + late exact / proxy |
| --- | --- | --- | --- |
| P0 | 6/10 / 6/10 | 6/10 / 6/10 | 6/10 / 6/10 |
| P1 | 0/10 / 0/10 | 0/10 / 0/10 | 0/10 / 0/10 |
| P2 | 0/10 / 0/10 | 0/10 / 0/10 | 0/10 / 0/10 |
| Mixed, P0 through visit 44 and P1 from visit 45 | 6/10 / 6/10 | 6/10 / 6/10 | 6/10 / 6/10 |

P1 and P2 cast zero votes in all three sets under either judge. The P0 and
mixed versions of starter and mid + late each had one exact distractor vote,
and one positive tie and two distractor votes under the proxy. The late set
at P0 or mixed had zero ties and distractor votes. A tie is a question whose
intermediate shares the highest positive vote count with a distractor.

At P1 the four computation questions peaked at ranks 13, 77, 104, and 419,
respectively. The three calendar questions reached the top 10 in the Gate 0.5
raw controls. Reading the period inside the original chat yielded weaker
ranks than reading the same decoded token in the raw input.

- [Decoded tokens and sweep log](../.leaderboard/gate-0-6/sweep.log)
- [All ranks and filtered readouts](../.leaderboard/gate-0-6/ranks.jsonl)
- [Full scoring counts and position assignments](../.leaderboard/gate-0-6/config_scores.jsonl)
- [Read-position decision](open_questions.md)

## Gate 0.7

| Run | Questions | Exact | Practice proxy | Wall time |
| --- | ---: | ---: | ---: | ---: |
| Practice, default batch size 25 | 10 | 6/10 | 6/10 | 46.06 s |
| Practice, batch size 4 with injected failures | 10 | 6/10 | 6/10 | 38.00 s |
| Mini set through `submission/main.py` | 10 | — | — | 51.70 s |

The candidate reads visits 43 through 47 at `read_position` and keeps the
Gate 0.5 token filter. Each NDIF batch gets up to three attempts. The batch-size-four
run used a temporary copy of the entry and injected a `RemoteError` and a
`WebSocketConnectionClosedException` into the second batch. The entry waited
two seconds and then four seconds, recovered on attempt three, and finished
all three batches. Its readouts matched the default practice run byte for byte.

The mini set had five raw inputs and five chat inputs. Two asked for a final
answer distinct from the intermediate, an arithmetic partial result and a
country in a capital lookup. The competition validator accepted all three
outputs. Each had ten distinct question IDs and five unique visits per ID,
with ten tokens of at most 64 characters per visit. The submission directory
was 19,179 bytes on disk. `submit.package` produced a 5,232-byte ZIP with
10,731 bytes of uncompressed files. The key-pattern grep and configured
credential scan passed, and Git ignored `.env`.

The runtime projection is 32 min 29 s for 290 questions with a 30% margin.
It scales the slower default-size run, the 51.70 s mini set, and charges a
fresh process and request per ten questions.

- `.venv/bin/python submit.py --local` [log](../.leaderboard/gate-0-7/default/run.log) · [readouts](../.leaderboard/gate-0-7/default/readouts.jsonl) · [proxy votes](../.leaderboard/gate-0-7/default/proxy.jsonl)
- `.venv/bin/python submit.py --local --submission .leaderboard/gate-0-7/batch4-entry` with `.leaderboard/gate-0-7/faults` on `PYTHONPATH` [log](../.leaderboard/gate-0-7/batch4/run.log) · [readouts](../.leaderboard/gate-0-7/batch4/readouts.jsonl) · [proxy votes](../.leaderboard/gate-0-7/batch4/proxy.jsonl)
- `../.venv/bin/python main.py` from `submission/` with `DATASET_NAME=calibration_mini` and the temporary input and output directories [log](../.leaderboard/gate-0-7/mini-0ezgearn/run.log) · [readouts](../.leaderboard/gate-0-7/mini-0ezgearn/output/readouts.jsonl)
- [Validation log](../.leaderboard/gate-0-7/validation.log)

## Gate 1

The reported leaderboard scores were 0.6619 for the starter and 0.6411 for
late-only v0.1. The dev sets determine the next visit selection.

| Set | Kept | Train / held-out | Raw / chat | Composition |
| --- | ---: | ---: | ---: | --- |
| A, practice-like | 84 | 59 / 25 | 0 / 84 | 32 facts, 28 arithmetic, 12 weekday, 12 month |
| B, latent | 96 | 67 / 29 | 43 / 53 | 34 arithmetic partials, 30 unit conversions, 14 calendar offsets, 18 geography two-hop |
| C, paired formats | 84 | 58 / 26 | 42 / 42 | 22 facts, 22 arithmetic, 20 weekday, 20 month |

`.venv/bin/python notes/dev_gate.py --output-dir .leaderboard/gate-1 --batch-size 96`
checked a top-1 next-token answer on NDIF. Chat answer checks supplied
`<|content_text|>` at the start of the reply. Full sweeps use the original
chat input up to `<|message_model|>` with thinking effort zero. Raw inputs end
at their answer lead-in. The two formats of each C prompt share a split and
both had to pass verification to be retained. The held-out split contains
new items from shared task templates.

The initial answer checks were stopped after 64 items because the default
thinking effort and cloze wording often elicited sentence restatements. A
second pass checked 446 single-token candidates. The refinement rechecked 127
items after revising raw numeric answer lead-ins and latent calendar prompts.
Final eligibility was 87 A, 116 B, and 144 C items before sampling. All 264
retained top-1 predictions matched the expected answers after case and
whitespace normalization.

The original `submission/main.py` from the parent of `6367e07` exited 0 on
all three sets. I ran it with each `input/` directory as `DATASET_PATH`,
`DATASET_NAME=dev_a`, `dev_b`, or `dev_c`, and the corresponding `starter/`
directory as `OUTPUT_DIR`. Held-out exact and proxy both returned 11/25 on A,
3/29 on B, and 19/26 on C.

- [Dataset manifest](../.leaderboard/gate-1/manifest.json)
- [Initial format check](../.leaderboard/gate-1-initial/verify.log), [answer checks](../.leaderboard/gate-1/verify.log), and [refined checks](../.leaderboard/gate-1/verify-refined.log)
- [Independent starter scores](../.leaderboard/gate-1/starter-scores.json) and run logs for [A](../.leaderboard/gate-1/a/starter/run.log), [B](../.leaderboard/gate-1/b/starter/run.log), and [C](../.leaderboard/gate-1/c/starter/run.log)

## Gate 2

| Configuration | Held-out A | Held-out B | Held-out C | Macro proxy |
| --- | ---: | ---: | ---: | ---: |
| Starter, raw, same sweep | 11/25 | 3/29 | 18/26 | 41.19% |
| v0.1, filtered, same sweep | 11/25 | 3/29 | 18/26 | 41.19% |
| Starter, independent `main.py` run | 11/25 | 3/29 | 19/26 | 42.47% |
| Raw, softmax, or filtered without deduplication at 44 | 11/25 | 14/29 | 18/26 | 53.84% |
| Proposed v0.2, filtered with deduplication at 1, 13, 14, 16, 25, 26, 44 | 11/25 | 14/29 | 19/26 | 55.12% |

Exact matching produced the same counts for these rows. The same-run proxy
tied the known configurations. The independent starter run gained one C
question. Across the independent run and sweep, 1,219 of 2,640 ordered
starter readouts differed and just one question changed its proxy verdict.
The leaderboard separated the starter and v0.1 by 0.0208 while the same-run
proxy tied them. Treat differences under about five percentage points on
this proxy as noise for submission decisions.

| Set | Best median rank | Top 100 at visit 44 | Top 100 by loop run 1 / 2 / 3 |
| --- | ---: | ---: | ---: |
| A | 59 at 44 | 56.0% | 1.8% / 3.5% / 7.5% |
| B | 3 at 44 | 66.7% | 6.1% / 4.8% / 6.7% |
| C | 1 at 44 | 85.7% | 1.3% / 3.7% / 16.7% |

On B, the final answer reached the top 10 more often than the intermediate
at visits 42, 43, and 45 through 47. Visit 44 alone passed 11 more latent
questions than v0.1 did. These comprised five arithmetic partials, five unit
conversions, and one weekday offset. The seven-visit proposal added one C
chat fact over visit 44 alone.

Raw logits and float32 softmax returned identical ordered top-10 IDs on all
12,672 question-visits. Filtering changed 10,441 lists and tied raw scores
at the best plain configuration and the starter and v0.1 visit sets.
Deduplication keeps each token surface form at its earliest selected visit
after case and whitespace normalization, and backfills later readouts from
their top 128 filtered tokens. It reduced macro proxy to 20.72% on the
starter visits and 29.35% on the v0.1 visits. All selected held-out readouts
refilled to ten tokens.

The 1–10 visit greedy paths used train macro proxy as the objective. Held-out
macro proxy selected the mode and prefix among those paths. A separate greedy
fit directly on held-out also peaked at 55.12%, first reached with filtered
deduplication at visits 38 and 44. The seven-visit proposal comes from the
train path. The held-out comparison is a selection estimate on shared task
templates, with 1.28 macro points over the single-visit candidate.

- `.venv/bin/python notes/dev_sweep.py --data-dir .leaderboard/gate-1 --output-dir .leaderboard/gate-2 --batch-size 32 --sets SET` [A log](../.leaderboard/gate-2/sweep-a.log) · [B log](../.leaderboard/gate-2/sweep-b.log) · [C log](../.leaderboard/gate-2/sweep-c.log)
- `.venv/bin/python notes/dev_scores.py --data-dir .leaderboard/gate-1 --sweep-dir .leaderboard/gate-2 --output-dir .leaderboard/gate-2/analysis` [scores and search paths](../.leaderboard/gate-2/analysis/scores.json) · [all ranks by visit](../.leaderboard/gate-2/analysis/rank-by-visit.csv) · [same-layer loop comparison](../.leaderboard/gate-2/analysis/rank-summary.json)

## Set A audit

| Cohort | Facts | Median rank at visit 44 | Fact median rank at visit 44 | Facts in top 10 at visit 44 |
| --- | ---: | ---: | ---: | ---: |
| Public practice | 6/10 | 4 | 1 | 6/6 |
| Original A | 32/84 | 59 | 1 | 22/32 |
| Practice-aligned A | 37/65 | 47 | 3 | 25/37 |

Both cohorts use thinking effort zero, the same user and assistant delimiters,
and `<|message_model|>` as the final token. Neither sweep supplied an assistant
content delimiter. The original A fact prompts were longer cloze questions
with a median of 39 input tokens versus 29.5 for the practice facts. They also
spanned more topics than the practice athlete, landmark, and musician items.

Original A had 52 computation questions, including 28 sums. The computation
median at visit 44 was 1,170 in A and 193.5 in practice. Reweighting the original
A ranks to a 60% fact, 40% computation mix drops its weighted median to 7 with
the scores held fixed. The rank-59 aggregate mainly reflected the mix.

The practice-aligned set uses new direct questions in the public practice
templates. It retained 65 verified questions, with 46 train and 19 held-out.
It has 11 athletes, 14 landmarks, and 12 musicians, plus 8 single-digit
subtractions, 6 day-after, 6 day-before, and 8 month-after items. The final
verified mix is 57% facts. Model inputs use the same wrapper and `Answer in
one word.` instruction as practice, and the lens still reads P0. I kept
the original A and Gate 2 results for comparison. The local `.leaderboard/dev-v2`
dataset root points to practice-aligned A and the original B and C.

At visit 44, 11/11 revised athlete, 6/14 landmark, 8/12 musician, and 0/28
computation intermediates made the top 10. The median computation rank was
358.5. The remaining aggregate gap comes from weaker landmark and musician
ranks plus computation items outside the top 10. Practice had two examples
from each fact category and all six made the top 10.

- `.venv/bin/python notes/practice_aligned.py --output-dir .leaderboard/gate-4/a-revised` [verification and sweep log](../.leaderboard/gate-4/a-revised.log) · [visit 44 ranks](../.leaderboard/gate-4/a-revised/ranks-44.jsonl)

## Gate 4

| Check | v0.2a | v0.2b |
| --- | ---: | ---: |
| Practice, exact and proxy | 6/10 twice | 6/10 twice |
| Practice wall time | 62.80 s, 70.94 s | 85.61 s, 89.90 s |
| Batch size four, exact and proxy | 6/10 in 229.57 s | 6/10 in 275.78 s |
| Original A, held-out | 11/25 | 11/25 |
| B, held-out | 13/29 | 13/29 |
| C, held-out | 18/26 | 19/26 |
| Original A/B/C mean proxy | 52.69% | 53.97% |
| Practice-aligned A, held-out | 8/19 | 9/19 |
| Practice-aligned A/B/C mean proxy | 52.05% | 55.09% |
| ZIP size | 5,173 bytes | 5,476 bytes |
| Projected runtime for 290 questions with 30% margin | 19 min 6 s | 26 min 48 s |

Both candidates read P0 and retain the token filter and three-attempt NDIF
retry. v0.2a reads visit 44 alone. v0.2b uses the seven visits from Gate 2 and
refills deduplicated readouts from up to 128 filtered candidates. Its readout
selection matched the Gate 2 implementation on all 264 cached dev inputs.

Two `submit.py --local` runs and a batch-size-four run using a temporary
`--submission` copy completed on each branch. Fault injection forced two
failures in the second batch. Both entries waited two and four seconds,
recovered on attempt three, and wrote all ten practice outputs. Both branches
also ran through `submission/main.py` on the original A, B, C, and
practice-aligned A. Exact and proxy counts agreed on every run. The validator
checked 718 question rows across 14 runs for IDs, visit labels, token count,
and token length. It also checked cross-visit uniqueness for v0.2b.

The key-pattern grep and configured-credential scan passed for both entries.
Git ignores `.env`. The runtime projection scales the sum of the original
A/B/C wall times from 264 to 290 questions and adds 30%. Those times include
the observed NDIF queue waits. The v0.2b edge is 1.28 points on the original
sets and 3.04 points with revised A. Both fall inside the five-point noise rule.

- `.venv/bin/python .leaderboard/gate-4/run_checks.py` and `.venv/bin/python .leaderboard/gate-4/run_checks.py --revised --workers 2` [summary](../.leaderboard/gate-4/summary.json) · [v0.2a runs](../.leaderboard/gate-4/runs/a) · [v0.2b runs](../.leaderboard/gate-4/runs/b) · [package report](../.leaderboard/gate-4/package-report.json)

## Real-judge calibration

| Entry | Practice | Dev A / B / C held-out | Held-out macro | All-dev macro | Held-out exact, same readouts |
| --- | ---: | ---: | ---: | ---: | ---: |
| Starter | 6/10 | 10/19 · 3/29 · 19/26 | 45.35% | 43.58% | 43.60% |
| v0.1 | 6/10 | 8/19 · 3/29 · 18/26 | 40.56% | 43.34% | 41.84% |
| v0.2a | 6/10 | 8/19 · 13/29 · 18/26 | 52.05% | 53.22% | 52.05% |
| v0.2b | 5/10 | 7/19 · 13/29 · 19/26 | 51.58% | 50.80% | 55.09% |

The reported leaderboard order was starter 0.6619, v0.1 0.6411, and v0.2a
0.6096. The real judge puts the starter above v0.1 on both dev comparisons,
and still ranks v0.2a above both. The search condition failed, so this run
ends with the calibration and citation audit.

`uv sync --group evaluator` installed the judge SDK. The calibration used
OpenAI `gpt-6-luna`, prompt version `j3-v3`, the official prompt builder,
citation validator, and plurality scoring. It used public practice metadata
as supplied and authored task descriptions for the dev sets. The four entries
each scored all ten public practice questions and all 245 `dev-v2` questions.
The missing starter A and v0.1 A/B/C readouts were captured from the frozen
entries via `main.py`.

Visits 6 through 41 had 173 distinct accepted citation occurrences beyond
exact matching, 118 beyond the limited proxy. Examples include `Polish` for
Poland at visit 24, `Australian` and Hindi `ऑस्ट्रेलिया` for Australia at
visit 24, `German` for Germany at visit 36, and Armenian `կիրակի` for Sunday
at visit 24. The limited proxy already accepts Russian `суббота` for Saturday
and `пятница` for Friday. Both received a vote on the same practice item.

Removing mid-visit citations the limited proxy missed changed the starter's
effective votes on 11 dev readouts, six toward the target and five toward
distractors. It left all starter dev verdicts unchanged. For v0.2b those
citations swung six dev verdicts, one gain and five losses. `French` for
France at visit 16 also cost v0.2b a practice pass. The judge's wider coverage
changes ballots in both directions and leaves the ranking mismatch intact.

The 1,020 responses used 881,281 input tokens and 295,996 output tokens. At
standard prices the measured-usage estimate was $0.2361. One unresolved
attempt reserved up to $0.00349. The conservative total booked against the
cap was $0.26165. [OpenAI GPT-6 Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)

- `.venv/bin/python notes/real_judge_calibration.py --cohorts practice` and `.venv/bin/python notes/real_judge_calibration.py --cohorts a b c --concurrency 40` [real scores](../.leaderboard/judge-calibration/openai/summary.json) · [same-readout exact scores](../.leaderboard/judge-calibration/string-match/summary.json) · [mid-visit citations](../.leaderboard/judge-calibration/openai/mid-citations.csv) · [usage ledger](../.leaderboard/judge-calibration/spend.jsonl)

## Gate 3b public material and training

The public README gives athlete-to-sport recall as a practice example. It
describes phase-one tasks as simple problems with a single-token intermediate,
with harder tasks in later phases. The judge documentation mentions whole-number
options and shows examples of translations, derived words, and word fragments.
The example lens explains the fixed visit sequence and distinguishes the model's
actual next-token output from an intermediate readout. The public files give
no category mapping for hidden A, B, or C. Per-question task descriptions and
rules for scored data are private. [Participant guide](../README.md) · [Judge prompt](../final-evals/judge_prompts/system_mc.txt) · [Example lens](../final-evals/examples/naive_logit_lens.py)

The starter visits are frozen at 12, 24, 34, 35, 36, and 43 through 47. The
training input is a seeded sample from WikiText-2 raw train and validation
splits. The capture saves the input to each visit and the final normalized
state at the last eight positions of each passage. The local decoder uses
the public final norm and output head and reproduces the model's logit soft
cap for full-vocabulary KL. The raw tensor downloads are local training inputs.
[WikiText-2](https://huggingface.co/datasets/Salesforce/wikitext)

| Training measurement | Result |
| --- | ---: |
| NDIF sample | 44 passages, 352 positions |
| Split | 256 train / 96 validation positions |
| NDIF execution across four requests | 56.30 s |
| Collection wall time | 423.60 s |
| Captured tensor files | 21,051,507 bytes |
| Local training | 50.79 s on MPS |
| Mean validation KL across the ten visits | 7.1298 → 3.7441 |
| Exported bfloat16 safetensors file | 1,523,128 bytes |

Each adapter computes `h + (h @ down) @ up + bias` with rank 16. The fixed
five-epoch fit selected a bfloat16 checkpoint for each visit using WikiText
validation KL. All ten visits improved on that split. The local head check
matched eight of eight NDIF teacher argmaxes with mean KL 0.000233 on the
eight anchor positions. The head and norm ranged download transferred
921,871,872 bytes in 238.80 seconds from the public checkpoint. Those base
tensors stay local and are excluded from the translator artifact.

- `.venv/bin/python notes/tuned_lens_collect.py --output-dir .leaderboard/tuned-lens` [capture log](../.leaderboard/tuned-lens/collect.log)
- `.venv/bin/python notes/tuned_lens_head.py --output-dir .leaderboard/tuned-lens` [public head download log](../.leaderboard/tuned-lens/head-fetch.log)
- `.venv/bin/python notes/tuned_lens_train.py --output-dir .leaderboard/tuned-lens` [per-visit KL and times](../.leaderboard/tuned-lens/fit.json) · [trained weights](../.leaderboard/tuned-lens/tuned-v0.3.safetensors)

The v0.3 entry uses the frozen starter visits, the supplied read position,
output-token filtering, and the three-attempt retry. The MIT model card and
weights were published together at revision
`56c538ed670e3cbbdbf264c1c2ab633b8f254ae4`. An anonymous local download
matched the export's SHA-256 and took 3.73 seconds. The NDIF smoke test
fetched and decoded all 30 tensors anonymously in 0.39 seconds. Its full
request took 50.50 seconds including the NDIF queue.
[Public model card](https://huggingface.co/achu-mohith/inkling2-mini-tuned-lens/tree/56c538ed670e3cbbdbf264c1c2ab633b8f254ae4)

- `.venv/bin/python notes/tuned_lens_publish.py achu-mohith/inkling2-mini-tuned-lens --root .leaderboard/tuned-lens --entry .leaderboard/tuned-lens/entry/submission --card .leaderboard/tuned-lens/model-card.md` [publication record](../.leaderboard/tuned-lens/publication.json)
- `.venv/bin/python notes/tuned_lens_fetch_check.py --entry .leaderboard/tuned-lens/entry/submission --output .leaderboard/tuned-lens/ndif-fetch.json` [NDIF fetch measurement](../.leaderboard/tuned-lens/ndif-fetch.json)

## Gate 4 v0.3

| Variant | Visits | Proxy A / B / C held-out | Practice exact | Dev s/question | Entry ZIP |
| --- | --- | ---: | ---: | ---: | ---: |
| v0.3, tuned and filtered | 12, 24, 34, 35, 36, 43–47 | 8/19 · 3/29 · 18/26 | 6/10 | 3.25 | 5,675 bytes |

| Gate 4 run | Exact | Wall time |
| --- | ---: | ---: |
| Practice 1 | 6/10 | 67.69 s |
| Practice 2 | 6/10 | 64.33 s |
| Practice, batch size four | 6/10 | 192.92 s |
| Dev A | 29/65 | 206.82 s |
| Dev B | 9/96 | 300.89 s |
| Dev C | 61/84 | 288.62 s |

All six runs exited 0 and the validator accepted all 275 output lines.
Each line had ten distinct visits and ten tokens per visit. All tokens
fit the 64-character limit and passed the output filter. The batch-size-four
test recovered from an injected `RemoteError` and a
`WebSocketConnectionClosedException` after waits of two and four seconds.
The sum of the three dev wall times, scaled from 245 questions to 290 and
padded by 30%, gives 20.42 minutes against the 45-minute limit. The archive
passed the configured credential scan and the `hf_` and `sk-` grep.
`.env` is ignored.

| Official judge | Starter, all | v0.3, all | Starter, held-out | v0.3, held-out |
| --- | ---: | ---: | ---: | ---: |
| Practice | 6/10 | 6/10 | | |
| Dev A | 31/65 | 32/65 | 10/19 | 9/19 |
| Dev B | 10/96 | 10/96 | 3/29 | 3/29 |
| Dev C | 61/84 | 61/84 | 19/26 | 18/26 |
| Held-out macro | | | 45.35% | 42.31% |

The comparison used the captured starter readouts and their cached
`gpt-6-luna` verdicts. The v0.3 run graded all 255 readouts with the same
prompt and scorer. The estimated spend from actual token usage was
$0.08328. The conservative budget charge was $0.08959 against the $2 cap.
[OpenAI GPT-6 Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna)

- `.venv/bin/python .leaderboard/tuned-lens/checks.py` ran both `submit.py --local` checks, the batch-size-four `--local` check, and `main.py` on dev A, B, and C. [Run logs and outputs](../.leaderboard/tuned-lens/runs/tuned) · [Validation and runtime summary](../.leaderboard/tuned-lens/gate4-summary.json) · [Package report](../.leaderboard/tuned-lens/package-report.json)
- `.venv/bin/python notes/tuned_lens_sanity.py --readouts .leaderboard/tuned-lens/runs/tuned --output .leaderboard/tuned-lens/real-judge` [Judge summary](../.leaderboard/tuned-lens/real-judge/summary.json) · [Usage ledger](../.leaderboard/tuned-lens/real-judge/spend.jsonl)

## v0.4 scaled tuned lens

The public WikiText-2 raw sample is fixed at 160 training passages and 40
held-out passages. Each passage has 256 token positions, for 51,200 total.
One quarter of each split uses the Inkling chat template with the assistant
reply started. NDIF captures all positions at the ten starter visits and
the final normalized state. The local shards store BF16 losslessly. Writes
check a 5 GB free-space floor.

The 25 completed shards contain 51,200 positions and occupy 1,816,805,812
bytes. NDIF reports 261.76 seconds of execution for those shards. Collection
took 1,990.52 seconds elapsed, including the queue and result downloads.
Four slow single-stream transfers were restarted with verified HTTP range
downloads. The reported execution total covers the completed shards.
The disk check after collection showed 7.22 GB free.
[Collection summary](../.leaderboard/tuned-lens-v04/collection-summary.json)

The local MPS fit uses rank-256 residual affine translators, two passes
over the training split, and full-vocabulary KL to Inkling's soft-capped
final distribution. The held-out split is reserved for comparing the
plain lens, v0.3, and v0.4 after the fit.

- `.venv/bin/python notes/tuned_lens_scale_collect.py --output-dir .leaderboard/tuned-lens-v04 --head-dir .leaderboard/tuned-lens --first-only` [Pilot capture](../.leaderboard/tuned-lens-v04/capture-pilot.log) · [Public corpus manifest](../.leaderboard/tuned-lens-v04/corpus.json)
- `.venv/bin/python notes/tuned_lens_range_fetch.py --output-dir .leaderboard/tuned-lens-v04 160` [Verified range download](../.leaderboard/tuned-lens-v04/range-pilot.log)
- `.venv/bin/python notes/tuned_lens_scale_train.py --output-dir .leaderboard/tuned-lens-v04 --head-dir .leaderboard/tuned-lens --rank 256 --epochs 2 --batch-size 32` [Training log](../.leaderboard/tuned-lens-v04/train.log)

The two epochs used all 40,960 training positions each. The timed
shard fit steps took 1,720.30 seconds on the local M4 GPU, and evaluation
took 295.42 seconds. The finished BF16 export is 23,641,656 bytes.
The reconstructed teacher agreed with NDIF's top token on the anchor,
with KL 0.00007157.

| Visit | Plain KL | v0.3 KL | v0.4 KL | Reduction vs plain |
| ---: | ---: | ---: | ---: | ---: |
| 12 | 11.7626 | 5.4471 | 3.4474 | 70.7% |
| 24 | 10.0152 | 5.6593 | 3.5797 | 64.3% |
| 34 | 10.3223 | 5.5777 | 3.2381 | 68.6% |
| 35 | 8.9562 | 5.5148 | 3.2020 | 64.2% |
| 36 | 9.8993 | 5.4168 | 3.0189 | 69.5% |
| 43 | 6.9301 | 4.1178 | 2.3397 | 66.2% |
| 44 | 5.8977 | 3.5713 | 2.0342 | 65.5% |
| 45 | 4.2575 | 2.5191 | 1.4321 | 66.4% |
| 46 | 2.0392 | 1.5332 | 0.8885 | 56.4% |
| 47 | 0.7874 | 0.7717 | 0.6016 | 23.6% |
| Mean | 7.0868 | 4.0129 | 2.3782 | 66.4% |

The same 10,240 held-out positions were used for all three lenses. The
mean plain, v0.3, and v0.4 KL values were 6.7297, 3.5641, and 2.4393
on raw text, and 8.1578, 5.3591, and 2.1950 on chat-formatted text.
[KL and fit report](../.leaderboard/tuned-lens-v04/fit.json)

## Gate 4 v0.4

| Variant | Visits | Proxy A / B / C held-out | Practice exact | Dev s/question | Entry ZIP |
| --- | --- | ---: | ---: | ---: | ---: |
| v0.4, rank-256 and filtered | 12, 24, 34, 35, 36, 43–47 | 6/19 · 3/29 · 15/26 | 4/10 | 4.39 | 5,744 bytes |

| Gate 4 run | Exact | Wall time |
| --- | ---: | ---: |
| Practice 1 | 4/10 | 77.33 s |
| Practice 2 | 4/10 | 99.52 s |
| Practice, batch size four | 4/10 | 261.82 s |
| Dev A | 19/65 | 290.84 s |
| Dev B | 10/96 | 399.06 s |
| Dev C | 52/84 | 384.69 s |

All six runs exited 0. All 275 output lines passed the official validator,
token filter checks, and the layer and token limits. The batch-size-four run
recovered from both injected failures after waits of two and four seconds.
Scaling the observed dev wall times to 290 questions with a 30% margin
gives 27.56 minutes. The archive passed the configured credential scan and
the `hf_` and `sk-` grep. `.env` stays ignored.

The BF16 weights and MIT model card were published at revision
`6d1d9d79503e59959c7fb53e5db9bd4102029969`. The anonymous local download
matched the export digest in 6.49 seconds. NDIF anonymously fetched and
decoded all 30 tensors in 0.73 seconds.
[Public model card and weights](https://huggingface.co/achu-mohith/inkling2-mini-tuned-lens/tree/6d1d9d79503e59959c7fb53e5db9bd4102029969)

| Real judge | Starter all / held-out | v0.3 all / held-out | v0.4 all / held-out |
| --- | ---: | ---: | ---: |
| Practice | 6/10 | 6/10 | 5/10 |
| Dev A | 31/65 · 10/19 | 32/65 · 9/19 | 20/65 · 6/19 |
| Dev B | 10/96 · 3/29 | 10/96 · 3/29 | 11/96 · 4/29 |
| Dev C | 61/84 · 19/26 | 61/84 · 18/26 | 52/84 · 15/26 |
| Held-out macro | 45.35% | 42.31% | 34.35% |

The larger fit lowered held-out language-model KL at every visit. The
official judge gave v0.4 lower practice, dev A, and dev C scores than both
baselines. It gave v0.4 one additional held-out pass on dev B. The 255 paid
calls cost an estimated $0.07132 based on measured token usage. The
conservative budget charge was $0.07767 against the $1 cap.

- `.venv/bin/python notes/tuned_lens_publish.py achu-mohith/inkling2-mini-tuned-lens --version v0.4 --root .leaderboard/tuned-lens-v04 --entry .leaderboard/tuned-lens-v04/entry/submission --card .leaderboard/tuned-lens-v04/model-card.md` [Publication record](../.leaderboard/tuned-lens-v04/publication.json) · [NDIF fetch](../.leaderboard/tuned-lens-v04/ndif-fetch.json)
- `.venv/bin/python .leaderboard/tuned-lens-v04/checks.py` and `.venv/bin/python .leaderboard/tuned-lens-v04/verify.py` [Runs and readouts](../.leaderboard/tuned-lens-v04/runs/tuned) · [Gate 4 summary](../.leaderboard/tuned-lens-v04/gate4-summary.json)
- `.venv/bin/python notes/tuned_lens_sanity.py --readouts .leaderboard/tuned-lens-v04/runs/tuned --output .leaderboard/tuned-lens-v04/real-judge --version v0.4 --budget 1` [Judge summary](../.leaderboard/tuned-lens-v04/real-judge/summary.json)

## Visit-47 contrast

| Real judge | Practice | Held-out A / B / C | Held-out macro |
| --- | ---: | ---: | ---: |
| Starter, cached | 6/10 | 10/19 · 3/29 · 19/26 | 45.35% |
| Filter only, α = 0 | 6/10 | 11/19 · 3/29 · 19/26 | 47.11% |
| α = 0.25 | 6/10 | 10/19 · 4/29 · 17/26 | 43.94% |
| α = 0.5 | 6/10 | 10/19 · 4/29 · 11/26 | 36.24% |
| α = 1.0 | 5/10 | 10/19 · 5/29 · 6/26 | 30.98% |

The sweep reused one forward pass per input across strengths. It read P0
at all ten starter visits and masked special, punctuation, and whitespace
tokens after subtraction. At α = 1.0, the all-zero row at visit 47 had
an empty token list and could not vote. The four requests took 11.24,
15.77, 20.13, and 25.15 seconds for practice and sets A, B, and C,
respectively, measured after local setup.

The promotion comparison required a clear practice gain of two passes
and at least the starter's held-out macro. None of the three contrast
strengths qualified. The 336 judge calls cost an estimated $0.10155.
The conservative budget charge was $0.10996 against the $1 cap.

Deleted 29 raw activation capture files from the v0.3 and v0.4 runs.
They occupied 1,837,912,064 allocated bytes. Filesystem free space rose by
1,781,215,232 bytes during cleanup. The weights and summaries matched
their pre-cleanup checksums.

- `.venv/bin/python notes/contrastive_lens.py --output .leaderboard/contrastive --capture SET` for practice, a, b, and c. [Capture logs and readouts](../.leaderboard/contrastive)
- `.venv/bin/python notes/contrastive_lens.py --output .leaderboard/contrastive` [Judge summary](../.leaderboard/contrastive/real-judge/summary.json) · [Usage ledger](../.leaderboard/contrastive/real-judge/spend.jsonl) · [Cleanup report](../.leaderboard/contrastive/cleanup-summary.json)

## Gate 4 v0.5

| Variant | Visits | Proxy A / B / C held-out | Practice exact | Dev s/question | Entry ZIP |
| --- | --- | ---: | ---: | ---: | ---: |
| v0.5, filtered logit lens | 12, 24, 34, 35, 36, 43–47 | 9/19 · 3/29 · 19/26 | 6/10 | 4.68 | 4,678 bytes |

| Run | Exact | Proxy | Wall time |
| --- | ---: | ---: | ---: |
| Practice 1 | 6/10 | 6/10 | 95.84 s |
| Practice 2 | 6/10 | 7/10 | 101.68 s |
| Practice, batch size four | 6/10 | 6/10 | 278.92 s |
| Dev A | 32/65 | 33/65 | 301.58 s |
| Dev B | 9/96 | 9/96 | 471.46 s |
| Dev C | 62/84 | 62/84 | 372.54 s |

The entry applies the plain logit lens at P0 and filters special,
punctuation-only, and whitespace-only tokens. All runs exited 0 and all
275 output lines passed validation. The batch-size-four run recovered
from both injected failures after the two- and four-second backoffs.
The entry archive passed the configured credential and key pattern scans.
The 290-question runtime projected from dev wall times is 29.38 minutes
with the 30% margin. The first practice run's ordered readouts matched the
earlier filter-only control on all ten questions.

v0.5 leaderboard: 0.6800 (A 0.66, B 0.60, C 0.78)

The leaderboard run passed 198 of 290 questions. The overall score is
the mean of the three dataset pass rates.

- `.venv/bin/python .leaderboard/v05/checks.py` and `.venv/bin/python .leaderboard/v05/verify.py` [Gate 4 report](../.leaderboard/v05/gate4-summary.json) · [Run logs and readouts](../.leaderboard/v05/runs/filtered)
