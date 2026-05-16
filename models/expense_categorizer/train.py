"""
Expense Categorizer — Training Script
Trains a Logistic Regression + TF-IDF model to classify transaction descriptions
into spending categories (Food, Rent, Transport, etc.)
"""

import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Load training data
data = pd.read_csv("./models/expense_categorizer/data.csv")
X_text = data["text"]
Y = data["label"]

print(f"Loaded {len(data)} training samples across {Y.nunique()} categories")
print(f"Categories: {sorted(Y.unique())}")
print(f"\nDistribution:\n{Y.value_counts()}\n")

# TF-IDF vectorization with bigrams
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=5000,
    sublinear_tf=True,
    strip_accents="unicode",
    lowercase=True,
)
X_tfidf = vectorizer.fit_transform(X_text)

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf, Y, test_size=0.2, random_state=42, stratify=Y
)

# Train model with balanced class weights
model = LogisticRegression(
    class_weight="balanced",
    max_iter=1000,
    C=1.0,
    solver="lbfgs",
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("\n-- Evaluation on held-out test set --")
print(classification_report(y_test, y_pred))

# Save artifacts
joblib.dump(model, "./models/expense_categorizer/model.pkl")
joblib.dump(vectorizer, "./models/expense_categorizer/vectorizer.pkl")

print("Expense Categorizer model trained and saved successfully!")
