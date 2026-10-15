from pathlib import Path
import json
import pickle

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "model.pkl"
EXPLAINER_PATH = ARTIFACTS_DIR / "explainer.pkl"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"
DISTRICTS_PATH = ARTIFACTS_DIR / "district_features.json"

_cached_model = None
_cached_explainer = None
_cached_metadata = None
_cached_districts = None


def load_model():
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH, "rb") as f:
                _cached_model = pickle.load(f)
                return _cached_model
        except Exception:
            return None
    return None


def load_explainer():
    global _cached_explainer
    if _cached_explainer is not None:
        return _cached_explainer
    if EXPLAINER_PATH.exists():
        try:
            with open(EXPLAINER_PATH, "rb") as f:
                _cached_explainer = pickle.load(f)
                return _cached_explainer
        except Exception:
            # mis. shap tak terpasang -> pemanggil pakai jalur fallback
            return None
    return None


def load_metadata():
    global _cached_metadata
    if _cached_metadata is not None:
        return _cached_metadata
    if METADATA_PATH.exists():
        _cached_metadata = json.loads(
            METADATA_PATH.read_text(encoding="utf-8"))
        return _cached_metadata
    return None


def load_district_features():
    global _cached_districts
    if _cached_districts is not None:
        return _cached_districts
    if DISTRICTS_PATH.exists():
        _cached_districts = json.loads(
            DISTRICTS_PATH.read_text(encoding="utf-8"))
        return _cached_districts
    return {}
