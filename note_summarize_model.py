# note_summarize_model.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch, threading

_MODEL_ID = "EbanLee/kobart-summary-v3"

_TOK = None
_MOD = None
_LOCK = threading.Lock()

def _ensure_loaded():
    global _TOK, _MOD
    if _MOD is not None:
        return
    with _LOCK:
        if _MOD is not None:
            return
        _TOK = AutoTokenizer.from_pretrained(_MODEL_ID)
        _MOD = AutoModelForSeq2SeqLM.from_pretrained(_MODEL_ID)
        _MOD.eval()

def summarize_text(text: str, max_char: int = 300) -> str:
    if not text or not text.strip():
        return ""
    _ensure_loaded()

    inputs = _TOK([text], max_length=1024, truncation=True, return_tensors="pt")
    with torch.inference_mode():
        output = _MOD.generate(
            **inputs,
            num_beams=4,
            do_sample=False,
            min_length=0,
            max_length=160,
            length_penalty=1.0,
            no_repeat_ngram_size=3
        )
    decoded = _TOK.batch_decode(output, skip_special_tokens=True)[0].strip()
    return decoded[:max_char]
