# Local inference models

[中文](README.zh.md)

The browser workstation, direct CLI and Revit plug-in use the same vector Flow
Matching checkpoint and CLIP text encoder. No LLM, external inference API or API
key is used. The complete Windows editions each supply both models; their
runtime/model copies are independent.

For source use, run `python scripts/setup_models.py` from the repository root.
It downloads `openai/clip-vit-large-patch14` into `models/clip/`. This needs internet
once; inference then reads the local encoder offline. Downloads are ignored by Git.

Place source Flow weights at `checkpoints/flow_matching_best.pth`, or pass
`--checkpoint`. Complete Windows applications store their compact checkpoint
beside `clip/` in their private `models/` folder. Either model location can be
passed explicitly to the [CLI](../docs/inference.md) or
[browser server](../web_editor/README.md).

`models/` contains model files; the separate `data/clip/` cache used during training
contains precomputed embeddings and is not a substitute for the text encoder.
No model downloads or generated embeddings are committed to the source repository.
See [checkpoint details](../checkpoints/README.md) and
[third-party notices](../THIRD_PARTY_NOTICES.md).
