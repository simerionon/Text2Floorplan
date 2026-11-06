# Model checkpoints

[中文](README.zh.md)

Model weights are not committed to the source repository. Both complete Windows
editions include the inference weights: the browser workstation carries them in
its Web Data ZIPs, and the Revit installer automatically downloads its own
environment parts. Users download only their chosen edition; neither edition
requires the other. Both use the same vector Flow Matching model, not raster DDPM.

## Standalone inference download

Download **[flow_matching_best.pth](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/flow_matching_best.pth)**
(193,053,154 bytes) into this directory for source inference. Verify it against
[SHA256-model.txt](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/SHA256-model.txt):

`11fe79209c433ec189b1d19b8626c20ff7319b71aac79915b54e570e89a3c6cb`

This is the same compact PTH supplied inside the Windows distributions. CLIP is
downloaded separately with `python scripts/setup_models.py`. The full training
checkpoint is not uploaded. Its provenance and this inference export are recorded
separately in [`manifest.json`](manifest.json).

For source inference or release builds, supply a compatible trained checkpoint
at `checkpoints/flow_matching_best.pth`, or pass its path with `--checkpoint`.
Local weight files are ignored by Git. Both full and inference-only checkpoints
can be passed to `python infer.py --checkpoint ... --prompt "..."` or the browser
server. Source inference needs the CLIP encoder too; see the
[inference guide](../docs/inference.md). Training from scratch does not require
the author's checkpoint.

The reference full training checkpoint is 770,009,261 bytes; its metadata is
retained in `manifest.json` for provenance.

SHA-256:
`a2e67e9c96069847d1a0c64b61fb65536faa54c0245e56364e4aea5d98b57bdd`

## Why the release PTH is smaller

| Contents | Original training PTH | Release inference PTH |
| --- | --- | --- |
| Production `model` tensors | 192,917,136 bytes | Identical tensors |
| EMA model copy | 192,917,136 bytes | Omitted |
| Optimizer tensors | 383,595,056 bytes | Omitted |
| Scheduler and training state | Included | Omitted |
| Required architecture arguments | Included | Included |
| Serialized file size | **770,009,261 bytes** | **193,053,154 bytes** |

Sizes use decimal MB: about 770 MB versus 193 MB. Serialization adds a small
overhead to the tensor sizes above. All 345 exported model tensors and their
dtypes were compared with the original and match exactly. There is no
quantization, pruning or reduction of the network. The production loader uses
`model`; exporting it does not switch to or from EMA inference. The compact PTH
is suitable for inference but not an exact training resume.

Source-code licensing does not by itself establish permission to redistribute
or commercially use weights trained on separately obtained datasets. Check the
applicable training-data agreements and [third-party notices](../THIRD_PARTY_NOTICES.md)
before assigning a weight license.
