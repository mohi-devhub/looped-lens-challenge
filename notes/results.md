# Lens results

| Variant | Visits | Proxy (a/b/c held-out) | Practice exact | s/question | Size |
| --- | --- | --- | --- | --- | --- |
| Starter logit lens | 12, 24, 34, 35, 36, 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 4.16 (wall time) | 9,404 bytes of source |
| Starter logit lens (session rerun) | 12, 24, 34, 35, 36, 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 4.58 (wall time) | 9,404 bytes of source |
| Starter with token filtering | 12, 24, 34, 35, 36, 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 2.79 (wall time) | 10,205 bytes of source |
| Calibration v0.1 | 43, 44, 45, 46, 47 | — | 0.6000 (6/10) | 4.61 (wall time) | 5,232-byte ZIP |

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

Start Gate 1 after the user confirms they submitted v0.1. Give extra weight to
arithmetic partial results, day and month offsets, unit conversion, and latent
two-hop questions.
