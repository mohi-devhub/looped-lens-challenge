# Tuned lens at the starter visits

The lens reads Inkling 2 Mini at the supplied `read_position` during visits
12, 24, 34, 35, 36, and 43 through 47. Each visit has a rank-16 affine
translator that adds a learned correction to the state entering the layer.
The lens then applies the model's final normalization and language-model
head.

The translators minimize next-token KL divergence to the model's final
output on public WikiText-2 text. The entry downloads the bfloat16 weights
once per NDIF request from the Hugging Face revision in `tuned-weights.json`.
[Training corpus](https://huggingface.co/datasets/Salesforce/wikitext)

The lens masks special tokens and tokens made entirely of punctuation or
whitespace and reports the ten highest-scoring remaining tokens per visit.
Each NDIF request has up to three attempts, with waits of two and four seconds
after failures.

This entry is released under the MIT License.
