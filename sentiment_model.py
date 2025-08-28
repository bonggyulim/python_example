# sentiment_model.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig
import torch, torch.nn.functional as F
import threading, traceback

MODEL_ID = "nlptown/bert-base-multilingual-uncased-sentiment"

_tok = None
_model = None
_cfg = None
_lock = threading.Lock()

def _ensure_loaded():
    global _tok, _model, _cfg
    if _model is not None:
        return
    with _lock:
        if _model is not None:
            return
        try:
            print("[sent] loading tokenizer…")
            _tok = AutoTokenizer.from_pretrained(MODEL_ID)  # BertTokenizer, sentencepiece 아님

            print("[sent] loading config…")
            _cfg = AutoConfig.from_pretrained(MODEL_ID)
            # 이 모델은 5라벨(1~5 stars). id2label/num_labels를 강제 동기화.
            _cfg.id2label = {0:"1 star", 1:"2 stars", 2:"3 stars", 3:"4 stars", 4:"5 stars"}
            _cfg.label2id = {v:k for k,v in _cfg.id2label.items()}
            _cfg.num_labels = 5

            print("[sent] loading model…")
            m = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, config=_cfg)
            m.eval()
            _model = m
            print("[sent] ready. num_labels:", _model.config.num_labels,
                  "id2label_len:", len(_model.config.id2label))
        except Exception as e:
            print("[sent] model load failed:", e)
            print(traceback.format_exc())
            _tok = None
            _model = None
            _cfg = None  # 서버는 계속 살려둠

@torch.inference_mode()
def classify_sentiment(text: str) -> float:
    if not text or not text.strip():
        return 0.0
    _ensure_loaded()
    if _model is None:
        return 0.0  # 안전 폴백
    inputs = _tok([text], return_tensors="pt", truncation=True, max_length=256)
    logits = _model(**inputs).logits
    probs = F.softmax(logits, dim=-1)[0]  # 5차원

    # 긍정(★4, ★5) 확률 합산
    pos = float(probs[3].item() + probs[4].item())
    return pos
