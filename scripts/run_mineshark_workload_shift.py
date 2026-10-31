"""Probe transfer from NBMiner (Ethereum) to XMRig (Monero) captures."""

from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, recall_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from run_mineshark_proxy_baseline import FEATURES, LABELS, ROOT


OUT = ROOT / "results/mineshark"


def main():
    df = pd.read_csv(OUT / "features.csv")
    train = df[df.capture.str.startswith("nbminer/")]
    test = df[df.capture.str.startswith("xmrig/")]
    train_cap = train.label.value_counts().min()
    test_cap = test.label.value_counts().min()
    train = pd.concat([x.sample(train_cap, random_state=42) for _, x in train.groupby("label")])
    test = pd.concat([x.sample(test_cap, random_state=42) for _, x in test.groupby("label")])
    models = {
        "Random Forest": make_pipeline(SimpleImputer(strategy="median"), RandomForestClassifier(
            n_estimators=200, max_features="sqrt", min_samples_leaf=2, random_state=42, n_jobs=-1)),
        "SVM RBF": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), SVC(C=10, gamma="scale")),
        "KNN k=7": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), KNeighborsClassifier(n_neighbors=7)),
    }
    metrics = []
    per_class = []
    for name, model in models.items():
        model.fit(train[FEATURES], train.label)
        predicted = model.predict(test[FEATURES])
        report = classification_report(test.label, predicted, labels=list(LABELS.values()),
                                       output_dict=True, zero_division=0)
        metrics.append({"model": name, "n_train": len(train), "n_test": len(test),
                        "accuracy": accuracy_score(test.label, predicted),
                        "macro_recall": recall_score(test.label, predicted, average="macro", zero_division=0),
                        "macro_f1": report["macro avg"]["f1-score"]})
        for label in LABELS.values():
            per_class.append({"model": name, "class": label, **report[label]})
    pd.DataFrame(metrics).to_csv(OUT / "workload_shift_metrics.csv", index=False)
    pd.DataFrame(per_class).to_csv(OUT / "workload_shift_per_class.csv", index=False)
    print(pd.DataFrame(metrics).to_string(index=False))
    print("train windows per class", train_cap, "test windows per class", test_cap)


if __name__ == "__main__":
    main()
