import joblib
import numpy as np
from scipy.sparse import hstack, csr_matrix

model      = joblib.load("./models/task_priority/model.pkl")
vectorizer = joblib.load("./models/task_priority/vectorizer.pkl")

# Must match the urgency keywords used during training
URGENCY_WORDS = [
    "asap", "urgent", "urgently", "now", "right now", "immediately",
    "emergency", "critical", "deadline", "overdue", "rush", "today",
    "tonight", "this morning", "before", "expire", "expires", "expiring",
    "summons", "court", "police", "911", "ambulance", "chest pain",
    "by midnight", "right away", "at once"
]

def _urgency_score(text: str) -> float:
    text_lower = text.lower()
    return float(any(kw in text_lower for kw in URGENCY_WORDS))

def predict_priority(text: str) -> str:
    tfidf_vec      = vectorizer.transform([text])
    urgency_feat   = csr_matrix(np.array([[_urgency_score(text)]]))
    combined       = hstack([tfidf_vec, urgency_feat])
    return model.predict(combined)[0]