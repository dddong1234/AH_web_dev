"""Inference and Grad-CAM helper for the V8 Lite DenseNet121 model."""

from __future__ import annotations

import argparse
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
DEFAULT_WEIGHT_PATH = ROOT / "models" / "v8_lite_densenet121_fp16.pth"
UPLOAD_ROOT = PROJECT_ROOT / "uploads"

CLASS_NAMES = ("normal", "pneumonia")
MODEL_NAME = "v8-lite-densenet121-fp16"


def build_model() -> nn.Module:
    model = models.densenet121(weights=None)
    model.classifier = nn.Linear(model.classifier.in_features, 2)
    return model


class V8LitePredictor:
    """Load the V8 Lite model once and reuse it for prediction."""

    def __init__(self, weight_path: str | Path = DEFAULT_WEIGHT_PATH):
        self.weight_path = Path(weight_path)
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        self.model: nn.Module | None = None
        # Grad-CAM은 shared model에서 backward를 수행하므로 동시 실행을 막는다.
        self._lock = Lock()

    def load_model(self) -> None:
        if self.model is not None:
            return

        with self._lock:
            if self.model is not None:
                return

            if not self.weight_path.is_file():
                raise FileNotFoundError(
                    f"V8 Lite 가중치가 없습니다: {self.weight_path}"
                )

            checkpoint = torch.load(
                self.weight_path,
                map_location="cpu",
                weights_only=True,
            )
            if checkpoint.get("class_names") != list(CLASS_NAMES):
                raise ValueError(
                    "체크포인트 클래스 순서가 "
                    "normal(0), pneumonia(1)가 아닙니다."
                )

            model = build_model()
            if DEVICE.type == "cuda":
                model = model.half()
            model.load_state_dict(checkpoint["state_dict"], strict=True)
            self.model = model.to(DEVICE).eval()

    def predict_image(
        self,
        image_input: str | Path | Image.Image,
        *,
        record_id: int | None = None,
        generate_heatmap: bool = True,
    ) -> dict[str, Any]:
        self.load_model()
        image = self._open_image(image_input)
        tensor = self.transform(image).unsqueeze(0).to(DEVICE)
        if DEVICE.type == "cuda":
            tensor = tensor.half()

        # 같은 모델 객체에서 hook/backward 결과가 섞이지 않도록 직렬 실행한다.
        with self._lock:
            if generate_heatmap:
                if record_id is None or record_id < 1:
                    raise ValueError(
                        "Heatmap 생성 시 1 이상의 record_id가 필요합니다."
                    )
                probabilities, heatmap = self._predict_with_gradcam(tensor)
                heatmap_path, heatmap_url = self._save_heatmap(
                    image,
                    heatmap,
                    record_id=record_id,
                )
            else:
                probabilities = self._predict_without_gradcam(tensor)
                heatmap_path = None
                heatmap_url = None

        pred_label = int(torch.argmax(probabilities).item())
        confidence = float(probabilities[pred_label].item())

        return {
            "pred_label": pred_label,
            "pred_class": CLASS_NAMES[pred_label],
            "pneumonia": pred_label == 1,
            "confidence": confidence,
            "probability": probabilities.tolist(),
            "prob_class_0": float(probabilities[0].item()),
            "prob_class_1": float(probabilities[1].item()),
            # DB에는 uploads/를 제외한 상대경로를 저장한다.
            "heatmap_path": heatmap_path,
            "heatmap_url": heatmap_url,
            "ai_model": MODEL_NAME,
        }

    @staticmethod
    def _open_image(
        image_input: str | Path | Image.Image,
    ) -> Image.Image:
        if isinstance(image_input, (str, Path)):
            with Image.open(image_input) as opened:
                return opened.convert("RGB")
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        raise TypeError("image_input은 이미지 경로 또는 PIL.Image 객체여야 합니다.")

    def _predict_without_gradcam(self, tensor: torch.Tensor) -> torch.Tensor:
        assert self.model is not None
        with torch.inference_mode():
            logits = self.model(tensor)
            return torch.softmax(logits, dim=1)[0].float().cpu()

    def _predict_with_gradcam(
        self,
        tensor: torch.Tensor,
    ) -> tuple[torch.Tensor, np.ndarray]:
        assert self.model is not None

        activations: torch.Tensor | None = None
        gradients: torch.Tensor | None = None

        # DenseNet121의 마지막 Conv2d 계층
        target_layer = self.model.features.denseblock4.denselayer16.conv2

        def save_activation(
            _module: nn.Module,
            _inputs: tuple[torch.Tensor, ...],
            output: torch.Tensor,
        ) -> None:
            nonlocal activations, gradients
            activations = output

            def save_gradient(gradient: torch.Tensor) -> None:
                nonlocal gradients
                gradients = gradient

            output.register_hook(save_gradient)

        hook = target_layer.register_forward_hook(save_activation)
        try:
            self.model.zero_grad(set_to_none=True)
            with torch.enable_grad():
                logits = self.model(tensor)
                probabilities = torch.softmax(logits, dim=1)[0]
                pred_label = int(torch.argmax(probabilities).item())
                logits[0, pred_label].backward()
        finally:
            hook.remove()

        if activations is None or gradients is None:
            raise RuntimeError("Grad-CAM activation 또는 gradient를 얻지 못했습니다.")

        # 채널별 gradient 평균을 activation의 가중치로 사용한다.
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((weights * activations).sum(dim=1, keepdim=True))
        cam = F.interpolate(
            cam,
            size=(tensor.shape[2], tensor.shape[3]),
            mode="bilinear",
            align_corners=False,
        )[0, 0]

        cam_min = cam.min()
        cam_max = cam.max()
        cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)

        return (
            probabilities.detach().float().cpu(),
            cam.detach().float().cpu().numpy(),
        )

    @staticmethod
    def _jet_colormap(cam: np.ndarray) -> np.ndarray:
        """Convert a normalized 2-D map into an RGB JET-style heatmap."""

        values = np.clip(cam, 0.0, 1.0)
        four = 4.0 * values
        red = np.clip(np.minimum(four - 1.5, -four + 4.5), 0.0, 1.0)
        green = np.clip(np.minimum(four - 0.5, -four + 3.5), 0.0, 1.0)
        blue = np.clip(np.minimum(four + 0.5, -four + 2.5), 0.0, 1.0)
        return np.stack([red, green, blue], axis=-1)

    def _save_heatmap(
        self,
        image: Image.Image,
        cam: np.ndarray,
        *,
        record_id: int,
    ) -> tuple[str, str]:
        record_heatmap_root = UPLOAD_ROOT / "heatmaps" / str(record_id)
        record_heatmap_root.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4()}.png"
        output_path = record_heatmap_root / filename

        cam_image = Image.fromarray(
            np.uint8(self._jet_colormap(cam) * 255)
        ).resize(image.size, Image.Resampling.BILINEAR)
        overlay = Image.blend(image.convert("RGB"), cam_image, alpha=0.35)
        overlay.save(output_path, format="PNG")

        relative_path = f"heatmaps/{record_id}/{filename}"
        response_url = f"/uploads/{relative_path}"
        return relative_path, response_url


# 애플리케이션 전체에서 동일한 Predictor를 재사용한다.
predictor = V8LitePredictor()


def load_prediction_model() -> None:
    """Load the model once during FastAPI startup."""

    predictor.load_model()


def predict_pneumonia(
    image_path: str | Path,
    record_id: int,
) -> dict[str, Any]:
    """API Service에서 사용하는 폐렴 예측 공용 함수."""

    result = predictor.predict_image(
        image_path,
        record_id=record_id,
        generate_heatmap=True,
    )

    return {
        "is_pneumonia": result["pneumonia"],
        "confidence": result["confidence"],
        "heatmap_path": result["heatmap_path"],
        "heatmap_url": result["heatmap_url"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V8 Lite 폐렴 예측")
    parser.add_argument("--image", required=True, help="예측할 이미지 경로")
    parser.add_argument(
        "--record-id",
        type=int,
        help="Grad-CAM 저장 폴더에 사용할 진료기록 ID",
    )
    parser.add_argument(
        "--no-heatmap",
        action="store_true",
        help="Grad-CAM 이미지를 생성하지 않음",
    )
    args = parser.parse_args()

    load_prediction_model()
    print(
        predict_pneumonia(
            args.image,
            record_id=args.record_id,
            generate_heatmap=not args.no_heatmap,
        )
    )