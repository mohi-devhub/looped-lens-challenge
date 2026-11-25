# Looped Lens experiments through v0.5

| Entry | Leaderboard pass rate | Change and takeaway |
| --- | ---: | --- |
| Starter | 0.6619 | The plain logit lens at 12, 24, 34, 35, 36, and 43–47 set the ten-visit reference. |
| v0.1 | 0.6411 | Kept visits 43–47 and added filtering and retries. The loss showed that practice had overstated the value of the late visits. |
| v0.2a | 0.6096 | Used only visit 44, the strongest single visit on dev. It scored lowest on the leaderboard. |
| v0.5 | 0.6800 | Used the plain logit lens at all ten starter visits with filtering and retries. It beat the starter by 1.81 percentage points. |

v0.5 passed 198 of 290 questions. Its dataset pass rates were 0.66 on A,
0.60 on B, and 0.78 on C. The leaderboard averages the three rates.
[Run details and commands](results.md)

| Other variants | Method | Real-judge practice | Real-judge held-out dev macro |
| --- | --- | ---: | ---: |
| v0.2b | Filtered logit lens with cross-visit deduplication at 1, 13, 14, 16, 25, 26, and 44 | 5/10 | 51.58% |
| v0.3 | Starter visits with rank-16 BF16 translators fitted on 256 positions and checked on 96 held-out positions | 6/10 | 42.31% |
| v0.4 | Starter visits with rank-256 BF16 translators fitted on 40,960 positions and evaluated on 10,240 held-out positions | 5/10 | 34.35% |

## Dev sets and the leaderboard

The same-sweep proxy tied the starter and v0.1 while the leaderboard
separated them by 2.08 percentage points. The real judge recovered that
pairwise order locally. It still put v0.2a first among those three entries,
while v0.2a was last on the leaderboard. Dev B drove much of the reversal.
On that set, the judge passed 13/29 for visit 44 alone and 3/29 for the
starter. The audit found mid-visit translations and inflections that the
proxy missed. Those extra citations changed some votes in both directions
and left the starter's dev verdicts unchanged. The authored B prompts
remain a poor basis for choosing visits for hidden B.
[Calibration and citation audit](results.md#real-judge-calibration)

## What the tuned-lens objective learned

On the same 10,240 held-out WikiText-2 positions, mean full-vocabulary KL
fell from 7.087 for the plain lens to 4.013 for v0.3 and 2.378 for v0.4.
v0.4 improved at all ten visits. Its exact practice score was 4/10 and
its real-judge scores dropped on dev A and C.

The teacher distribution rewards prediction of what the model emits next.
At a chat boundary that can be `<|content_thinking|>`. Later it can be the
final answer. A latent intermediate can help the model reach that answer
and have little probability in the teacher distribution. A translator can
fit the KL objective well while making the intermediate harder to read.
[Held-out KL and evaluation](results.md#v04-scaled-tuned-lens)

## Contrast against visit 47

| Real judge | Practice | Dev A | Dev B | Dev C | Held-out dev macro |
| --- | ---: | ---: | ---: | ---: | ---: |
| Starter | 6/10 | 10/19 | 3/29 | 19/26 | 45.35% |
| Filter only | 6/10 | 11/19 | 3/29 | 19/26 | 47.11% |
| α = 0.25 | 6/10 | 10/19 | 4/29 | 17/26 | 43.94% |
| α = 0.5 | 6/10 | 10/19 | 4/29 | 11/26 | 36.24% |
| α = 1.0 | 5/10 | 10/19 | 5/29 | 6/26 | 30.98% |

Each strength subtracts scaled visit-47 logits from the ten starter visits.
At α = 1.0, visit 47 cancels itself and abstains. The mild strengths tied
the starter on practice and lost on held-out macro. As subtraction increased,
dev B gained up to two passes and dev C lost up to thirteen. No strength
qualified for v0.5. Judge spend was an estimated $0.10155 with a $1 cap.
[Judge results](../.leaderboard/contrastive/real-judge/summary.json)

The user selected the filter-only lens for v0.5. It passed Gate 4 with
6/10 exact on all three practice runs. [v0.5 checks](results.md#gate-4-v05)

Cleanup removed 29 raw activation capture files totaling 1.84 GB. Free
space rose by 1.78 GB during the deletion. Both fitted weight files, the
base norm and output head, and the summaries were verified by checksum.
[Cleanup record](../.leaderboard/contrastive/cleanup-summary.json)

## What a supervised lens would need

- Build independent, labeled prompt families for latent two-hop and
  multi-step computation tasks. Record the intended intermediate, the
  final answer, valid single-token forms, and plausible distractors. Use
  a model forward pass to verify that the prompt elicits the intended
  final answer.
- Capture Inkling's activations at the supplied read position. Fit a
  vocabulary readout with a supervised objective that ranks valid
  intermediate tokens above distractor tokens, including the final answer
  when it differs from the intermediate. The entry can use the resulting
  weights and activations to score vocabulary tokens.
- Hold out whole prompt templates and groups of related entities. Test
  answer-imminent and latent questions in raw and chat formats. Report
  the correct-token rank, wrong votes, and strict plurality passes by task
  family using the real judge. Keep the starter as the comparison point.

## Next ideas

1. **Supervised intermediate-token lens.** Train on broad synthetic data
   with intermediate-token labels and plausible distractors. Keep the
   training examples and templates separate from the dev sets.
2. **Contrast between loop runs.** Adapt LoopCD to compare earlier and
   later runs of the same layer at P0. Layer 12 provides visits 12, 24,
   and 36 as an initial set of pairs. Measure the change in intermediate
   rank and judged votes. [LoopCD paper](https://arxiv.org/abs/2610.02185)
3. **Judge-calibrated dev set.** Use only public guidance from
   `final-evals/` to author prompts, intermediates, and distractors. Check
   candidate tokens with the official judge and test whether the dev set
   reproduces the recorded ordering of the known entries.
   [Public evaluation guide](../final-evals/README.md) · [Judge prompts](../final-evals/judge_prompts/README.md)
