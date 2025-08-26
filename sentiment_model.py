# sentiment_model.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch, torch.nn.functional as F

MODEL_ID = "clapAI/roberta-base-multilingual-sentiment"
tok = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
model.eval()

@torch.inference_mode()
def classify_sentiment(text: str) -> float:
    if not text or not text.strip():
        return 0.0                      # 🔁 항상 float
    inputs = tok([text], return_tensors="pt", truncation=True, max_length=512)
    logits = model(**inputs).logits
    probs = F.softmax(logits, dim=-1)[0]
    pred_id = int(torch.argmax(probs).item())
    score = float(probs[pred_id].item())
    return score
