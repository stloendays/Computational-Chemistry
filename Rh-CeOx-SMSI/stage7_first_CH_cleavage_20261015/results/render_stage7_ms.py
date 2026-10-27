#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MS-style renders (black background, CPK, ball-and-stick, real cell frame) of the stage-7 systems.

Reuses the stage-3 renderer: front view along a1, top view down the normal, outermost atoms on the cell lines,
frame = real calculation cell. Structure: results/raw/<name>/CONTCAR of systems with a final single point
(E_final_sp.txt). Systems still running are not rendered (placeholders in the deck).
Run with D:/Tools/render-venv/Scripts/python.exe
"""
import json
import os
import shutil
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
S7 = os.path.dirname(HERE)
S3FIG = os.path.join(os.path.dirname(S7), "DynSMSI_stage3_units_CH4_20260924", "figures")
sys.path.insert(0, S3FIG)
import render_stage3_ms as r3                                      # noqa: E402

OUT = os.path.join(HERE, "figures_ms_bonds")


def main():
    done = [l.split()[0] for l in open(os.path.join(HERE, "E_final_sp.txt"), encoding="utf-8") if len(l.split()) >= 2]
    tmpin = os.path.join(OUT, "_in")
    os.makedirs(tmpin, exist_ok=True)
    for n in done:
        os.makedirs(os.path.join(tmpin, n), exist_ok=True)
        shutil.copy(os.path.join(HERE, "raw", n, "CONTCAR"), os.path.join(tmpin, n, "POSCAR"))
    r3.INPUTS = tmpin
    man = {}
    z = np.array([0.0, 0.0, 1.0])
    for n in done:
        cell, sym, pos, tmp, info = r3.prepare(n, "slab", OUT)
        pl = r3.build(tmp, sym, "slab")
        pl.add_to_scene()
        try:
            v = {}
            pts = np.vstack([pos, r3.cell_corners(cell)])
            for tag, d, up in [("front", r3.side_direction(cell), z),
                               ("top", np.array([0.0, 0.0, -1.0]), np.array([0.0, 1.0, 0.0]))]:
                fn = os.path.join(OUT, "%s_%s.png" % (n, tag))
                v[tag] = {"file": os.path.basename(fn), "size": r3.shoot(pl, pts, d, up, fn, 60.0)}
        finally:
            pl.remove_from_scene()
        man[n] = {"kind": "slab", "structure": "relaxed", "views": v, **info}
        print(n, {k: x["size"] for k, x in v.items()}, info.get("z_min_A"), info.get("vacuum_above_top_atom_A"))
    json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
