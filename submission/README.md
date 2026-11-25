# Filtered logit lens at the starter visits

The lens reads Inkling 2 Mini at the supplied `read_position` during visits
12, 24, 34, 35, 36, and 43 through 47. The lens applies the model's final
normalization and language-model head to the state entering each visit.

The lens masks special tokens and tokens made entirely of punctuation or
whitespace and reports the ten highest-scoring remaining tokens per visit.
Each NDIF request has up to three attempts, with waits of two and four seconds
after failures.

This entry is released under the MIT License.
