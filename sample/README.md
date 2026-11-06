# Calibrated example

[中文](README.zh.md)

These examples cover both independent editions: the browser workstation and the
Revit plug-in. In the browser, click **Import sample** for `plan.json`, or
**Open JSON** to inspect either saved JSON. Importing a sample needs no model
inference. Newly generated CLI JSON can be opened in the same workstation; see
the [inference guide](../docs/inference.md). The Revit plug-in creates native
elements through its own generation command; it does not currently offer a
separate edited-JSON import command.

The two images and `plan.json` describe the same editable apartment. The layout
retains seed `3968430468` and now uses the current **large** physical calibration:
**0.05466578730522668 metres per canvas unit**. Total net floor area, including
balconies and excluding joined wall footprints, is **128.9 m²**.

Prompt: `A large 3-bedroom apartment with 2 bathrooms and 2 balconies.`

| Space | Net area |
|---|---:|
| Living room | 49.1 m² |
| Kitchen | 10.8 m² |
| Bedroom 1 | 16.0 m² |
| Bedroom 2 | 21.2 m² |
| Bedroom 3 | 14.3 m² |
| Bathroom 1 | 3.9 m² |
| Bathroom 2 | 2.7 m² |
| Balcony 1 | 3.0 m² |
| Balcony 2 | 7.7 m² |

The total uses full precision rather than adding rounded labels. There are
28 wall segments, nine doors, four windows and five balcony railing segments.
Exterior walls are 400 mm thick, partitions 200 mm, and walls 3.3 m high.
Meeting wall faces include complete corner joins; editable centerlines stay
independent. Opening widths follow the calibrated horizontal scale; wall
thicknesses, wall heights and opening heights/sills retain their metre values.

- `floorplan.png`: newly rendered 2D plan with current room and total areas.
- `model3d.png`: 2048 × 1536 PNG exported by the browser's WebGL renderer from
  the same sample document, including real opening voids and open railings.
- `model-metadata.json`: current calibration, areas, counts and verification scope.

These updated illustrations come from the local editor geometry. They are not
new native Revit exports; the retained native sample is available below. Native Revit measurements for this recalibrated layout have not
been rerun. The JSON retains the Revit input schema.

All windows avoid the continuous entrance facade. The bedroom connected to a
balcony has no additional window. Room areas, floor meshes, JSON reimport and
opening-placement rules are checked against the current sample.

## Native Revit example

`revit-floorplan.png` and `revit-model3d.png` are the original native Revit 2022
exports from the earlier 106.2 m² sample. `revit-plan.json` retains their input,
and `revit-metadata.json` records the native measured areas and element counts.
They are preserved alongside the browser illustrations so both workflows can
be inspected. The current 128.9 m² browser sample uses a later scale calibration.
