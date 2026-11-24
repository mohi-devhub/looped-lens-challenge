# Late-visit logit lens

This entry reads Inkling 2 Mini at the supplied `read_position` during visits
43 through 47. At each visit it applies the model's final normalization and
language-model head to the state entering the layer.

The lens masks special tokens and tokens made entirely of punctuation or
whitespace. It reports the ten highest-scoring remaining vocabulary tokens
per visit. Each NDIF request has up to three attempts, with waits of two and
four seconds after failures.

This entry is released under the MIT License.
