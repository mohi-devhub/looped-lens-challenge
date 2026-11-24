# Logit lens with cross-visit deduplication

This entry reads Inkling 2 Mini at the supplied `read_position` during visits
1, 13, 14, 16, 25, 26, and 44. At each visit it applies the model's final
normalization and language-model head to the state entering the layer.

The lens masks special tokens and tokens made entirely of punctuation or
whitespace. Each readout omits tokens already reported at an earlier visit,
ignoring case and surrounding whitespace. The lens refills each readout from
up to 128 filtered candidates at that visit. Each NDIF request has up to three
attempts, with waits of two and four seconds after failures.

This entry is released under the MIT License.
