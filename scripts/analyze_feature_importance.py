"""Reproduce the JA4Tor RF baseline and rank its training-derived MDI scores."""
import json
import hashlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score
from run_ja4tor_baseline import ROOT, DATA, OUT, FEATURES, load, matrix


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    train, test = load("train.csv"), load("test.csv")
    model = make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(
        n_estimators=200, max_features="sqrt", min_samples_leaf=2, random_state=42, n_jobs=-1))
    model.fit(matrix(train), train.traffic_type)
    predicted = model.predict(matrix(test))
    saved = pd.read_csv(OUT / "metrics.csv")
    expected = saved[(saved.dataset == "test.csv") & (saved.model == "Random Forest")].accuracy.iloc[0]
    accuracy = accuracy_score(test.traffic_type, predicted)
    assert np.isclose(accuracy, expected, atol=1e-12, rtol=0)
    forest = model.steps[-1][1]
    scores = pd.DataFrame({"feature": FEATURES, "importance": forest.feature_importances_})
    scores = scores.sort_values("importance", ascending=False).reset_index(drop=True)
    scores.insert(0, "rank", np.arange(1, len(scores) + 1))
    assert len(scores) == 30 and np.isclose(scores.importance.sum(), 1)
    scores.to_csv(OUT / "feature_importance.csv", index=False)
    top = scores.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.6, 4.7), layout="constrained")
    bars = ax.barh(top.feature, top.importance * 100, color="#24425c", height=.64)
    ax.bar_label(bars, fmt="%.2f", padding=4, fontsize=9)
    ax.set_xlim(0, top.importance.max() * 119)
    ax.set_xlabel("Mean decrease in impurity (% of total importance)")
    ax.set_axisbelow(True)
    ax.grid(axis="x", alpha=.18)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "feature_importance.png", dpi=240)
    plt.close(fig)
    (OUT / "feature_importance_manifest.json").write_text(json.dumps({
        "method": "Random Forest mean decrease in impurity (MDI)",
        "ranking_data": "train.csv only", "n_train": len(train),
        "baseline_test_accuracy_verified": accuracy, "seed": 42,
        "training_sha256": hashlib.sha256((DATA / "train.csv").read_bytes()).hexdigest(),
        "limitations": "MDI can favor continuous/high-cardinality variables; correlated features share credit. No causal or cross-domain interpretation."
    }, indent=2), encoding="utf-8")
    methodology()
    print(scores.head(10).to_string(index=False))
    print("Reproduced RF test accuracy:", accuracy)


def methodology():
    folder = ROOT / "results/figures"
    folder.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 3.4))
    ax.set_xlim(0, 11); ax.set_ylim(0, 3.4); ax.axis("off")
    texts = ["PCAP / CSV\nData Input", "Feature Extraction\nJA4Tor: 30 features\nMineShark: 20 features", "Data Split\nPublished / capture-\ndisjoint partitions", "Classifiers\nRF / SVM / KNN", "Classification Results\nAccuracy / Recall / F1\nConfusion matrices"]
    xs = [0.1, 2.32, 4.54, 6.76, 8.98]
    for x, label in zip(xs, texts):
        box = FancyBboxPatch((x, 1.05), 1.92, 1.22, boxstyle="round,pad=0.05,rounding_size=.08", facecolor="#edf3f7", edgecolor="#24425c", linewidth=1.2)
        ax.add_patch(box)
        ax.text(x+.96, 1.66, label, ha="center", va="center", fontsize=9)
    for x in xs[:-1]:
        ax.annotate("", (x+2.17, 1.66), (x+1.99, 1.66), arrowprops={"arrowstyle": "->", "color": "#24425c", "lw": 1.5})
    ax.text(5.5, .5, "Split capture groups before sampling windows; fit imputation/scaling on training data only.", ha="center", fontsize=10, color="#24425c")
    fig.savefig(folder / "methodology.png", dpi=240, bbox_inches="tight")
    fig.savefig(folder / "methodology.svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
