# Run text-to-floorplan inference

[中文](inference.zh.md)

The source repository includes the complete production inference path. It does
not require Revit, a browser, an LLM, API keys, or a running cloud service.
CLIP encodes a supported English prompt; the vector Flow Matching model samples
room geometry, followed by geometry repair, door/window placement and area checks.
The current public model is Flow Matching, not the separate raster FM/DDPM experiment.

## Prepare once

Use a Python environment; Windows x64, Python 3.14 and PyTorch 2.11 were tested.
Run these commands from the source repository root:

```powershell
python -m pip install -r requirements.txt
python scripts/setup_models.py
```

The second command downloads `openai/clip-vit-large-patch14` to `models/clip/`.
Download the standalone **[193 MB PTH](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/flow_matching_best.pth)**
from the release; its checksum is in
[SHA256-model.txt](https://github.com/Simon777hh/Text2Floorplan/releases/download/v1.1.0/SHA256-model.txt).
Place your compatible weights at `checkpoints/flow_matching_best.pth`, or supply
`--checkpoint`. Both the original full training PTH and the inference-only PTH
work. For an already prepared Windows application, its `models/` contains the
Flow checkpoint and `clip/`; those paths can be supplied directly. Weights are
not committed to Git. See [checkpoint details](../checkpoints/README.md).

Dependency/model downloads need internet access once. Generation is then local
and offline. If you only want to use the application without setting up Python,
choose a complete [Windows edition](../README.md#choose-your-edition).

The refreshed portable browser package also includes this CLI. Prepare the
package by starting its normal launcher once, then run the following from its
extracted `Text2Floorplan` directory to use the bundled Python and models:

```powershell
.\runtime\python.exe -B infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
```

The local server does not need to remain open for CLI generation.

## Generate a PNG and editable JSON

```powershell
python infer.py --prompt "A 3-bedroom apartment with 2 bathrooms and 1 balcony."
```

Optional explicit model paths and CPU execution:

```powershell
python infer.py --prompt "A small 2-bedroom apartment with 1 bathroom and 1 balcony." --checkpoint "C:/Models/flow_matching_best.pth" --clip-dir "C:/Models/clip" --device cpu --seed 42 --output-dir outputs/my_plans
```

`--device auto` is the default: use a compatible NVIDIA GPU with CPU fallback.
`--device cpu` forces CPU. `--language zh` changes progress messages only; prompts
remain English. Omit `small`/`large` for medium. Change only the supported size,
bedroom, bathroom and balcony counts. Each plan includes a living room and kitchen.

Results have unique timestamped names under `outputs/inference/` by default:

- `floorplan_YYYYMMDD_HHMMSS_microseconds.png`: 2D preview with room and total areas.
- Matching `.json`: rooms, walls, hosted openings, balcony railings, physical scale,
  prompt, final seed and clear areas. Open it with **Open JSON** in the browser
  workstation for linked 2D/3D editing.

The CLI reuses the same backend as the browser workstation and Revit plug-in,
including generation retries for invalid layouts and minimum kitchen/bathroom
area checks. `--seed` supplies the first attempt's seed; rejected layouts retry
with new seeds. The final seed is recorded in JSON. Inference uses 200 solver
steps. No training GT, precomputed masks, dataset files or training process is
needed. The small committed `data/` priors and settings are required.

This command creates geometry and a preview; it does not produce an RVT file.
Native Revit construction requires the separate add-in. There is currently no
Revit ribbon command to import an arbitrary edited JSON file.

## Code map

| File | Responsibility |
| --- | --- |
| `infer.py` | Public command-line entry; model paths, device and output selection |
| `backend_cli.py` | Shared production backend; checks, retries, preview and structured JSON |
| `pipeline_generate.py` | Prompt/topology sampling, CLIP, model loading, geometry recovery and openings |
| `inference_runtime.py`, `flow_solver.py` | Inference-only model execution and Heun integration |
| `model.py` | Vector Flow Matching Transformer architecture |
| `geometry_cleanup.py`, `plan_postprocess.py` | Geometry repair |
| `door_window_rules.py`, `revit_geometry.py`, `plan_quality.py` | Openings, physical dimensions and clear-area checks |

The older direct `pipeline_generate.py` command remains available, including
`--steps`, `--seed`, `--checkpoint`, `--clip-dir` and `--output-dir`. It writes
intermediate pipeline metadata; use `infer.py` for the editable application JSON.
For programmatic integration, `backend_cli.py --request request.json --response
plan.json` accepts `{"prompt": "A 3-bedroom apartment with 2 bathrooms and 1 balcony.",
"seed": 42, "language": "en"}`. The request seed is optional.

## Full versus inference-only checkpoint

The original PTH is **770,009,261 bytes**; its release export is
**193,053,154 bytes**. The original contains model parameters, another complete
EMA model, optimizer moments, scheduler state and training metadata. The export
retains `model` and the architecture arguments needed for inference.

All **345 tensors**, including their dtypes, were compared against the original
checkpoint's `model` and match exactly. This is training-state removal, not
quantization, pruning or a smaller network. The production loader already uses
`model`, not `ema_model`; the export does not change that selection. The compact
PTH supports inference but is not sufficient for an exact training resume.

Training-data and third-party permissions remain separate from source-code
licensing. See [third-party notices](../THIRD_PARTY_NOTICES.md).
