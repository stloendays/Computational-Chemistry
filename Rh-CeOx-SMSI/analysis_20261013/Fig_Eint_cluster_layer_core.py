"""E_int of Ce2Oy clusters (Stage 5) and Ce4O2y layers/2 (Stage 4) on Rh(111), per Ce2Oy unit -> figures/Fig_Eint.png."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CC = os.path.dirname(os.path.dirname(HERE))
R5 = json.load(open(os.path.join(CC, "DynSMSI_stage5_cluster_layer_Eint_20260930", "results", "stage5_Eint.json"),
                    encoding="utf-8"))["comparison"]

lab = ["Ce$_2$O$_3$", "Ce$_2$O$_4$"]
clu = [R5["Ce2O3"]["cluster_E_int"], R5["Ce2O4"]["cluster_E_int"]]
lay = [R5["Ce2O3"]["layer_E_int_per_unit"], R5["Ce2O4"]["layer_E_int_per_unit"]]

plt.rcParams.update({"font.family": "Arial", "font.size": 18, "axes.linewidth": 1.2,
                     "xtick.direction": "in", "ytick.direction": "in"})
fig, ax = plt.subplots(figsize=(7.2, 5.4))
x = np.arange(2)
w = 0.34
for dx, v, col, name in ((-w / 2, clu, "#b5334a", "Cluster/Rh(111)"), (w / 2, lay, "#264b96", "Layer/Rh(111)")):
    bars = ax.bar(x + dx, v, w, color=col, label=name)
    for bx, vv in zip(bars, v):
        ax.text(bx.get_x() + bx.get_width() / 2, vv - 0.12, ("%.2f" % vv).replace("-", "−"),
                ha="center", va="top", fontsize=16)
ax.axhline(0, color="k", lw=1.0)
ax.set_xticks(x, lab)
ax.set_ylim(-6.0, 0)
ax.set_ylabel(r"$E_\mathrm{int}$ per Ce$_2$O$_y$ unit (eV)")
ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=16)
ax.set_xlim(-0.55, 1.55)
fig.tight_layout()
os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
fig.savefig(os.path.join(HERE, "figures", "Fig_Eint.png"), dpi=220)
print(clu, lay)
