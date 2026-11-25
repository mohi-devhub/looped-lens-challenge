"""A token lens, written as functions that run inside an NDIF trace.

A lens here takes ``h``, the state entering one layer visit at the read position (a tensor of
shape [hidden]), and returns scores over the vocabulary ([vocabulary]). Everything in these
functions executes on NDIF; only the top ten token ids per visit are sent back.
"""


def layers(model):
    """The decoder layers: 24 of them, of which 6 to 17 run three times per forward pass."""
    return model.model.language_model.layers


def visit_address(config, visit: int) -> tuple[int, int]:
    """Where a layer visit happens: which layer, and which of that layer's runs (0, 1 or 2).

    One token passes through 48 visits, numbered 0 to 47 in the order they run: layers 0-5 once,
    then layers 6-17 three times over, then layers 18-23 once. ``config`` is the model's text
    configuration, which holds those numbers.
    """
    start, end, passes = config.loop_layer_index_start, config.loop_layer_index_end, config.loop_num_passes
    looped = end - start
    if not 0 <= visit < config.num_hidden_layers + looped * (passes - 1):
        raise ValueError(f"there is no layer visit {visit}")
    if visit < start:
        return visit, 0
    if visit < start + looped * passes:
        return start + (visit - start) % looped, (visit - start) // looped
    return visit - looped * (passes - 1), 0


def logit_lens(model, h):
    """The model's own final norm and unembedding, applied early. No trained weights.

    The model also soft-caps its logits, which does not change their order, so it is left out.
    """
    return model.lm_head(model.model.language_model.norm(h))
