"""QLoRA fine-tuning script for code-migration on Qwen 2.5 7B.

Designed for Kaggle's free T4 (or any 16 GB GPU). Uses Unsloth — it patches
HuggingFace transformers + PEFT to ~2x train throughput on T4-class hardware.

Run:
    python -m code_migrator.train.train \\
        --dataset examples/dataset/train.jsonl \\
        --output_dir ./out/qwen-codemigrator-v1

Or use `notebooks/kaggle_train.ipynb` which wraps this with the right install.

This script is GPU-only by design. Import-time it doesn't require torch — the
heavy imports happen inside main() so the eval harness and inference layer
stay importable on CPU-only laptops.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ..data.schema import MigrationPair


# Hyperparameters picked for a small (~5K example) instruction-tuning run on
# a single T4. Verified to fit in 16 GB with 4-bit QLoRA. For larger datasets
# bump epochs to 1 (still enough; the gain past 1 epoch is marginal).
HYPERPARAMS = dict(
    model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
    lora_r=16,
    lora_alpha=16,
    lora_dropout=0.0,
    learning_rate=2e-4,
    batch_size=2,
    gradient_accumulation_steps=8,
    epochs=3,
    warmup_ratio=0.05,
    weight_decay=0.01,
    seed=42,
)


def load_dataset(path: Path) -> list[MigrationPair]:
    pairs: list[MigrationPair] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        pairs.append(MigrationPair.model_validate(json.loads(line)))
    return pairs


def format_for_training(pair: MigrationPair) -> dict[str, str]:
    """One-row format the trainer consumes: messages-of-role JSON."""
    return {
        "instruction": pair.prompt(),
        "response": pair.target(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument("--output_dir", required=True, type=Path)
    parser.add_argument("--epochs", type=int, default=HYPERPARAMS["epochs"])
    parser.add_argument("--max_steps", type=int, default=-1, help="-1 = epoch-based")
    args = parser.parse_args(argv)

    # --- GPU-only imports ----------------------------------------------------
    try:
        import torch
        from unsloth import FastLanguageModel  # type: ignore
        from trl import SFTConfig, SFTTrainer  # type: ignore
        from datasets import Dataset  # type: ignore
    except ImportError as e:
        print(
            "GPU dependencies missing. Run on Kaggle/Colab with a T4+ GPU, or:\n"
            "    pip install 'unsloth[colab-new]' trl datasets accelerate peft bitsandbytes\n"
            f"Underlying error: {e}"
        )
        return 1

    if not torch.cuda.is_available():
        print("No CUDA device. Fine-tuning a 7B model on CPU is not viable.")
        return 1

    pairs = load_dataset(args.dataset)
    print(f"Loaded {len(pairs)} training pairs from {args.dataset}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=HYPERPARAMS["model_name"],
        max_seq_length=HYPERPARAMS["max_seq_length"],
        load_in_4bit=HYPERPARAMS["load_in_4bit"],
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=HYPERPARAMS["lora_r"],
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=HYPERPARAMS["lora_alpha"],
        lora_dropout=HYPERPARAMS["lora_dropout"],
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=HYPERPARAMS["seed"],
    )

    # Build the training dataset in instruction-response format
    rows = [format_for_training(p) for p in pairs]

    def format_row(row: dict) -> dict:
        text = (
            f"<|im_start|>user\n{row['instruction']}<|im_end|>\n"
            f"<|im_start|>assistant\n{row['response']}<|im_end|>"
        )
        return {"text": text}

    ds = Dataset.from_list(rows).map(format_row)

    config = SFTConfig(
        output_dir=str(args.output_dir),
        per_device_train_batch_size=HYPERPARAMS["batch_size"],
        gradient_accumulation_steps=HYPERPARAMS["gradient_accumulation_steps"],
        num_train_epochs=args.epochs,
        max_steps=args.max_steps,
        learning_rate=HYPERPARAMS["learning_rate"],
        warmup_ratio=HYPERPARAMS["warmup_ratio"],
        weight_decay=HYPERPARAMS["weight_decay"],
        logging_steps=10,
        save_steps=200,
        seed=HYPERPARAMS["seed"],
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        optim="adamw_8bit",
        max_seq_length=HYPERPARAMS["max_seq_length"],
        dataset_text_field="text",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        args=config,
    )

    print("Starting training…")
    stats = trainer.train()
    print(stats)

    # Save the LoRA adapters separately + a merged 4-bit model for inference.
    os.makedirs(args.output_dir, exist_ok=True)
    model.save_pretrained(str(args.output_dir / "lora"))
    tokenizer.save_pretrained(str(args.output_dir / "lora"))
    try:
        model.save_pretrained_merged(
            str(args.output_dir / "merged"),
            tokenizer,
            save_method="merged_4bit_forced",
        )
    except Exception as e:
        print(f"merged save skipped: {e}")

    print(f"Done. Adapters at {args.output_dir / 'lora'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
