from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import torch
import joblib

from src.data import one_hot
from src.models import MODELS
from src.features import feature_matrix
from src.groups import DOMAIN_IDS, MODEL_GROUPS

DEFAULT_LENGTHS = {group: details["input_length"] for group, details in MODEL_GROUPS.items()}
MAX_RECORDS = 10_000


@dataclass(frozen=True)
class SequenceRecord:
    sequence_id: str
    sequence: str


def parse_sequence(text: str, sequence_id: str = "sequence_1") -> list[SequenceRecord]:
    sequence = re.sub(r"\s+", "", text).upper()
    if not sequence:
        raise ValueError("Enter a DNA sequence.")
    _validate_sequence(sequence, sequence_id)
    return [SequenceRecord(sequence_id, sequence)]


def parse_fasta(text: str) -> list[SequenceRecord]:
    records: list[SequenceRecord] = []
    header: str | None = None
    chunks: list[str] = []
    seen: dict[str, int] = {}

    def append_record() -> None:
        if header is None:
            return
        if len(records) >= MAX_RECORDS:
            return
        sequence = re.sub(r"\s+", "", "".join(chunks)).upper()
        if not sequence:
            raise ValueError(f"FASTA record {header!r} has no sequence.")
        _validate_sequence(sequence, header)
        count = seen.get(header, 0) + 1
        seen[header] = count
        unique_id = header if count == 1 else f"{header} ({count})"
        records.append(SequenceRecord(unique_id, sequence))

    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            append_record()
            header = line[1:].strip()
            chunks = []
            if not header:
                raise ValueError(f"FASTA header on line {line_number} is empty.")
        elif header is None:
            raise ValueError(f"Expected a FASTA header ('>') before line {line_number}.")
        else:
            chunks.append(line)
    append_record()
    if not records:
        raise ValueError("The FASTA file contains no records.")
    return records


def _validate_sequence(sequence: str, sequence_id: str) -> None:
    invalid = sorted(set(sequence) - set("ACGTN"))
    if invalid:
        chars = ", ".join(repr(char) for char in invalid)
        raise ValueError(f"Sequence {sequence_id!r} contains invalid nucleotide(s): {chars}. Use A, C, G, T, or N.")


class ModelRegistry:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.checkpoint_root = project_root / "results" / "checkpoints"
        self.input_lengths = self._input_lengths()
        ensemble_path = project_root / "results" / "main_tables" / "multiseed_ensemble.json"
        payload = json.loads(ensemble_path.read_text()) if ensemble_path.exists() else {}
        organism_metadata = payload.get("organism_models", {})
        manifest_path = project_root / "webapp" / "model_manifest.json"
        serving_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        self.ensemble_metadata = {**serving_manifest, **organism_metadata}

    def hybrid_metadata(self, group: str) -> dict | None:
        path = self.project_root / "results" / "hybrid_models" / group / "metadata.json"
        if not path.exists(): return None
        metadata=json.loads(path.read_text())
        # Version-1 forests used the removed N-ratio/legacy schema and are not
        # dimensionally compatible with the validation-selected version-2 blocks.
        return metadata if metadata.get("feature_version",1) >= 2 else None

    @lru_cache(maxsize=3)
    def load_forest(self, group: str):
        path = self.project_root / "results" / "hybrid_models" / group / "random_forest.joblib"
        return joblib.load(path)

    def _input_lengths(self) -> dict[str, int]:
        # These are tensor/feature lengths, not necessarily natural sequence lengths.
        # B. subtilis is naturally 80 nt and is masked/padded to the bacterial 81-nt input.
        return DEFAULT_LENGTHS.copy()

    def checkpoint_for(self, group: str) -> Path:
        if group not in MODEL_GROUPS:
            raise ValueError(f"Unsupported model group: {group!r}.")
        candidates = list((self.checkpoint_root / group).glob("**/best_mcc.pt"))
        if not candidates:
            raise FileNotFoundError(f"No trained checkpoint is available for {group}.")

        def mcc(path: Path) -> float:
            checkpoint = torch.load(path, map_location="cpu", weights_only=False)
            return float(checkpoint.get("best_mcc", -2))

        return max(candidates, key=mcc)

    @lru_cache(maxsize=3)
    def load(self, group: str):
        ensemble = self.ensemble_metadata.get(group)
        if ensemble:
            model_name = ensemble["model"]
            seeds = ensemble["seeds"]
            paths = self._ensemble_paths(group, ensemble)
            if paths:
                models = []
                for path in paths:
                    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
                    model = MODELS[model_name](**checkpoint.get("config", {}))
                    model.load_state_dict(checkpoint["model"])
                    model.eval()
                    models.append(model)
                return tuple(models), float(ensemble["threshold"]), f"{model_name}_3_seed_ensemble", tuple(paths)

        checkpoint_path = self.checkpoint_for(group)
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model_name = checkpoint["model_name"]
        model = MODELS[model_name](**checkpoint.get("config", {}))
        model.load_state_dict(checkpoint["model"])
        model.eval()
        history = checkpoint.get("history", [])
        best_epoch = int(checkpoint.get("epoch", -1))
        epoch_row = next((row for row in history if int(row["epoch"]) == best_epoch), None)
        threshold = float((epoch_row or history[-1])["threshold"]) if history else 0.5
        return (model,), threshold, model_name, (checkpoint_path,)

    def _ensemble_paths(self, group: str, ensemble: dict) -> list[Path] | None:
        model_root = self.checkpoint_root / group / ensemble["model"]
        run = ensemble.get("run")
        directories = [model_root / run] if run else (
            [directory for directory in model_root.iterdir() if directory.is_dir()] if model_root.exists() else []
        )
        for directory in directories:
            paths = [directory / f"seed_{seed}" / "best_mcc.pt" for seed in ensemble["seeds"]]
            if all(path.exists() for path in paths):
                return paths
        return None

    def describe(self) -> list[dict]:
        descriptions = []
        for group, details in MODEL_GROUPS.items():
            ensemble = self.ensemble_metadata.get(group)
            paths = self._ensemble_paths(group, ensemble) if ensemble else None
            try:
                if paths:
                    threshold = float(ensemble["threshold"])
                    model_name = f"{ensemble['model']}_3_seed_ensemble"
                else:
                    checkpoint = self.checkpoint_for(group)
                    saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
                    model_name = saved["model_name"]
                    threshold = 0.5
                    paths = [checkpoint]
                hybrid = self.hybrid_metadata(group)
                descriptions.append({"model_group": group, "domain": details["domain"], "organism": details["organism"], "available": True,
                    "model": f"cnn_kmer_rf_hybrid ({model_name})" if hybrid else model_name,
                    "threshold": hybrid["threshold"] if hybrid else threshold,
                    "maximum_length": self.input_lengths[group],
                    "cnn_weight": hybrid["cnn_weight"] if hybrid else 1.0,
                    "random_forest_weight": hybrid["random_forest_weight"] if hybrid else 0.0,
                    "checkpoints": [str(path.relative_to(self.project_root)) for path in paths]})
            except FileNotFoundError:
                descriptions.append({"model_group": group, "domain": details["domain"], "organism": details["organism"], "available": False})
        return descriptions

    def predict(self, group: str, records: list[SequenceRecord], batch_size: int = 128) -> dict:
        if group not in MODEL_GROUPS: raise ValueError(f"Unsupported model group: {group!r}.")
        details=MODEL_GROUPS[group]; models, threshold, model_name, _ = self.load(group)
        hybrid = self.hybrid_metadata(group)
        if hybrid:
            threshold = float(hybrid["threshold"])
            model_name = f"cnn_kmer_rf_hybrid ({model_name})"
        max_length = self.input_lengths[group]
        too_long = [(record.sequence_id, len(record.sequence)) for record in records if len(record.sequence) > max_length]
        if too_long:
            name, length = too_long[0]
            raise ValueError(f"Sequence {name!r} is {length} nt; the {group} model accepts at most {max_length} nt.")

        results = []
        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]
            encoded = [one_hot(record.sequence, max_length) for record in batch]
            x = torch.stack([item[0] for item in encoded])
            mask = torch.stack([item[2] for item in encoded])
            lengths = torch.tensor([len(record.sequence) for record in batch])
            domains = torch.full((len(batch),), DOMAIN_IDS[details["domain"]], dtype=torch.long)
            with torch.inference_mode():
                model_probabilities = []
                for model in models:
                    output = model(x, mask, length=lengths, domain=domains)
                    logits = output if torch.is_tensor(output) else 0.5 * output["shared"] + 0.5 * output["specialist"]
                    model_probabilities.append(torch.sigmoid(logits))
                cnn_probabilities = torch.stack(model_probabilities).mean(0).numpy()
            if hybrid:
                forest = self.load_forest(group)
                features = feature_matrix([record.sequence for record in batch],max_length,details["domain"],
                                          hybrid.get("feature_blocks", ("canonical_kmers","position_specific","stability")))
                rf_probabilities = forest.predict_proba(features)[:, 1]
                probabilities = (
                    float(hybrid["cnn_weight"]) * cnn_probabilities
                    + float(hybrid["random_forest_weight"]) * rf_probabilities
                ).tolist()
            else:
                probabilities = cnn_probabilities.tolist()
            for record, probability in zip(batch, probabilities):
                results.append({"sequence_id": record.sequence_id, "length": len(record.sequence),
                    "promoter_probability": round(float(probability), 6),
                    "predicted_class": "promoter" if probability >= threshold else "non-promoter"})

        promoter_count = sum(row["predicted_class"] == "promoter" for row in results)
        return {"model_group": group, "domain": details["domain"], "organism": details["organism"], "model": model_name, "threshold": round(threshold, 6), "total": len(results),
            "summary": {"promoter": promoter_count, "non_promoter": len(results) - promoter_count},
            "predictions": results}
