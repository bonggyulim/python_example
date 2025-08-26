# note_summarize_model.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

_MODEL_ID = "EbanLee/kobart-summary-v3"

_TOKENIZER = AutoTokenizer.from_pretrained(_MODEL_ID)
_MODEL = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_ID)
_MODEL.eval()  # 추론 모드

def summarize_text(text: str, max_char: int = 300) -> str:
    if not text or not text.strip():
        return ""

    # KoBART 요약은 보통 prefix 없이 사용
    inputs = _TOKENIZER([text], max_length=1024, truncation=True, return_tensors="pt")

    with torch.inference_mode():
        output = _MODEL.generate(
            **inputs,
            num_beams=4,
            do_sample=False,
            min_length=0,
            max_length=160,
            length_penalty=1.0,
            no_repeat_ngram_size=3
        )

    decoded = _TOKENIZER.batch_decode(output, skip_special_tokens=True)[0].strip()
    return decoded[:max_char]
