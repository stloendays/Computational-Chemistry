#!/usr/bin/env python3
"""Render a reproducible POSCAR morphology comparison with OVITO.

This figure is intentionally a geometry/morphology visualization, not an
energetics plot.  It compares representative layer POSCARs (3x3 Rh(111))
with the current cluster POSCARs (4x4 Rh(111)) for the two matched
stoichiometries requested in the 2026-09-30 supervisor task.

Output:
  results/ovito/Fig_POSCAR_layer_vs_cluster_topview.png
  results/ovito/panels/*.png
"""

from __future__ import annotations

from pathlib import Path
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ovito.io import import_file
from ovito.modifiers import PythonScriptModifier
from ovito.vis import TachyonRenderer, Viewport


ROOT = Path(__file__).resolve().parents[3]
STAGE2 = ROOT / "stage2_interfaces_20260910"
STAGE5 = STAGE2 / "cluster_layer_Eint_20260930"
OUTDIR = STAGE5 / "results" / "ovito"
PANELDIR = OUTDIR / "panels"

CASES = [
    {
        "key": "ce2o3_layer",
        "title": "Ce2O3 basis — LAYER",
        "subtitle": "Ce4O6/Rh(111) 3x3, A-type layer",
        "path": STAGE2 / "inputs" / "30d_Ce4O6_layer_Atype" / "POSCAR",
    },
    {
        "key": "ce2o3_cluster",
        "title": "Ce2O3 — CLUSTER",
        "subtitle": "Ce2O3/Rh(111) 4x4, C3b start",
        "path": STAGE5 / "inputs" / "C3b_Ce2O3_Rh_from12a" / "POSCAR",
    },
    {
        "key": "ce2o4_layer",
        "title": "Ce2O4 basis — LAYER",
        "subtitle": "Ce4O8/Rh(111) 3x3, FCC registry",
        "path": STAGE2 / "inputs" / "20a_Ce4O8_layer_regFCC" / "POSCAR",
    },
    {
        "key": "ce2o4_cluster",
        "title": "Ce2O4 — CLUSTER",
        "subtitle": "Ce2O4/Rh(111) 4x4, C4a start",
        "path": STAGE5 / "inputs" / "C4a_Ce2O4_Rh_from10c" / "POSCAR",
    },
]

# Element styling: substrate deliberately small so the Ce/O footprint is obvious.
STYLE = {
    "Rh": ((0.72, 0.74, 0.77), 0.42),
    "Ce": ((0.93, 0.69, 0.16), 1.05),
    "O":  ((0.86, 0.16, 0.13), 0.72),
}
DEFAULT_STYLE = ((0.45, 0.45, 0.45), 0.55)

PANEL_SIZE = (760, 760)
WHITE = (255, 255, 255)
TEXT = (28, 28, 28)
MUTED = (95, 95, 95)
BORDER = (205, 205, 205)


def _style_particles(frame, data):
    """Assign per-particle colors and radii using the VASP element labels."""
    if data.particles is None:
        return

    ptype_values = np.asarray(data.particles["Particle Type"], dtype=int)
    type_def = data.particles.particle_types
    id_to_name = {int(t.id): str(t.name).strip() for t in type_def.types}

    colors = np.zeros((len(ptype_values), 3), dtype=float)
    radii = np.zeros(len(ptype_values), dtype=float)

    for i, tid in enumerate(ptype_values):
        name = id_to_name.get(int(tid), "")
        color, radius = STYLE.get(name, DEFAULT_STYLE)
        colors[i, :] = color
        radii[i] = radius

    data.particles_.create_property("Color", data=colors)
    data.particles_.create_property("Radius", data=radii)

    if data.cell is not None:
        data.cell.vis.enabled = False


def render_top_view(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing POSCAR: {source}")

    pipeline = import_file(str(source))
    pipeline.modifiers.append(PythonScriptModifier(function=_style_particles))
    pipeline.add_to_scene()

    viewport = Viewport(type=Viewport.Type.Top)
    viewport.zoom_all(size=PANEL_SIZE)
    viewport.render_image(
        filename=str(target),
        size=PANEL_SIZE,
        background=(1.0, 1.0, 1.0),
        alpha=False,
        renderer=TachyonRenderer(),
    )

    pipeline.remove_from_scene()


def load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def add_text_centered(draw, xy_center, text, font, fill=TEXT):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]
    draw.text((xy_center[0] - width / 2, xy_center[1]), text, font=font, fill=fill)


def make_montage(panel_files: list[Path], output: Path) -> None:
    cell_w = 840
    cell_h = 900
    margin = 70
    header_h = 115
    footer_h = 145
    canvas_w = margin * 2 + cell_w * 2
    canvas_h = header_h + cell_h * 2 + footer_h + 30

    canvas = Image.new("RGB", (canvas_w, canvas_h), WHITE)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(34, bold=True)
    subtitle_font = load_font(21, bold=False)
    big_font = load_font(42, bold=True)
    small_font = load_font(22, bold=False)
    legend_font = load_font(23, bold=True)

    add_text_centered(
        draw,
        (canvas_w / 2, 24),
        "Rh(111) supported CeOx: layer vs cluster (POSCAR top view)",
        big_font,
    )
    add_text_centered(
        draw,
        (canvas_w / 2, 77),
        "OVITO Python rendering • same element styling • each panel fitted to its own cell",
        small_font,
        fill=MUTED,
    )

    for idx, (case, panel_path) in enumerate(zip(CASES, panel_files)):
        row, col = divmod(idx, 2)
        x0 = margin + col * cell_w
        y0 = header_h + row * cell_h

        # panel frame
        draw.rounded_rectangle(
            (x0 + 10, y0 + 5, x0 + cell_w - 10, y0 + cell_h - 5),
            radius=16,
            outline=BORDER,
            width=2,
            fill=WHITE,
        )

        add_text_centered(
            draw,
            (x0 + cell_w / 2, y0 + 22),
            case["title"],
            title_font,
        )
        add_text_centered(
            draw,
            (x0 + cell_w / 2, y0 + 68),
            case["subtitle"],
            subtitle_font,
            fill=MUTED,
        )

        panel = Image.open(panel_path).convert("RGB")
        panel.thumbnail((740, 740), Image.Resampling.LANCZOS)
        px = int(x0 + (cell_w - panel.width) / 2)
        py = int(y0 + 110)
        canvas.paste(panel, (px, py))

    # Footer / legend.
    footer_y = header_h + cell_h * 2 + 16
    legend_items = [
        ("Rh", (184, 189, 196)),
        ("Ce", (237, 176, 41)),
        ("O",  (219, 41, 33)),
    ]
    lx = margin + 20
    for label, color in legend_items:
        draw.ellipse((lx, footer_y + 12, lx + 26, footer_y + 38), fill=color, outline=(80, 80, 80))
        draw.text((lx + 38, footer_y + 8), label, font=legend_font, fill=TEXT)
        lx += 120

    note1 = "Layer panels contain two Ce2Oy units (Ce4O6 / Ce4O8); cluster panels contain one Ce2Oy unit."
    note2 = "3x3 and 4x4 Rh cells differ in physical size: compare Ce/O spatial distribution and morphology, not panel scale."
    draw.text((margin + 20, footer_y + 58), note1, font=small_font, fill=TEXT)
    draw.text((margin + 20, footer_y + 91), note2, font=small_font, fill=MUTED)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=95)


def main() -> None:
    PANELDIR.mkdir(parents=True, exist_ok=True)

    panel_files = []
    for case in CASES:
        out = PANELDIR / f"{case['key']}.png"
        print(f"[OVITO] {case['path']} -> {out}")
        render_top_view(case["path"], out)
        panel_files.append(out)

    final = OUTDIR / "Fig_POSCAR_layer_vs_cluster_topview.png"
    make_montage(panel_files, final)
    print(f"[DONE] {final}")


if __name__ == "__main__":
    main()
