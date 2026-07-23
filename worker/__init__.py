"""V8 Lite pneumonia prediction worker package."""

from .model import (
    V8LitePredictor,
    load_prediction_model,
    predict_pneumonia,
)

__all__ = [
    "V8LitePredictor",
    "load_prediction_model",
    "predict_pneumonia",
]