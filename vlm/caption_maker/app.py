import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QGroupBox, QFormLayout, QLineEdit,
    QTabWidget, QListWidget, QListWidgetItem
)

# Ensure project root on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.log_manager import LogManager
from utils.node_threshold_manager import NodeThresholdManager
from utils.key_registry import KeyRegistry
from utils.agents.vlm_executor import VLMExecutor
from vlm.model_manager import ModelManager

# Import type configuration with robust fallbacks (supports direct file run)
try:
    from .type_config import DEFAULT_TYPE_MAP, CLASSIFIER_PARAMS, CLASSIFIER_PROMPT, VLMParamSet  # type: ignore
except Exception:
    try:
        from caption_maker.type_config import (
            DEFAULT_TYPE_MAP, CLASSIFIER_PARAMS, CLASSIFIER_PROMPT, VLMParamSet
        )  # type: ignore
    except Exception:
        TYPE_DIR = Path(__file__).resolve().parent
        if str(TYPE_DIR) not in sys.path:
            sys.path.insert(0, str(TYPE_DIR))
        from type_config import DEFAULT_TYPE_MAP, CLASSIFIER_PARAMS, CLASSIFIER_PROMPT, VLMParamSet  # type: ignore


def build_default_config() -> Dict[str, Any]:
    return {
        "nodes": [{"id": "1", "type": "vlm"}],
        "node_thresholds": {"1": {}},
        "logging": {"default_level": "MINIMAL", "node_specific_levels": {"1": "MINIMAL"}},
    }


def set_thresholds(thresholds: NodeThresholdManager, node_id: str, params: Dict[str, Any]):
    for k, v in params.items():
        thresholds.set_value(node_id, k, v)


def to_pixmap(path: Path, max_w: int = 200, max_h: int = 150) -> QPixmap:
    img = QImage(str(path))
    if img.isNull():
        pm = QPixmap(max_w, max_h)
        pm.fill(Qt.lightGray)
        return pm
    pm = QPixmap.fromImage(img)
    return pm.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)


_RE_HIRA = r"\u3040-\u309F"
_RE_KATA = r"\u30A0-\u30FF\uFF66-\uFF9D"
_RE_CJK = r"\u4E00-\u9FFF"

def _has_hiragana_katakana(text: str) -> bool:
    import re
    return re.search(f"[{_RE_HIRA}{_RE_KATA}]", text) is not None

def _has_cjk(text: str) -> bool:
    import re
    return re.search(f"[{_RE_CJK}]", text) is not None

def _needs_language_retry(text: str) -> bool:
    if not text:
        return False
    return _has_cjk(text) and not _has_hiragana_katakana(text)

STRICT_LANGUAGE_SUFFIX = (
    " 出力は必ず日本語のみ。ひらがな/カタカナを含めてください。"
    "中国語の簡体字・繁体字の使用は禁止です。"
)


class CaptionWorker(QThread):
    progress = Signal(int, str)
    finished_one = Signal(int, dict)
    finished_all = Signal()
    error = Signal(str)

    def __init__(self, image_paths: List[Path], exec_env: Dict[str, Any], type_map: Dict[str, Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.exec_env = exec_env
        self.type_map = type_map
        self._stopping = False

    def stop(self):
        self._stopping = True

    def _run_vlm(self, user_query: str, image_path: Path, params: VLMParamSet | Dict[str, Any]) -> str:
        node_id = "1"
        vlm: VLMExecutor = self.exec_env["vlm"]
        thresholds: NodeThresholdManager = self.exec_env["thresholds"]
        param_dict = params.to_clean_dict() if isinstance(params, VLMParamSet) else {k: v for k, v in params.items() if v is not None}
        set_thresholds(thresholds, node_id, param_dict)
        current_data = {KeyRegistry.USER_QUERY: user_query, KeyRegistry.IMAGE_PATH: str(image_path)}
        result = vlm.execute(current_data=current_data, node_id=node_id)
        if result.has_error:
            raise RuntimeError(result.data.get("error", "VLM error"))
        return result.data.get(KeyRegistry.VLM_ANSWER, "")

    def _classify(self, image_path: Path) -> Dict[str, Any]:
        try:
            resp = self._run_vlm(CLASSIFIER_PROMPT, image_path, CLASSIFIER_PARAMS)
            parsed = None
            try:
                parsed = json.loads(resp)
            except Exception:
                lowered = resp.lower()
                t = None
                for cand in list(DEFAULT_TYPE_MAP.keys()):
                    if cand in lowered:
                        t = cand
                        break
                parsed = {"type": t or "natural_image", "confidence": 0.5, "reason": resp[:200]}
            if parsed and isinstance(parsed, dict) and parsed.get("type") in DEFAULT_TYPE_MAP:
                return parsed
            else:
                return {"type": "natural_image", "confidence": 0.3, "reason": "fallback"}
        except Exception as e:
            return {"type": "natural_image", "confidence": 0.0, "reason": f"classifier error: {e}"}

    def run(self):
        for idx, img_path in enumerate(self.image_paths):
            if self._stopping:
                break
            try:
                self.progress.emit(idx, f"Classifying {img_path.name} ...")
                cls = self._classify(img_path)
                ctype = cls.get("type", "natural_image")
                cfg = self.type_map.get(ctype, DEFAULT_TYPE_MAP["natural_image"])  # safe default
                params: VLMParamSet = cfg.get("params")
                prompt: str = cfg.get("prompt", "画像の内容を日本語で説明してください。")
                self.progress.emit(idx, f"Captioning {img_path.name} as {ctype} ...")
                caption = self._run_vlm(prompt, img_path, params)
                if _needs_language_retry(caption):
                    strict_params = params.to_clean_dict() if isinstance(params, VLMParamSet) else dict(params)
                    strict_params.update({
                        "do_sample": False,
                        "temperature": 0.0,
                        "top_p": 1.0,
                        "top_k": 20,
                        "num_beams": max(3, int(strict_params.get("num_beams", 1))),
                        "repetition_penalty": max(1.02, float(strict_params.get("repetition_penalty", 1.02))),
                    })
                    caption2 = self._run_vlm(prompt + STRICT_LANGUAGE_SUFFIX, img_path, strict_params)
                    if caption2 and (not _needs_language_retry(caption2)):
                        caption = caption2
                self.finished_one.emit(idx, {
                    "type": ctype,
                    "caption": caption,
                    "classifier": cls,
                    "params": params.to_clean_dict() if isinstance(params, VLMParamSet) else params,
                })
            except Exception as e:
                self.finished_one.emit(idx, {
                    "type": "error",
                    "caption": f"[ERROR] {e}",
                    "classifier": {"reason": "exception"},
                    "params": {},
                })
        self.finished_all.emit()


class ParamPanel(QGroupBox):
    """Simple parameter editor for presets and common knobs."""
    def __init__(self, title: str, param_set: VLMParamSet, parent=None):
        super().__init__(title, parent)
        self.param_set = param_set
        self._build()

    def _build(self):
        form = QFormLayout(self)

        # Preset
        self.preset = QComboBox()
        self.preset.addItem("(none)", None)
        for p in ["accurate", "balanced", "ocr", "qa", "code", "creative", "summary", "json"]:
            self.preset.addItem(p, p)
        form.addRow("preset", self.preset)

        # Common numeric params
        def add_float(label, init, minimum, maximum, step=0.1):
            w = QDoubleSpinBox()
            w.setRange(minimum, maximum)
            w.setSingleStep(step)
            if init is not None:
                w.setValue(init)
            form.addRow(label, w)
            return w

        def add_int(label, init, minimum, maximum, step=1):
            w = QSpinBox()
            w.setRange(minimum, maximum)
            w.setSingleStep(step)
            if init is not None:
                w.setValue(init)
            form.addRow(label, w)
            return w

        def add_bool(label, init):
            w = QCheckBox()
            if init:
                w.setChecked(True)
            form.addRow(label, w)
            return w

        self.temperature = add_float("temperature", self.param_set.temperature or 0.7, 0.0, 2.0, 0.1)
        self.top_p = add_float("top_p", self.param_set.top_p or 0.8, 0.0, 1.0, 0.05)
        self.top_k = add_int("top_k", self.param_set.top_k or 20, 1, 100, 1)
        self.do_sample = add_bool("do_sample", self.param_set.do_sample if self.param_set.do_sample is not None else True)
        self.max_new_tokens = add_int("max_new_tokens", self.param_set.max_new_tokens or 512, 16, 4096, 8)
        self.min_new_tokens = add_int("min_new_tokens", self.param_set.min_new_tokens or 1, 0, 2048, 1)
        self.repetition_penalty = add_float("repetition_penalty", self.param_set.repetition_penalty or 1.0, 1.0, 2.0, 0.05)
        self.no_repeat_ngram_size = add_int("no_repeat_ngram_size", self.param_set.no_repeat_ngram_size or 0, 0, 10, 1)
        self.num_beams = add_int("num_beams", self.param_set.num_beams or 1, 1, 10, 1)
        self.length_penalty = add_float("length_penalty", self.param_set.length_penalty or 1.0, 0.5, 2.0, 0.05)
        self.diversity_penalty = add_float("diversity_penalty", self.param_set.diversity_penalty or 0.0, 0.0, 2.0, 0.1)
        self.early_stopping = add_bool("early_stopping", self.param_set.early_stopping if self.param_set.early_stopping is not None else False)

    def to_params(self) -> Dict[str, Any]:
        return {
            "preset": self.preset.currentData(),
            "temperature": self.temperature.value(),
            "top_p": self.top_p.value(),
            "top_k": int(self.top_k.value()),
            "do_sample": self.do_sample.isChecked(),
            "max_new_tokens": int(self.max_new_tokens.value()),
            "min_new_tokens": int(self.min_new_tokens.value()),
            "repetition_penalty": self.repetition_penalty.value(),
            "no_repeat_ngram_size": int(self.no_repeat_ngram_size.value()),
            "num_beams": int(self.num_beams.value()),
            "length_penalty": self.length_penalty.value(),
            "diversity_penalty": self.diversity_penalty.value(),
            "early_stopping": self.early_stopping.isChecked(),
        }


class ClassificationTuningWorker(QThread):
    progress = Signal(int, int, str)  # image_index, combo_index, message
    finished_one = Signal(int, int, dict)  # image_index, combo_index, result
    finished_all = Signal()
    error = Signal(str)

    def __init__(self, image_paths: List[Path], exec_env: Dict[str, Any], combos: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.exec_env = exec_env
        self.combos = combos
        self._stopping = False

    def stop(self):
        self._stopping = True

    def _run_vlm(self, user_query: str, image_path: Path, params: Dict[str, Any]) -> str:
        node_id = "1"
        vlm: VLMExecutor = self.exec_env["vlm"]
        thresholds: NodeThresholdManager = self.exec_env["thresholds"]
        set_thresholds(thresholds, node_id, {k: v for k, v in params.items() if v is not None})
        current_data = {KeyRegistry.USER_QUERY: user_query, KeyRegistry.IMAGE_PATH: str(image_path)}
        result = vlm.execute(current_data=current_data, node_id=node_id)
        if result.has_error:
            raise RuntimeError(result.data.get("error", "VLM error"))
        return result.data.get(KeyRegistry.VLM_ANSWER, "")

    def _parse_classification(self, text: str) -> Dict[str, Any]:
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                t = obj.get("type")
                c = obj.get("confidence", 0.0)
                r = obj.get("reason", "")
                return {"type": t, "confidence": c, "reason": r, "raw": text}
        except Exception:
            pass
        low = (text or "").lower()
        t = None
        for cand in list(DEFAULT_TYPE_MAP.keys()):
            if cand in low:
                t = cand
                break
        return {"type": t or "natural_image", "confidence": 0.3, "reason": (text or "")[:200], "raw": text}

    def run(self):
        try:
            for i, img_path in enumerate(self.image_paths):
                if self._stopping:
                    break
                for j, params in enumerate(self.combos):
                    if self._stopping:
                        break
                    try:
                        self.progress.emit(i, j, f"Classifying {img_path.name} (combo {j+1}) ...")
                        resp = self._run_vlm(CLASSIFIER_PROMPT, img_path, params)
                        parsed = self._parse_classification(resp)
                        self.finished_one.emit(i, j, parsed)
                    except Exception as e:
                        self.finished_one.emit(i, j, {"type": "error", "confidence": 0.0, "reason": f"{e}", "raw": ""})
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished_all.emit()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLM Caption Tester (Two-Stage)")
        self.resize(1200, 700)

        self.exec_env: Dict[str, Any] = {}
        self.type_map: Dict[str, Dict[str, Any]] = DEFAULT_TYPE_MAP.copy()
        
        self._build_ui()
        self._init_vlm()
        # Auto mode hooks
        self._auto_images: Optional[Path] = None
        self._auto_out: Optional[Path] = None
        self._auto_close: bool = False

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Tabs
        self.tabs = QTabWidget(self)
        root.addWidget(self.tabs, 1)

        # Main tab
        main_tab = QWidget(self)
        main_layout = QVBoxLayout(main_tab)

        # Folder controls
        top = QHBoxLayout()
        self.path_edit = QLineEdit(str((PROJECT_ROOT / "new_pdf_converter" / "images").resolve()))
        btn_browse = QPushButton("フォルダ選択")
        btn_browse.clicked.connect(self._choose_folder)
        btn_scan = QPushButton("スキャン")
        btn_scan.clicked.connect(self._scan_folder)
        btn_run = QPushButton("キャプション生成")
        btn_run.clicked.connect(self._run)
        btn_stop = QPushButton("停止")
        btn_stop.clicked.connect(self._stop)
        self.status_label = QLabel("")

        top.addWidget(QLabel("画像フォルダ:"))
        top.addWidget(self.path_edit, 1)
        top.addWidget(btn_browse)
        top.addWidget(btn_scan)
        top.addWidget(btn_run)
        top.addWidget(btn_stop)
        top.addWidget(self.status_label)
        main_layout.addLayout(top)

        # Parameters (classifier + per-type quick edit)
        param_bar = QHBoxLayout()
        self.classifier_panel = ParamPanel("分類(一段目)パラメータ", CLASSIFIER_PARAMS)
        param_bar.addWidget(self.classifier_panel)

        # Quick per-type preset overrides: only preset here to keep compact; detailed tuning in code
        self.combo_table = QComboBox(); self._fill_presets(self.combo_table, self.type_map["table"]["params"].preset)
        self.combo_plot = QComboBox(); self._fill_presets(self.combo_plot, self.type_map["plot_graph"]["params"].preset)
        self.combo_natural = QComboBox(); self._fill_presets(self.combo_natural, self.type_map["natural_image"]["params"].preset)
        self.combo_ocr = QComboBox(); self._fill_presets(self.combo_ocr, self.type_map["text_ocr"]["params"].preset)
        self.combo_formula = QComboBox(); self._fill_presets(self.combo_formula, self.type_map["formula"]["params"].preset)

        quick = QGroupBox("タイプ別プリセット(簡易)")
        quick_form = QFormLayout(quick)
        quick_form.addRow("table", self.combo_table)
        quick_form.addRow("plot_graph", self.combo_plot)
        quick_form.addRow("natural_image", self.combo_natural)
        quick_form.addRow("text_ocr", self.combo_ocr)
        quick_form.addRow("formula", self.combo_formula)
        param_bar.addWidget(quick)

        main_layout.addLayout(param_bar)

        # Table
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["画像", "ファイル名", "分類", "プリセット", "キャプション"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        main_layout.addWidget(self.table, 1)

        self.tabs.addTab(main_tab, "メイン")

        # Tuning tab (分類パラメータのチューニング)
        tune_tab = QWidget(self)
        tune_layout = QHBoxLayout(tune_tab)

        # Left: combo manager + editor
        left_panel = QVBoxLayout()
        add_bar = QHBoxLayout()
        self.tune_preset_add = QComboBox()
        for p in ["accurate", "balanced", "ocr", "qa", "code", "creative", "summary", "json"]:
            self.tune_preset_add.addItem(p, p)
        btn_add_preset = QPushButton("プリセットから追加")
        btn_add_default = QPushButton("デフォルト追加")
        add_bar.addWidget(self.tune_preset_add, 1)
        add_bar.addWidget(btn_add_preset)
        add_bar.addWidget(btn_add_default)
        left_panel.addLayout(add_bar)

        self.tune_list = QListWidget()
        left_panel.addWidget(self.tune_list, 1)

        edit_box = QGroupBox("選択中の組み合わせを編集")
        edit_layout = QVBoxLayout(edit_box)
        name_bar = QHBoxLayout()
        name_bar.addWidget(QLabel("名前:"))
        self.tune_name_edit = QLineEdit()
        name_bar.addWidget(self.tune_name_edit, 1)
        edit_layout.addLayout(name_bar)
        # Reuse ParamPanel for editing params
        # Start with a copy of CLASSIFIER_PARAMS
        self.tune_panel = ParamPanel("分類(一段目)パラメータ", CLASSIFIER_PARAMS)
        edit_layout.addWidget(self.tune_panel)
        btn_apply = QPushButton("更新")
        btn_remove = QPushButton("削除")
        apply_bar = QHBoxLayout()
        apply_bar.addWidget(btn_apply)
        apply_bar.addWidget(btn_remove)
        edit_layout.addLayout(apply_bar)
        left_panel.addWidget(edit_box)

        tune_layout.addLayout(left_panel, 1)

        # Right: results + controls
        right_panel = QVBoxLayout()
        ctrl_bar = QHBoxLayout()
        self.tune_status = QLabel("")
        btn_tune_start = QPushButton("スタート")
        btn_tune_stop = QPushButton("停止")
        ctrl_bar.addWidget(QLabel("メインの画像を使用"))
        ctrl_bar.addStretch(1)
        ctrl_bar.addWidget(btn_tune_start)
        ctrl_bar.addWidget(btn_tune_stop)
        ctrl_bar.addWidget(self.tune_status)
        right_panel.addLayout(ctrl_bar)

        self.tune_table = QTableWidget(0, 6, self)
        self.tune_table.setHorizontalHeaderLabels(["画像", "ファイル名", "コンボ", "type", "confidence", "reason"])
        self.tune_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tune_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tune_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tune_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tune_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tune_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tune_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_panel.addWidget(self.tune_table, 1)

        tune_layout.addLayout(right_panel, 2)

        self.tabs.addTab(tune_tab, "分類パラメータのチューニング")

        # State for tuning combos
        self.tune_combos: List[VLMParamSet] = []
        self.tune_combo_names: List[str] = []

        # Wire events
        btn_add_preset.clicked.connect(self._tune_add_combo_from_preset)
        btn_add_default.clicked.connect(self._tune_add_default_combo)
        btn_apply.clicked.connect(self._tune_apply_changes)
        btn_remove.clicked.connect(self._tune_remove_selected)
        self.tune_list.currentRowChanged.connect(self._tune_on_select)
        btn_tune_start.clicked.connect(self._tune_start)
        btn_tune_stop.clicked.connect(self._tune_stop)

        # Seed with one default
        self._tune_add_default_combo()


    def _fill_presets(self, combo: QComboBox, current: Optional[str]):
        combo.addItem("(none)", None)
        for p in ["accurate", "balanced", "ocr", "qa", "code", "creative", "summary", "json"]:
            combo.addItem(p, p)
        # select
        if current:
            idx = combo.findData(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)

    def _choose_folder(self):
        d = QFileDialog.getExistingDirectory(self, "画像フォルダを選択")
        if d:
            self.path_edit.setText(d)
            self._scan_folder()

    def _scan_folder(self):
        folder = Path(self.path_edit.text())
        if not folder.exists() or not folder.is_dir():
            self.status_label.setText("フォルダが無効です")
            return
        exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
        files = [p for p in folder.iterdir() if p.suffix.lower() in exts]
        self._populate_table(files)
        self.status_label.setText(f"{len(files)}件の画像")

    def _populate_table(self, image_paths: List[Path]):
        self.image_paths = image_paths
        self.table.setRowCount(len(image_paths))
        for i, p in enumerate(image_paths):
            pix = to_pixmap(p)
            img_label = QLabel()
            img_label.setPixmap(pix)
            self.table.setCellWidget(i, 0, img_label)
            self.table.setItem(i, 1, QTableWidgetItem(p.name))
            self.table.setItem(i, 2, QTableWidgetItem("-"))
            self.table.setItem(i, 3, QTableWidgetItem("-"))
            self.table.setItem(i, 4, QTableWidgetItem(""))

    def _init_vlm(self):
        # Build managers
        config = build_default_config()
        log_manager = LogManager(config)
        thresholds = NodeThresholdManager(config)

        model_path = str((PROJECT_ROOT / "vlm" / "SAIL-VL2-2B").resolve())
        self.model_manager = ModelManager(model_path=model_path)
        ok = self.model_manager.setup_model(progress_callback=lambda s: self.status_label.setText(s))
        if not ok:
            self.status_label.setText("モデル初期化失敗")

        vlm = VLMExecutor(log_manager, thresholds, model_manager=self.model_manager)
        vlm.set_model_manager(self.model_manager)
        vlm.set_node_config({}, node_id="1")

        # Save in env
        self.exec_env = {
            "vlm": vlm,
            "thresholds": thresholds,
        }

    def _apply_quick_presets(self):
        # Update type_map presets from quick selectors
        m = self.type_map
        def upd(key: str, combo: QComboBox):
            data = combo.currentData()
            if data is not None:
                m[key]["params"].preset = data
        upd("table", self.combo_table)
        upd("plot_graph", self.combo_plot)
        upd("natural_image", self.combo_natural)
        upd("text_ocr", self.combo_ocr)
        upd("formula", self.combo_formula)

        # Update classifier params from panel
        cls_params = self.classifier_panel.to_params()
        for k, v in cls_params.items():
            setattr(CLASSIFIER_PARAMS, k, v)

    

    def _run(self):
        if not hasattr(self, "image_paths") or not self.image_paths:
            self._scan_folder()
            if not getattr(self, "image_paths", []):
                return
        self._apply_quick_presets()
        self.status_label.setText("実行中...")

        self.worker = CaptionWorker(self.image_paths, self.exec_env, self.type_map, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished_one.connect(self._on_finished_one)
        self.worker.finished_all.connect(self._on_finished_all)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _stop(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
            self.status_label.setText("停止要求中...")

    def _on_progress(self, row: int, msg: str):
        self.status_label.setText(msg)

    def _on_finished_one(self, row: int, info: Dict[str, Any]):
        if row < 0 or row >= self.table.rowCount():
            return
        self.table.setItem(row, 2, QTableWidgetItem(info.get("type", "-")))
        self.table.setItem(row, 3, QTableWidgetItem(str(info.get("params", {}).get("preset"))))
        self.table.setItem(row, 4, QTableWidgetItem(info.get("caption", "")))

    def _on_finished_all(self):
        self.status_label.setText("完了")
        # Auto export if requested
        try:
            if self._auto_out:
                out_dir = Path(self._auto_out)
                out_dir.mkdir(parents=True, exist_ok=True)
                csv_path = out_dir / "captions.csv"
                import csv
                with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f)
                    w.writerow(["file", "path", "type", "preset", "caption"])
                    total = self.table.rowCount()
                    for i in range(total):
                        file_name = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
                        img_path = str(self.image_paths[i].resolve()) if hasattr(self, 'image_paths') and i < len(self.image_paths) else ""
                        ctype = self.table.item(i, 2).text() if self.table.item(i, 2) else ""
                        preset = self.table.item(i, 3).text() if self.table.item(i, 3) else ""
                        caption = self.table.item(i, 4).text() if self.table.item(i, 4) else ""
                        w.writerow([file_name, img_path, ctype, preset, caption])
        except Exception as e:
            self.status_label.setText(f"CSV保存エラー: {e}")
        finally:
            if self._auto_close:
                QTimer.singleShot(600, self.close)

    def _on_error(self, msg: str):
        self.status_label.setText(f"エラー: {msg}")

    # --- Tuning tab handlers ---
    def _tune_refresh_list(self):
        self.tune_list.clear()
        for name in self.tune_combo_names:
            self.tune_list.addItem(QListWidgetItem(name))

    def _tune_add_default_combo(self):
        base = CLASSIFIER_PARAMS.to_clean_dict()
        combo = VLMParamSet(**base)
        name = f"combo{len(self.tune_combos)+1}"
        self.tune_combos.append(combo)
        self.tune_combo_names.append(name)
        self._tune_refresh_list()
        self.tune_list.setCurrentRow(len(self.tune_combos)-1)

    def _tune_add_combo_from_preset(self):
        preset = self.tune_preset_add.currentData()
        base = CLASSIFIER_PARAMS.to_clean_dict()
        base["preset"] = preset
        combo = VLMParamSet(**base)
        name = f"{preset or 'none'}_{len(self.tune_combos)+1}"
        self.tune_combos.append(combo)
        self.tune_combo_names.append(name)
        self._tune_refresh_list()
        self.tune_list.setCurrentRow(len(self.tune_combos)-1)

    def _tune_on_select(self, row: int):
        if row < 0 or row >= len(self.tune_combos):
            self.tune_name_edit.setText("")
            return
        cmb = self.tune_combos[row]
        self.tune_name_edit.setText(self.tune_combo_names[row])
        # Populate editor with current values
        params = cmb.to_clean_dict()
        # Update preset combobox
        idx = self.tune_panel.preset.findData(params.get("preset"))
        if idx >= 0:
            self.tune_panel.preset.setCurrentIndex(idx)
        # Set numeric/boolean fields with fallbacks
        def _set_if(widget, key, default):
            val = params.get(key, default)
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(val))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(val))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(val))
        _set_if(self.tune_panel.temperature, "temperature", 0.7)
        _set_if(self.tune_panel.top_p, "top_p", 0.8)
        _set_if(self.tune_panel.top_k, "top_k", 20)
        _set_if(self.tune_panel.do_sample, "do_sample", False)
        _set_if(self.tune_panel.max_new_tokens, "max_new_tokens", 96)
        _set_if(self.tune_panel.min_new_tokens, "min_new_tokens", 16)
        _set_if(self.tune_panel.repetition_penalty, "repetition_penalty", 1.02)
        _set_if(self.tune_panel.no_repeat_ngram_size, "no_repeat_ngram_size", 3)
        _set_if(self.tune_panel.num_beams, "num_beams", 1)
        _set_if(self.tune_panel.length_penalty, "length_penalty", 1.0)
        _set_if(self.tune_panel.diversity_penalty, "diversity_penalty", 0.0)
        _set_if(self.tune_panel.early_stopping, "early_stopping", False)

    def _tune_apply_changes(self):
        row = self.tune_list.currentRow()
        if row < 0 or row >= len(self.tune_combos):
            return
        self.tune_combo_names[row] = self.tune_name_edit.text() or self.tune_combo_names[row]
        params = self.tune_panel.to_params()
        self.tune_combos[row] = VLMParamSet(**params)
        self._tune_refresh_list()
        self.tune_list.setCurrentRow(row)

    def _tune_remove_selected(self):
        row = self.tune_list.currentRow()
        if row < 0 or row >= len(self.tune_combos):
            return
        del self.tune_combos[row]
        del self.tune_combo_names[row]
        self._tune_refresh_list()
        if self.tune_combos:
            self.tune_list.setCurrentRow(min(row, len(self.tune_combos)-1))

    def _tune_start(self):
        if not hasattr(self, "image_paths") or not self.image_paths:
            self._scan_folder()
            if not getattr(self, "image_paths", []):
                self.tune_status.setText("画像がありません")
                return
        if not self.tune_combos:
            self.tune_status.setText("組み合わせがありません")
            return
        # Clear results
        self.tune_table.setRowCount(0)
        # Build combos dict list
        combos = [c.to_clean_dict() for c in self.tune_combos]
        self.tune_status.setText("実行中...")
        self.tune_worker = ClassificationTuningWorker(self.image_paths, self.exec_env, combos, self)
        self.tune_worker.progress.connect(self._tune_on_progress)
        self.tune_worker.finished_one.connect(self._tune_on_finished_one)
        self.tune_worker.finished_all.connect(self._tune_on_finished_all)
        self.tune_worker.error.connect(self._tune_on_error)
        self.tune_worker.start()

    def _tune_stop(self):
        if hasattr(self, "tune_worker") and self.tune_worker.isRunning():
            self.tune_worker.stop()
            self.tune_status.setText("停止要求中...")

    def _tune_on_progress(self, img_idx: int, combo_idx: int, msg: str):
        self.tune_status.setText(msg)

    def _tune_on_finished_one(self, img_idx: int, combo_idx: int, info: Dict[str, Any]):
        # Append a row
        row = self.tune_table.rowCount()
        self.tune_table.insertRow(row)
        if hasattr(self, "image_paths") and 0 <= img_idx < len(self.image_paths):
            pix = to_pixmap(self.image_paths[img_idx])
            img_label = QLabel()
            img_label.setPixmap(pix)
            self.tune_table.setCellWidget(row, 0, img_label)
            self.tune_table.setItem(row, 1, QTableWidgetItem(self.image_paths[img_idx].name))
        else:
            self.tune_table.setItem(row, 0, QTableWidgetItem(""))
            self.tune_table.setItem(row, 1, QTableWidgetItem(""))
        combo_name = self.tune_combo_names[combo_idx] if 0 <= combo_idx < len(self.tune_combo_names) else f"#{combo_idx+1}"
        self.tune_table.setItem(row, 2, QTableWidgetItem(combo_name))
        self.tune_table.setItem(row, 3, QTableWidgetItem(str(info.get("type", "-"))))
        self.tune_table.setItem(row, 4, QTableWidgetItem(str(info.get("confidence", ""))))
        self.tune_table.setItem(row, 5, QTableWidgetItem(str(info.get("reason", ""))))

    def _tune_on_finished_all(self):
        self.tune_status.setText("完了")

    def _tune_on_error(self, msg: str):
        self.tune_status.setText(f"エラー: {msg}")

    


def main():
    import argparse
    app = QApplication(sys.argv)
    mw = MainWindow()

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--images", type=str)
    parser.add_argument("--out", type=str)
    parser.add_argument("--close-on-finish", action="store_true")
    # Ignore unknown args to keep standard launching unaffected
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        args = argparse.Namespace(auto=False, images=None, out=None, close_on_finish=False)

    # Setup auto mode if requested
    if getattr(args, 'auto', False):
        if getattr(args, 'images', None):
            mw._auto_images = Path(args.images)
            mw.path_edit.setText(str(mw._auto_images))
        if getattr(args, 'out', None):
            mw._auto_out = Path(args.out)
        mw._auto_close = bool(getattr(args, 'close_on_finish', False))
        # Defer actions until UI is shown
        def _kickoff():
            mw._scan_folder()
            QTimer.singleShot(500, mw._run)
        QTimer.singleShot(400, _kickoff)

    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())

