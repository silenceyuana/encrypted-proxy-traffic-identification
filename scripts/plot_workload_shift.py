"""Visualize the measured MineShark in-domain and workload-shift results."""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/mineshark"
inside = pd.read_csv(OUT / "metrics.csv").set_index("model")
shift = pd.read_csv(OUT / "workload_shift_metrics.csv").set_index("model")
models = list(inside.index)
x = np.arange(len(models))
fig, ax = plt.subplots(figsize=(7.5, 4.0), layout="constrained")
ax.bar(x - .19, inside.loc[models, "accuracy"] * 100, .38, color="#1f5a85", label="Capture-disjoint test")
ax.bar(x + .19, shift.loc[models, "accuracy"] * 100, .38, color="#b56d2c", label="NBMiner to XMRig")
ax.set_xticks(x, models)
ax.set_ylabel("Accuracy / macro recall (%)")
ax.set_ylim(0, 100)
ax.grid(axis="y", alpha=.2)
ax.set_axisbelow(True)
ax.legend(frameon=False)
fig.savefig(OUT / "workload_shift_comparison.png", dpi=220)
plt.close(fig)
