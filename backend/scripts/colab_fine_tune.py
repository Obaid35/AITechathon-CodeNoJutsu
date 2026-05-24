# NaqsKAR — Fine-tune XLM-R on Google Colab
# Upload this notebook to colab.research.google.com
# Runtime → Change runtime type → GPU (T4)

# ============================================
# CELL 1: Install Dependencies
# ============================================
# !pip install transformers datasets torch scikit-learn accelerate -q

# ============================================
# CELL 2: Upload Data
# ============================================
# from google.colab import files
# uploaded = files.upload()  # Upload synthetic_training_data.json

# ============================================
# CELL 3: Load & Prepare Data
# ============================================
import json
import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    TrainingArguments, Trainer, EarlyStoppingCallback,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report,
    confusion_matrix, ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
import pandas as pd

# Load data
with open("synthetic_training_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"Loaded {len(data)} samples")

DEPT_LABELS = [
    "water_supply", "electricity", "gas_supply", "roads_infrastructure",
    "sanitation_sewerage", "health", "education", "police_security",
    "fire_emergency", "public_transport", "telecom", "revenue_land", "environment",
]
URG_LABELS = ["critical", "high", "medium", "low"]
SENT_LABELS = ["angry", "frustrated", "neutral", "polite"]

# ============================================
# CELL 4: Dataset Class
# ============================================
class ComplaintDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(texts, truncation=True, padding="max_length", max_length=max_length, return_tensors="pt")
        self.labels = torch.tensor(labels, dtype=torch.long)
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {"accuracy": accuracy_score(labels, preds), "f1": f1_score(labels, preds, average="weighted")}

# ============================================
# CELL 5: Train Function (generates all tables for judges)
# ============================================
BASE_MODEL = "xlm-roberta-base"

def train_and_evaluate(task_name, texts, labels, label_names, save_dir):
    print(f"\n{'='*60}")
    print(f"  Training: {task_name}")
    print(f"  Samples: {len(texts)} | Labels: {len(label_names)}")
    print(f"{'='*60}")

    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=len(label_names))

    train_ds = ComplaintDataset(train_texts, train_labels, tokenizer)
    val_ds = ComplaintDataset(val_texts, val_labels, tokenizer)

    args = TrainingArguments(
        output_dir=f"./{save_dir}/checkpoints",
        num_train_epochs=5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_ratio=0.1,
        weight_decay=0.01,
        learning_rate=2e-5,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=10,
        save_total_limit=2,
        fp16=True,
        report_to="none",
    )

    trainer = Trainer(
        model=model, args=args,
        train_dataset=train_ds, eval_dataset=val_ds,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    trainer.train()

    # ── TABLE 1: Training Metrics Per Epoch ──
    logs = [l for l in trainer.state.log_history if "eval_accuracy" in l]
    metrics_table = []
    for i, log in enumerate(logs):
        metrics_table.append({
            "Epoch": i + 1,
            "Train Loss": round(log.get("loss", log.get("train_loss", 0)), 4),
            "Val Loss": round(log.get("eval_loss", 0), 4),
            "Val Accuracy": round(log.get("eval_accuracy", 0), 4),
            "Val F1": round(log.get("eval_f1", 0), 4),
        })
    df_metrics = pd.DataFrame(metrics_table)
    print(f"\n📊 {task_name} — Training Metrics:")
    print(df_metrics.to_string(index=False))

    # ── TABLE 2: Classification Report ──
    preds = trainer.predict(val_ds)
    pred_labels = np.argmax(preds.predictions, axis=-1)
    report = classification_report(val_labels, pred_labels, target_names=label_names, output_dict=True)
    df_report = pd.DataFrame(report).transpose()
    print(f"\n📋 {task_name} — Classification Report:")
    print(df_report.round(3).to_string())

    # ── CHART 3: Confusion Matrix ──
    cm = confusion_matrix(val_labels, pred_labels)
    fig, ax = plt.subplots(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(cm, display_labels=label_names)
    disp.plot(ax=ax, cmap="Blues", xticks_rotation=45)
    ax.set_title(f"{task_name} — Confusion Matrix")
    plt.tight_layout()
    plt.savefig(f"{save_dir}_confusion_matrix.png", dpi=150)
    plt.show()
    print(f"💾 Confusion matrix saved: {save_dir}_confusion_matrix.png")

    # ── CHART 4: Accuracy & F1 Over Epochs ──
    if metrics_table:
        fig, ax = plt.subplots(figsize=(8, 5))
        epochs = [m["Epoch"] for m in metrics_table]
        ax.plot(epochs, [m["Val Accuracy"] for m in metrics_table], "o-", label="Accuracy", color="#4285F4")
        ax.plot(epochs, [m["Val F1"] for m in metrics_table], "s-", label="F1 Score", color="#EA4335")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Score")
        ax.set_title(f"{task_name} — Training Progress")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{save_dir}_training_progress.png", dpi=150)
        plt.show()

    # Save model
    model.save_pretrained(f"./{save_dir}/final")
    tokenizer.save_pretrained(f"./{save_dir}/final")
    label_map = {i: name for i, name in enumerate(label_names)}
    with open(f"./{save_dir}/final/label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)

    final_acc = round(logs[-1]["eval_accuracy"], 4) if logs else 0
    final_f1 = round(logs[-1]["eval_f1"], 4) if logs else 0
    print(f"\n✅ {task_name} DONE! Accuracy: {final_acc} | F1: {final_f1}")
    return {"task": task_name, "accuracy": final_acc, "f1": final_f1}

# ============================================
# CELL 6: Train All 3 Models
# ============================================

# Prepare data
dept_texts, dept_labels = [], []
urg_texts, urg_labels = [], []
sent_texts, sent_labels = [], []

for s in data:
    if s.get("department") in DEPT_LABELS:
        dept_texts.append(s["text"])
        dept_labels.append(DEPT_LABELS.index(s["department"]))
    if s.get("urgency") in URG_LABELS:
        urg_texts.append(s["text"])
        urg_labels.append(URG_LABELS.index(s["urgency"]))
    if s.get("sentiment") in SENT_LABELS:
        sent_texts.append(s["text"])
        sent_labels.append(SENT_LABELS.index(s["sentiment"]))

results = []
results.append(train_and_evaluate("Department Classifier", dept_texts, dept_labels, DEPT_LABELS, "xlmr-department"))
results.append(train_and_evaluate("Urgency Classifier", urg_texts, urg_labels, URG_LABELS, "xlmr-urgency"))
results.append(train_and_evaluate("Sentiment Classifier", sent_texts, sent_labels, SENT_LABELS, "xlmr-sentiment"))

# ============================================
# CELL 7: Final Summary Table (for judges)
# ============================================
print(f"\n{'='*60}")
print("  FINAL RESULTS SUMMARY")
print(f"{'='*60}")
df_results = pd.DataFrame(results)
print(df_results.to_string(index=False))

# ============================================
# CELL 8: Download trained models
# ============================================
# import shutil
# for name in ["xlmr-department", "xlmr-urgency", "xlmr-sentiment"]:
#     shutil.make_archive(name, "zip", f"./{name}/final")
#     files.download(f"{name}.zip")
# print("All models downloaded!")
