"""
Headless caption generation runner using VLMExecutor/ModelManager.

Produces a CSV summary and returns a mapping from image absolute path to caption.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import csv
import json

from utils.log_manager import LogManager
from utils.node_threshold_manager import NodeThresholdManager
from utils.key_registry import KeyRegistry
from utils.agents.vlm_executor import VLMExecutor
from vlm.model_manager import ModelManager

# type configs from caption_maker
from .type_config import DEFAULT_TYPE_MAP, CLASSIFIER_PARAMS, CLASSIFIER_PROMPT


def _build_env() -> Tuple[LogManager, NodeThresholdManager, VLMExecutor, ModelManager]:
    cfg = {
        "nodes": [{"id": "1", "type": "vlm"}],
        "node_thresholds": {"1": {}},
        "logging": {"default_level": "MINIMAL", "node_specific_levels": {"1": "MINIMAL"}},
    }
    log = LogManager(cfg)
    thr = NodeThresholdManager(cfg)
    mm = ModelManager()
    mm.setup_model()
    vlm = VLMExecutor(log, thr, model_manager=mm)
    # Ensure thresholds lookup uses a real node_id instead of 'unknown'
    vlm.set_node_config({}, "1")
    return log, thr, vlm, mm


def _set_thresholds(thr: NodeThresholdManager, params: Dict):
    node_id = "1"
    for k, v in params.items():
        try:
            thr.set_value(node_id, k, v)
        except Exception:
            # ignore unknown keys
            pass


def classify_and_caption(images_dir: Path, out_dir: Path) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    _, thr, vlm, _ = _build_env()

    # Collect images
    imgs: List[Path] = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp"):
        imgs.extend(sorted(images_dir.glob(ext)))

    results: List[Dict] = []
    path_to_caption: Dict[str, str] = {}

    for p in imgs:
        # 1) classify
        _set_thresholds(thr, CLASSIFIER_PARAMS.to_clean_dict())
        resp = vlm.execute({KeyRegistry.USER_QUERY: CLASSIFIER_PROMPT, KeyRegistry.IMAGE_PATH: str(p)}, node_id="1")
        if resp.has_error:
            ctype = "natural_image"
        else:
            text = resp.data.get(KeyRegistry.VLM_ANSWER, "")
            ctype = None
            try:
                obj = json.loads(text)
                if isinstance(obj, dict):
                    ctype = obj.get("type")
            except Exception:
                low = text.lower()
                for t in DEFAULT_TYPE_MAP.keys():
                    if t in low:
                        ctype = t
                        break
            if ctype not in DEFAULT_TYPE_MAP:
                ctype = "natural_image"

        # 2) caption
        entry = DEFAULT_TYPE_MAP[ctype]
        caption_params = entry["params"].to_clean_dict()
        _set_thresholds(thr, caption_params)
        cap_resp = vlm.execute({KeyRegistry.USER_QUERY: entry["prompt"], KeyRegistry.IMAGE_PATH: str(p)}, node_id="1")
        caption = cap_resp.data.get(KeyRegistry.VLM_ANSWER, "") if not cap_resp.has_error else ""

        results.append({
            "file": p.name,
            "path": str(p.resolve()),
            "type": ctype,
            "preset": caption_params.get("preset"),
            "caption": caption,
        })
        path_to_caption[str(p.resolve())] = caption

    # write CSV
    csv_path = out_dir / "captions.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["file", "path", "type", "preset", "caption"])
        w.writeheader()
        for r in results:
            w.writerow(r)

    return path_to_caption
