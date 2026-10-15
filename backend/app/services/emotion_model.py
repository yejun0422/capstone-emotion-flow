"""
KcELECTRA 기반 한국어 감정 분석 모델 로더.

"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


EXPECTED_EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]


class MultiTaskKcELECTRA(nn.Module):
    """학습 시 사용한 대분류/소분류 멀티태스크 모델 구조."""

    def __init__(
        self,
        model_name: str,
        num_major_labels: int,
        num_minor_labels: int,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.major_classifier = nn.Linear(hidden_size, num_major_labels)
        self.minor_classifier = nn.Linear(hidden_size, num_minor_labels)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        pooled_output = outputs.last_hidden_state[:, 0, :]
        pooled_output = self.dropout(pooled_output)
        major_logits = self.major_classifier(pooled_output)
        minor_logits = self.minor_classifier(pooled_output)
        return major_logits, minor_logits


def _default_model_dir() -> Path:
    """프로젝트 루트/model 또는 환경 변수로 지정한 모델 디렉터리를 반환."""
    configured = os.getenv("EMOTION_MODEL_DIR")
    if configured:
        return Path(configured).expanduser().resolve()

    # 파일이 backend/app/services/emotion_model.py에 있을 때:
    # parents[0]=services, [1]=app, [2]=backend, [3]=project root
    file_path = Path(__file__).resolve()
    try:
        project_root = file_path.parents[3]
        candidate = project_root / "model"
        if candidate.exists():
            return candidate
    except IndexError:
        pass

    # 개발/테스트 시 파일이 프로젝트 루트 근처에 놓인 경우의 대안
    for parent in file_path.parents:
        candidate = parent / "model"
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "모델 디렉터리를 찾지 못했습니다. 프로젝트 루트에 model/ 폴더를 두거나 "
        "EMOTION_MODEL_DIR 환경 변수로 해당 경로를 지정하세요."
    )


class EmotionClassifier:
    """모델을 한 번 로드하고 문장별 대분류/소분류 점수를 반환한다."""

    def __init__(
        self,
        model_dir: str | Path | None = None,
        device: str | torch.device | None = None,
        batch_size: int = 16,
    ) -> None:
        self.model_dir = Path(model_dir).expanduser().resolve() if model_dir else _default_model_dir()
        self.weights_path = self.model_dir / "final_kcelectra_multitask.pt"
        self.config_path = self.model_dir / "final_kcelectra_multitask_config.json"
        self.tokenizer_dir = self.model_dir / "final_kcelectra_multitask_tokenizer"
        self.batch_size = max(1, int(batch_size))

        for required_path in (self.weights_path, self.config_path, self.tokenizer_dir):
            if not required_path.exists():
                raise FileNotFoundError(f"필요한 모델 파일/폴더가 없습니다: {required_path}")

        with self.config_path.open("r", encoding="utf-8") as f:
            self.config: dict[str, Any] = json.load(f)

        required_keys = {
            "model_name",
            "num_major_labels",
            "num_minor_labels",
            "max_length",
            "major_id2label",
            "minor_id2label",
        }
        missing = required_keys - self.config.keys()
        if missing:
            raise ValueError(f"모델 설정 파일에 필요한 키가 없습니다: {sorted(missing)}")

        self.model_name = self.config["model_name"]
        self.max_length = int(self.config["max_length"])
        self.major_id2label = {
            int(k): str(v) for k, v in self.config["major_id2label"].items()
        }
        self.minor_id2label = {
            int(k): str(v) for k, v in self.config["minor_id2label"].items()
        }

        if len(self.major_id2label) != int(self.config["num_major_labels"]):
            raise ValueError("대분류 라벨 개수와 설정 파일의 num_major_labels가 일치하지 않습니다.")
        if len(self.minor_id2label) != int(self.config["num_minor_labels"]):
            raise ValueError("소분류 라벨 개수와 설정 파일의 num_minor_labels가 일치하지 않습니다.")

        missing_emotions = set(EXPECTED_EMOTIONS) - set(self.major_id2label.values())
        if missing_emotions:
            raise ValueError(
                "모델 설정의 대분류 라벨에 프로젝트 필수 감정이 없습니다: "
                f"{sorted(missing_emotions)}"
            )

        self.device = torch.device(
            device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu")
        )
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.tokenizer_dir))

        self.model = MultiTaskKcELECTRA(
            model_name=self.model_name,
            num_major_labels=int(self.config["num_major_labels"]),
            num_minor_labels=int(self.config["num_minor_labels"]),
        )
        state_dict = torch.load(self.weights_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def predict_many(self, texts: Sequence[str]) -> list[dict[str, Any]]:
        """
        문장 목록을 각각 독립적으로 분석한다.
        입력 순서와 출력 순서는 동일하며, 빈 문자열은 ValueError를 발생시킨다.
        """
        if isinstance(texts, (str, bytes)):
            raise TypeError("texts에는 문자열 하나가 아니라 문자열 목록을 전달하세요.")

        cleaned_texts: list[str] = []
        for index, text in enumerate(texts):
            if text is None:
                raise ValueError(f"texts[{index}]가 None입니다.")
            cleaned = str(text).strip()
            if not cleaned:
                raise ValueError(f"texts[{index}]가 빈 문자열입니다.")
            cleaned_texts.append(cleaned)

        if not cleaned_texts:
            return []

        results: list[dict[str, Any]] = []
        for start in range(0, len(cleaned_texts), self.batch_size):
            batch_texts = cleaned_texts[start : start + self.batch_size]
            encoded = self.tokenizer(
                batch_texts,
                truncation=True,
                max_length=self.max_length,
                padding=True,
                return_tensors="pt",
            )
            input_ids = encoded["input_ids"].to(self.device)
            attention_mask = encoded["attention_mask"].to(self.device)

            major_logits, minor_logits = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            major_probs_batch = torch.softmax(major_logits, dim=-1).cpu()
            minor_probs_batch = torch.softmax(minor_logits, dim=-1).cpu()

            for text, major_probs, minor_probs in zip(
                batch_texts, major_probs_batch, minor_probs_batch
            ):
                major_scores = {
                    self.major_id2label[i]: float(major_probs[i].item())
                    for i in range(len(major_probs))
                }
                # 파이프라인/시각화에서 기대하는 6개 감정 이름과 순서를 보장한다.
                major_scores = {emotion: major_scores[emotion] for emotion in EXPECTED_EMOTIONS}

                major_top_idx = int(torch.argmax(major_probs).item())
                minor_top_idx = int(torch.argmax(minor_probs).item())
                major_top_k = sorted(
                    (
                        {"emotion": label, "probability": float(major_probs[idx].item())}
                        for idx, label in self.major_id2label.items()
                    ),
                    key=lambda item: item["probability"],
                    reverse=True,
                )[: min(3, len(self.major_id2label))]
                minor_top_k = sorted(
                    (
                        {"emotion": label, "probability": float(minor_probs[idx].item())}
                        for idx, label in self.minor_id2label.items()
                    ),
                    key=lambda item: item["probability"],
                    reverse=True,
                )[: min(3, len(self.minor_id2label))]

                results.append(
                    {
                        "text": text,
                        "major_emotion": self.major_id2label[major_top_idx],
                        "major_probability": float(major_probs[major_top_idx].item()),
                        "major_scores": major_scores,
                        "minor_emotion": self.minor_id2label[minor_top_idx],
                        "minor_probability": float(minor_probs[minor_top_idx].item()),
                        "major_top_k": major_top_k,
                        "minor_top_k": minor_top_k,
                    }
                )

        return results

    def predict(self, text: str) -> dict[str, Any]:
        """단일 문장 분석 편의 함수."""
        return self.predict_many([text])[0]


if __name__ == "__main__":
    # 프로젝트 루트/model/에 학습 산출물이 있으면 바로 실행해 볼 수 있다.
    classifier = EmotionClassifier()
    samples = [
        "오늘 발표를 망쳐서 정말 속상했어요.",
        "친구가 도와줘서 마음이 한결 편해졌어요.",
    ]
    for item in classifier.predict_many(samples):
        print(f"\n입력: {item['text']}")
        print(f"대표 감정: {item['major_emotion']} ({item['major_probability']:.4f})")
        print("6개 감정 점수:")
        for emotion, score in item["major_scores"].items():
            print(f"  {emotion}: {score:.4f}")
