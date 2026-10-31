"""Classify real MineShark proxy traces with size, IAT and direction features.

This experiment uses three archive labels: ShadowsocksR, Trojan and VMess.
The archive contains neither VLESS nor ordinary HTTPS labels. Each 60-second
window is a sample; original capture files are disjoint across train and test.
"""

from __future__ import annotations

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
DATA = ROOT / "data/raw/mineshark_subset/dataset/obfuscated"
OUT = ROOT / "results/mineshark"
LABELS = {"ssr": "ShadowsocksR", "trojan": "Trojan", "v2ray": "VMess"}
SEED = 42
WINDOW = 60
MIN_PACKETS = 12
FEATURES = [
    "packet_count", "total_bytes", "duration_s", "packet_rate",
    "frame_mean", "frame_std", "frame_median", "frame_p90", "frame_min", "frame_max",
    "iat_mean_ms", "iat_std_ms", "iat_median_ms", "iat_p90_ms", "iat_max_ms",
    "up_count_ratio", "down_up_bytes_ratio", "up_frame_mean", "down_frame_mean",
    "direction_switch_rate",
]


def features_from_window(frame: pd.DataFrame, local_ip: str) -> dict:
    lengths = frame["frame.len"].to_numpy(dtype=float)
    times = frame["frame.time_epoch"].to_numpy(dtype=float)
    up = frame["ip.src"].eq(local_ip).to_numpy()
    gaps = np.diff(times) * 1000.0
    gaps = np.maximum(gaps, 0)
    ups = lengths[up]
    downs = lengths[~up]
    duration = max(float(times[-1] - times[0]), 1e-9)
    return {
        "packet_count": len(lengths), "total_bytes": lengths.sum(), "duration_s": duration,
        "packet_rate": len(lengths) / duration,
        "frame_mean": lengths.mean(), "frame_std": lengths.std(),
        "frame_median": np.median(lengths), "frame_p90": np.quantile(lengths, .9),
        "frame_min": lengths.min(), "frame_max": lengths.max(),
        "iat_mean_ms": gaps.mean(), "iat_std_ms": gaps.std(),
        "iat_median_ms": np.median(gaps), "iat_p90_ms": np.quantile(gaps, .9),
        "iat_max_ms": gaps.max(),
        "up_count_ratio": up.mean(),
        "down_up_bytes_ratio": downs.sum() / max(ups.sum(), 1),
        "up_frame_mean": ups.mean() if len(ups) else 0,
        "down_frame_mean": downs.mean() if len(downs) else 0,
        "direction_switch_rate": np.mean(up[1:] != up[:-1]),
    }


def build_features() -> pd.DataFrame:
    rows = []
    files = sorted(DATA.glob("*/*/*.tsv"))
    for i, path in enumerate(files, 1):
        label = path.parent.name
        if label not in LABELS:
            continue
        frame = pd.read_csv(path, sep="\t", usecols=["frame.time_epoch", "frame.len", "ip.src", "tcp.srcport"])
        frame = frame.dropna(subset=["frame.time_epoch", "frame.len", "ip.src", "tcp.srcport"])
        frame = frame[(frame["frame.len"] > 0) & np.isfinite(frame["frame.time_epoch"])]
        frame = frame.sort_values("frame.time_epoch", kind="mergesort")
        if len(frame) < MIN_PACKETS:
            continue
        private = frame["ip.src"].astype(str).str.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18."))
        local_ip = str(frame.loc[private, "ip.src"].mode().iloc[0]) if private.any() else str(frame["ip.src"].iloc[0])
        start = float(frame["frame.time_epoch"].iloc[0])
        frame = frame.assign(window=np.floor((frame["frame.time_epoch"] - start) / WINDOW).astype(int))
        for window_id, window in frame.groupby("window", sort=True):
            if len(window) < MIN_PACKETS:
                continue
            rows.append({"capture": str(path.relative_to(DATA)).replace("\\", "/"),
                         "label": LABELS[label], "window": int(window_id),
                         **features_from_window(window, local_ip)})
        if i % 40 == 0:
            print(f"processed {i}/{len(files)} captures", flush=True)
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("No windows extracted")
    result.to_csv(OUT / "features.csv", index=False)
    return result


def balanced_split(frame: pd.DataFrame):
    rng = np.random.default_rng(SEED)
    train_parts, test_parts, split_rows = [], [], []
    for label in LABELS.values():
        captures = np.array(sorted(frame.loc[frame.label.eq(label), "capture"].unique()))
        rng.shuffle(captures)
        n_test = max(1, round(.3 * len(captures)))
        test_set = set(captures[:n_test])
        for capture in captures:
            split_rows.append({"capture": capture, "label": label,
                               "split": "test" if capture in test_set else "train"})
        part = frame[frame.label.eq(label)]
        train_parts.append(part[~part.capture.isin(test_set)])
        test_parts.append(part[part.capture.isin(test_set)])
    train_cap = min(map(len, train_parts))
    test_cap = min(map(len, test_parts))
    train = pd.concat([x.sample(train_cap, random_state=SEED) for x in train_parts], ignore_index=True)
    test = pd.concat([x.sample(test_cap, random_state=SEED) for x in test_parts], ignore_index=True)
    pd.DataFrame(split_rows).to_csv(OUT / "capture_splits.csv", index=False)
    train[["capture", "window", "label"]].to_csv(OUT / "train_windows.csv", index=False)
    test[["capture", "window", "label"]].to_csv(OUT / "test_windows.csv", index=False)
    assert set(train.capture).isdisjoint(set(test.capture))
    return train, test, train_cap, test_cap


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frame = build_features()
    train, test, train_cap, test_cap = balanced_split(frame)
    x_train, y_train = train[FEATURES], train.label
    x_test, y_test = test[FEATURES], test.label
    models = {
        "Random Forest": make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(
            n_estimators=200, max_features="sqrt", min_samples_leaf=2, random_state=SEED, n_jobs=-1)),
        "SVM RBF": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), SVC(C=10, gamma="scale")),
        "KNN k=7": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), KNeighborsClassifier(n_neighbors=7)),
    }
    summary, classes, preds = [], [], []
    for model_name, model in models.items():
        model.fit(x_train, y_train)
        predicted = model.predict(x_test)
        report = classification_report(y_test, predicted, labels=list(LABELS.values()),
                                       output_dict=True, zero_division=0)
        summary.append({"model": model_name, "n_train": len(train), "n_test": len(test),
                        "accuracy": accuracy_score(y_test, predicted),
                        "macro_recall": recall_score(y_test, predicted, average="macro", zero_division=0),
                        "macro_f1": report["macro avg"]["f1-score"]})
        for label in LABELS.values():
            classes.append({"model": model_name, "class": label, **report[label]})
        for _, row in test[["capture", "window", "label"]].reset_index(drop=True).iterrows():
            idx = len(preds) % len(test)
            preds.append({"model": model_name, "capture": row.capture, "window": row.window,
                          "actual": row.label, "predicted": predicted[idx]})
        pd.DataFrame(confusion_matrix(y_test, predicted, labels=list(LABELS.values())),
                     index=LABELS.values(), columns=LABELS.values()).to_csv(
                         OUT / f"confusion_{model_name.replace(' ', '_').replace('=', '')}.csv")
    result = pd.DataFrame(summary)
    result.to_csv(OUT / "metrics.csv", index=False)
    pd.DataFrame(classes).to_csv(OUT / "per_class.csv", index=False)
    pd.DataFrame(preds).to_csv(OUT / "predictions.csv", index=False)
    (OUT / "run_manifest.json").write_text(json.dumps({
        "source": "https://zenodo.org/records/13624058", "archive_md5": "6c64268ec35414fc9f483a7a4ed43755",
        "labels": LABELS, "window_seconds": WINDOW, "minimum_packets": MIN_PACKETS,
        "features": FEATURES, "seed": SEED, "train_windows_per_class": train_cap,
        "test_windows_per_class": test_cap, "capture_count_per_class": frame.groupby("label").capture.nunique().to_dict(),
        "windows_per_class": frame.label.value_counts().to_dict(), "sklearn": sklearn.__version__,
        "scope_warning": "Mining traffic only; classes are ShadowsocksR, Trojan and VMess, not Shadowsocks/VLESS/HTTPS."
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    fig, ax = plt.subplots(figsize=(7.3, 3.7), layout="constrained")
    x = np.arange(len(result))
    ax.bar(x - .19, result.accuracy * 100, .38, color="#1f5a85", label="Accuracy")
    ax.bar(x + .19, result.macro_recall * 100, .38, color="#b56d2c", label="Macro recall")
    ax.set_xticks(x, result.model)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Percent")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
    fig.savefig(OUT / "accuracy_recall.png", dpi=220)
    plt.close(fig)
    print(result.to_string(index=False))
    print(frame.groupby("label").agg(captures=("capture", "nunique"), windows=("window", "size")))


if __name__ == "__main__":
    main()
