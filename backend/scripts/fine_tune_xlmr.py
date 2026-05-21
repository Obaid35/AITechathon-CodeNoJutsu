"""
NaqsKAR — Fine-tune XLM-R for Complaint Classification
Trains 3 separate models (or heads) for:
  1. Department classification (14 labels)
  2. Urgency classification (4 labels)
  3. Sentiment classification (4 labels)

Usage:
    python scripts/fine_tune_xlmr.py

Input:
    data/synthetic_training_data.json

Output:
    models/xlmr-department/
    models/xlmr-urgency/
    models/xlmr-sentiment/
"""
import json
import os
import sys
import logging
from pathlib import Path
from collections import Counter

import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────
BASE_MODEL = "xlm-roberta-base"  # ~280MB, good balance of speed + accuracy
DATA_PATH = Path(__file__).parent.parent / "data" / "synthetic_training_data.json"
MODELS_DIR = Path(__file__).parent.parent / "models"

DEPARTMENT_LABELS = [
    "water_supply", "electricity", "gas_supply", "roads_infrastructure",
    "sanitation_sewerage", "health", "education", "police_security",
    "fire_emergency", "public_transport", "telecom", "revenue_land",
    "environment",
]

URGENCY_LABELS = ["critical", "high", "medium", "low"]
SENTIMENT_LABELS = ["angry", "frustrated", "neutral", "polite"]


# ── Dataset ─────────────────────────────────────
class ComplaintDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.encodings = tokenizer(
            texts, truncation=True, padding="max_length",
            max_length=max_length, return_tensors="pt"
        )
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


# ── Metrics ─────────────────────────────────────
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="weighted")
    return {"accuracy": acc, "f1": f1}


# ── Training Function ──────────────────────────
def train_classifier(
    task_name: str,
    texts: list[str],
    labels: list[int],
    label_names: list[str],
    output_dir: Path,
    epochs: int = 5,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
):
    logger.info(f"\n{'='*60}")
    logger.info(f"🧠 Training: {task_name}")
    logger.info(f"   Samples: {len(texts)}, Labels: {len(label_names)}")
    logger.info(f"   Distribution: {Counter(labels)}")
    logger.info(f"{'='*60}")

    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=0.15, random_state=42, stratify=labels
    )
    logger.info(f"   Train: {len(train_texts)}, Val: {len(val_texts)}")

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL, num_labels=len(label_names)
    )

    # Create datasets
    train_dataset = ComplaintDataset(train_texts, train_labels, tokenizer)
    val_dataset = ComplaintDataset(val_texts, val_labels, tokenizer)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        warmup_ratio=0.1,
        weight_decay=0.01,
        learning_rate=learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_dir=str(output_dir / "logs"),
        logging_steps=10,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),  # Use FP16 if GPU available
        report_to="none",  # No wandb/tensorboard
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # Train
    logger.info("🚀 Starting training...")
    trainer.train()

    # Evaluate
    results = trainer.evaluate()
    logger.info(f"📊 Results: {results}")

    # Detailed classification report
    preds = trainer.predict(val_dataset)
    pred_labels = np.argmax(preds.predictions, axis=-1)
    report = classification_report(val_labels, pred_labels, target_names=label_names)
    logger.info(f"\n📋 Classification Report:\n{report}")

    # Save model + tokenizer + label mapping
    final_dir = output_dir / "final"
    model.save_pretrained(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    # Save label mapping
    label_map = {i: name for i, name in enumerate(label_names)}
    with open(final_dir / "label_map.json", "w") as f:
        json.dump(label_map, f, indent=2)

    logger.info(f"✅ Model saved to: {final_dir}")
    logger.info(f"   Accuracy: {results['eval_accuracy']:.4f}")
    logger.info(f"   F1 Score: {results['eval_f1']:.4f}")

    return results


def main():
    # Load synthetic data
    if not DATA_PATH.exists():
        logger.error(f"❌ Training data not found at {DATA_PATH}")
        logger.error("   Run 'python scripts/generate_synthetic_data.py' first!")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"📂 Loaded {len(data)} training samples from {DATA_PATH}")

    # Prepare texts
    texts = [s["text"] for s in data]

    # ── 1. Department Classifier ────────────────
    dept_labels = []
    valid_texts_dept = []
    for s in data:
        dept = s.get("department", "")
        if dept in DEPARTMENT_LABELS:
            dept_labels.append(DEPARTMENT_LABELS.index(dept))
            valid_texts_dept.append(s["text"])

    train_classifier(
        task_name="Department Classifier",
        texts=valid_texts_dept,
        labels=dept_labels,
        label_names=DEPARTMENT_LABELS,
        output_dir=MODELS_DIR / "xlmr-department",
        epochs=5,
        batch_size=16,
    )

    # ── 2. Urgency Classifier ──────────────────
    urg_labels = []
    valid_texts_urg = []
    for s in data:
        urg = s.get("urgency", "")
        if urg in URGENCY_LABELS:
            urg_labels.append(URGENCY_LABELS.index(urg))
            valid_texts_urg.append(s["text"])

    train_classifier(
        task_name="Urgency Classifier",
        texts=valid_texts_urg,
        labels=urg_labels,
        label_names=URGENCY_LABELS,
        output_dir=MODELS_DIR / "xlmr-urgency",
        epochs=5,
        batch_size=16,
    )

    # ── 3. Sentiment Classifier ────────────────
    sent_labels = []
    valid_texts_sent = []
    for s in data:
        sent = s.get("sentiment", "")
        if sent in SENTIMENT_LABELS:
            sent_labels.append(SENTIMENT_LABELS.index(sent))
            valid_texts_sent.append(s["text"])

    train_classifier(
        task_name="Sentiment Classifier",
        texts=valid_texts_sent,
        labels=sent_labels,
        label_names=SENTIMENT_LABELS,
        output_dir=MODELS_DIR / "xlmr-sentiment",
        epochs=5,
        batch_size=16,
    )

    logger.info(f"\n{'='*60}")
    logger.info("🎉 ALL 3 MODELS TRAINED SUCCESSFULLY!")
    logger.info(f"📁 Models saved in: {MODELS_DIR}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
