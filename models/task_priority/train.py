import pandas as pd
import joblib
import numpy as np
from scipy.sparse import hstack, csr_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

data = pd.read_csv("./models/task_priority/data.csv")
X_text = data['text']
Y = data['label']

# ngram_range=(1,2) captures multi-word patterns like "right now", "by midnight"
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
X_tfidf = vectorizer.fit_transform(X_text)

# A single extra binary column that fires on strong urgency signals the TF-IDF
# vocabulary might miss in short, novel sentences.
URGENCY_WORDS = [
    "asap", "urgent", "urgently", "now", "right now", "immediately",
    "emergency", "critical", "deadline", "overdue", "rush", "today",
    "tonight", "this morning", "before", "expire", "expires", "expiring",
    "summons", "court", "police", "911", "ambulance", "chest pain",
    "by midnight", "right away", "at once"
]

def urgency_score(text: str) -> float:
    text_lower = text.lower()
    return float(any(kw in text_lower for kw in URGENCY_WORDS))

urgency_feature = csr_matrix(
    np.array([urgency_score(t) for t in X_text]).reshape(-1, 1)
)

# Combine TF-IDF + urgency feature
X_combined = hstack([X_tfidf, urgency_feature])

# Train / test split
X_train, X_test, y_train, y_test = train_test_split(
    X_combined, Y, test_size=0.2, random_state=42, stratify=Y
)

# class_weight='balanced' prevents the model from defaulting to the majority class
model = LogisticRegression(class_weight='balanced', max_iter=500, C=1.0)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("\n-- Evaluation on held-out test set ----------------------------------")
print(classification_report(y_test, y_pred))

# Save artifacts
joblib.dump(model,      "./models/task_priority/model.pkl")
joblib.dump(vectorizer, "./models/task_priority/vectorizer.pkl")

print("Model trained and saved successfully")
