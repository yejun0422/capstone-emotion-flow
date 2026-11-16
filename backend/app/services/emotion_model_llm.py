"""
LLM backbone(LoRA) + 멀티태스크 분류 헤드 기반 한국어 감정 분석 모델 로더 (EXAONE-4.0-1.2B).
기존 emotion_model.EmotionClassifier와 같은 predict()/predict_many() 반환 구조를 제공한다.

사용 예:
    from app.services.emotion_model_llm import EmotionClassifier as LLMEmotionClassifier
    clf = LLMEmotionClassifier(model_dir="<프로젝트 루트>/model/llm_exaone")
    clf.predict_many(["문장1", "문장2"])

주의: 기반 모델(LGAI-EXAONE/EXAONE-4.0-1.2B, 약 2.5GB)은 이 저장소에 포함되지 않고 첫 로드 때 Hugging Face에서 내려받는다.
EXAONE은 비상업 라이선스(EXAONE AI Model License 1.2-NC)이므로 비상업 목적에서만 사용할 수 있다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from peft import LoraConfig, inject_adapter_in_model


EXPECTED_EMOTIONS = ["불안", "분노", "상처", "슬픔", "당황", "기쁨"]


class MultiTaskLLMClassifier(nn.Module):
    """학습 시 사용한 구조: 공유 backbone + 대분류/소분류 헤드, 마지막 유효 토큰 풀링."""

    def __init__(self, backbone, hidden_size, n_major, n_minor, dropout=0.1):
        super().__init__()
        self.backbone = backbone
        self.dropout = nn.Dropout(dropout)
        self.major_head = nn.Linear(hidden_size, n_major)
        self.minor_head = nn.Linear(hidden_size, n_minor)

    def forward(self, input_ids, attention_mask):
        h = self.backbone(input_ids=input_ids, attention_mask=attention_mask, use_cache=False).last_hidden_state
        idx = attention_mask.sum(1) - 1
        pooled = h[torch.arange(h.size(0), device=h.device), idx]
        with torch.autocast(device_type="cuda", enabled=False):
            pooled = self.dropout(pooled.float())
            return self.major_head(pooled), self.minor_head(pooled)


def format_result(text, major_probs, minor_probs, major_id2label, minor_id2label):
    """확률 리스트 → emotion_model.EmotionClassifier와 같은 구조의 dict (순수 파이썬)."""
    major_scores = {major_id2label[i]: float(major_probs[i]) for i in range(len(major_probs))}
    major_scores = {emotion: major_scores[emotion] for emotion in EXPECTED_EMOTIONS}
    major_top_idx = max(range(len(major_probs)), key=lambda i: major_probs[i])
    minor_top_idx = max(range(len(minor_probs)), key=lambda i: minor_probs[i])
    major_top_k = sorted(
        ({"emotion": major_id2label[i], "probability": float(major_probs[i])} for i in range(len(major_probs))),
        key=lambda item: item["probability"],
        reverse=True,
    )[: min(3, len(major_id2label))]
    minor_top_k = sorted(
        ({"emotion": minor_id2label[i], "probability": float(minor_probs[i])} for i in range(len(minor_probs))),
        key=lambda item: item["probability"],
        reverse=True,
    )[: min(3, len(minor_id2label))]
    return {
        "text": text,
        "major_emotion": major_id2label[major_top_idx],
        "major_probability": float(major_probs[major_top_idx]),
        "major_scores": major_scores,
        "minor_emotion": minor_id2label[minor_top_idx],
        "minor_probability": float(minor_probs[minor_top_idx]),
        "major_top_k": major_top_k,
        "minor_top_k": minor_top_k,
    }


def _default_model_dir() -> Path:
    configured = os.getenv("EMOTION_MODEL_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    here = Path(__file__).resolve().parent
    if (here / "config.json").exists():
        return here
    for parent in Path(__file__).resolve().parents:
        for candidate in (parent / "model" / "llm_exaone", parent / "model"):
            if (candidate / "config.json").exists() and (candidate / "adapter").is_dir():
                return candidate
    raise FileNotFoundError(
        "LLM 모델 디렉터리를 찾지 못했습니다. 프로젝트 루트의 model/llm_exaone/ (config.json, adapter/, tokenizer/ 포함)에 "
        "파일을 두거나, EmotionClassifier(model_dir=...) 또는 EMOTION_MODEL_DIR 환경 변수로 경로를 지정하세요."
    )


def _from_pretrained_dtype(cls, model_id, dtype, **kw):
    try:
        return cls.from_pretrained(model_id, dtype=dtype, **kw)
    except TypeError:
        return cls.from_pretrained(model_id, torch_dtype=dtype, **kw)


class EmotionClassifier:
    """모델을 한 번 로드하고 문장별 대분류/소분류 확률을 반환한다 (기존 인터페이스와 동일)."""

    def __init__(self, model_dir=None, device=None, batch_size: int = 16, base_model_path=None) -> None:
        self.model_dir = Path(model_dir).expanduser().resolve() if model_dir else _default_model_dir()
        self.config_path = self.model_dir / "config.json"
        self.weights_path = self.model_dir / "adapter" / "lora_and_heads.pt"
        self.lora_config_path = self.model_dir / "adapter" / "lora_config.json"
        self.tokenizer_dir = self.model_dir / "tokenizer"
        self.batch_size = max(1, int(batch_size))

        for required_path in (self.config_path, self.weights_path, self.lora_config_path, self.tokenizer_dir):
            if not required_path.exists():
                raise FileNotFoundError(f"필요한 모델 파일/폴더가 없습니다: {required_path}")

        with self.config_path.open("r", encoding="utf-8") as f:
            self.config: dict[str, Any] = json.load(f)
        required_keys = {"model_name", "num_major_labels", "num_minor_labels", "max_length",
                         "major_id2label", "minor_id2label", "hidden_size", "dropout"}
        missing = required_keys - self.config.keys()
        if missing:
            raise ValueError(f"모델 설정 파일에 필요한 키가 없습니다: {sorted(missing)}")

        self.model_name = self.config["model_name"]
        self.max_length = int(self.config["max_length"])
        self.major_id2label = {int(k): str(v) for k, v in self.config["major_id2label"].items()}
        self.minor_id2label = {int(k): str(v) for k, v in self.config["minor_id2label"].items()}
        if len(self.major_id2label) != int(self.config["num_major_labels"]):
            raise ValueError("대분류 라벨 개수와 설정 파일의 num_major_labels가 일치하지 않습니다.")
        if len(self.minor_id2label) != int(self.config["num_minor_labels"]):
            raise ValueError("소분류 라벨 개수와 설정 파일의 num_minor_labels가 일치하지 않습니다.")
        missing_emotions = set(EXPECTED_EMOTIONS) - set(self.major_id2label.values())
        if missing_emotions:
            raise ValueError(f"모델 설정의 대분류 라벨에 프로젝트 필수 감정이 없습니다: {sorted(missing_emotions)}")

        self.device = torch.device(device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu"))
        use_cuda = self.device.type == "cuda"
        self.use_amp = use_cuda and self.config.get("load_dtype", "float16") == "float16"
        dtype = torch.float16 if self.use_amp else torch.float32          # CPU는 fp32
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.tokenizer_dir))
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        source = str(base_model_path) if base_model_path else self.model_name
        backbone = None
        for attn in ("sdpa", "eager"):
            try:
                backbone = _from_pretrained_dtype(AutoModel, source, dtype, attn_implementation=attn,
                                                  trust_remote_code=False, low_cpu_mem_usage=True)
                break
            except Exception as e:  # noqa: BLE001
                if attn == "eager" or "attn" not in str(e).lower():
                    raise
        for p in backbone.parameters():
            p.requires_grad_(False)
        with self.lora_config_path.open("r", encoding="utf-8") as f:
            lcfg = LoraConfig(**json.load(f))
        backbone = inject_adapter_in_model(lcfg, backbone)
        self.model = MultiTaskLLMClassifier(
            backbone, int(self.config["hidden_size"]), int(self.config["num_major_labels"]),
            int(self.config["num_minor_labels"]), float(self.config["dropout"]),
        )
        for name, p in self.model.named_parameters():
            if "lora_" in name or name.startswith(("major_head", "minor_head")):
                p.data = p.data.float()
        state = torch.load(self.weights_path, map_location="cpu")
        own = self.model.state_dict()
        expected = [n for n in own if "lora_" in n or n.startswith(("major_head", "minor_head"))]
        absent = [n for n in expected if n not in state]
        unknown = [n for n in state if n not in own]
        if absent or unknown:
            raise ValueError(f"가중치 키 불일치: 파일에 없음 {absent[:3]}..., 모델에 없음 {unknown[:3]}...")
        with torch.no_grad():
            params = dict(self.model.named_parameters())
            for n, v in state.items():
                params[n].copy_(v.to(params[n].device, params[n].dtype))
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

        eos_id = self.tokenizer.eos_token_id
        pad_id = self.tokenizer.pad_token_id
        results: list[dict[str, Any]] = []
        for start in range(0, len(cleaned_texts), self.batch_size):
            batch_texts = cleaned_texts[start : start + self.batch_size]
            seqs = []
            for t in batch_texts:
                ids = self.tokenizer(t, add_special_tokens=False)["input_ids"][: self.max_length]
                seqs.append(ids + [eos_id])                      # 학습과 동일: 텍스트 토큰 + eos
            width = max(len(s) for s in seqs)
            input_ids = torch.tensor([s + [pad_id] * (width - len(s)) for s in seqs], device=self.device)
            attention_mask = torch.tensor([[1] * len(s) + [0] * (width - len(s)) for s in seqs], device=self.device)
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=self.use_amp):
                major_logits, minor_logits = self.model(input_ids, attention_mask)
            major_probs_batch = torch.softmax(major_logits.float(), dim=-1).cpu().tolist()
            minor_probs_batch = torch.softmax(minor_logits.float(), dim=-1).cpu().tolist()
            for text, mp, np_ in zip(batch_texts, major_probs_batch, minor_probs_batch):
                results.append(format_result(text, mp, np_, self.major_id2label, self.minor_id2label))
        return results

    def predict(self, text: str) -> dict[str, Any]:
        """단일 문장 분석 편의 함수."""
        return self.predict_many([text])[0]


if __name__ == "__main__":
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
