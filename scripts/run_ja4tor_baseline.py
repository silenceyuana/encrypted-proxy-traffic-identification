"""Run an auditable statistical-feature baseline on the public JA4Tor CSVs.

These tables contain real flow measurements but no public capture/run identifiers.
The five labels are NonTor, Tor, Tor-over-Shadowsocks, Tor-over-Trojan,
Tor-over-VMess. They are not the requested VLESS/HTTPS four-class benchmark.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/ja4tor"
OUT = ROOT / "results/ja4tor"
LABELS = {0: "NonTor", 1: "Tor", 2: "Tor-SS", 3: "Tor-Trojan", 4: "Tor-VMess"}

# Flow-level observables only: packet counts, lengths, timing and direction ratio.
# No IPs, ports, domains, TCP flags, TLS or HTTP parser fields, timestamps or flow IDs.
FEATURES = [
    "Total Fwd Packets", "Total Bwd Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean", "Fwd Packet Length Std",
    "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean", "Bwd Packet Length Std",
    "Packet Length Variance", "Down/Up Ratio", "Average Packet Size",
    "Flow Duration", "Flow Bytes/s", "Flow Packets/s",
    "Flow IAT Mean", "Flow IAT Std", "Flow IAT Max", "Flow IAT Min",
    "Fwd IAT Mean", "Fwd IAT Std", "Fwd IAT Max", "Fwd IAT Min",
    "Bwd IAT Mean", "Bwd IAT Std", "Bwd IAT Max", "Bwd IAT Min",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(name: str) -> pd.DataFrame:
    df = pd.read_csv(DATA / name, low_memory=False)
    absent = set(FEATURES + ["traffic_type"]) - set(df.columns)
    if absent:
        raise ValueError(f"{name}: missing {sorted(absent)}")
    return df


def matrix(frame: pd.DataFrame) -> np.ndarray:
    x = frame[FEATURES].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    x[~np.isfinite(x)] = np.nan
    return x


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    train = load("train.csv")
    tests = {name: load(name) for name in ["test.csv", "test-cross.csv"]}
    x_train, y_train = matrix(train), train.traffic_type.to_numpy()
    models = {
        "Random Forest": make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(
            n_estimators=200, max_features="sqrt", min_samples_leaf=2, random_state=42, n_jobs=-1)),
        "SVM RBF": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), SVC(C=10, gamma="scale")),
        "KNN k=7": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), KNeighborsClassifier(n_neighbors=7)),
    }
    metrics, per_class, predictions = [], [], []
    for model_name, model in models.items():
        model.fit(x_train, y_train)
        for test_name, test in tests.items():
            x_test, y_test = matrix(test), test.traffic_type.to_numpy()
            pred = model.predict(x_test)
            report = classification_report(y_test, pred, labels=list(LABELS), target_names=list(LABELS.values()),
                                           output_dict=True, zero_division=0)
            metrics.append({"dataset": test_name, "model": model_name, "n_train": len(train), "n_test": len(test),
                            "accuracy": accuracy_score(y_test, pred),
                            "macro_recall": recall_score(y_test, pred, average="macro", zero_division=0),
                            "macro_f1": report["macro avg"]["f1-score"]})
            for cls in LABELS.values():
                per_class.append({"dataset": test_name, "model": model_name, "class": cls,
                                  "precision": report[cls]["precision"], "recall": report[cls]["recall"],
                                  "f1": report[cls]["f1-score"], "support": report[cls]["support"]})
            for actual, predicted in zip(y_test, pred):
                predictions.append({"dataset": test_name, "model": model_name,
                                    "actual": LABELS[int(actual)], "predicted": LABELS[int(predicted)]})
            pd.DataFrame(confusion_matrix(y_test, pred, labels=list(LABELS)),
                         index=LABELS.values(), columns=LABELS.values()).to_csv(
                             OUT / f"confusion_{model_name.replace(' ', '_').replace('=', '')}_{test_name}.csv")
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(OUT / "metrics.csv", index=False)
    pd.DataFrame(per_class).to_csv(OUT / "per_class.csv", index=False)
    pd.DataFrame(predictions).to_csv(OUT / "predictions.csv", index=False)
    (OUT / "run_manifest.json").write_text(json.dumps({
        "source": "https://github.com/das-lab/JA4Tor",
        "source_note": "NESTTOR/JA4Tor published flow tables; no capture IDs in these public CSVs",
        "labels": LABELS, "features": FEATURES,
        "files": {name: sha256(DATA / name) for name in ["train.csv", "test.csv", "test-cross.csv"]},
        "sklearn": sklearn.__version__, "seed": 42,
        "scope_warning": "NonTor is not verified to be exclusively HTTPS; Tor-SS/Trojan carry Tor; no VLESS class."
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0), sharey=True, layout="constrained")
    for ax, ds in zip(axes, tests):
        rows = metrics_df[metrics_df.dataset.eq(ds)]
        x = np.arange(len(rows))
        ax.bar(x - 0.18, rows.accuracy * 100, width=0.36, color="#1f5a85", label="Accuracy")
        ax.bar(x + 0.18, rows.macro_recall * 100, width=0.36, color="#b56d2c", label="Macro recall")
        ax.set_title("Original test" if ds == "test.csv" else "Cross test")
        ax.set_xticks(x, rows.model, rotation=15)
        ax.set_ylim(0, 100)
        ax.grid(axis="y", alpha=.2)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Percent")
    axes[1].legend(loc="lower right", frameon=False)
    fig.savefig(OUT / "accuracy_recall.png", dpi=220)
    plt.close(fig)
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
