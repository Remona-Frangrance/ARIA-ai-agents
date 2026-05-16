"""
Expense Categorizer — Prediction Module
Loads the trained model and provides category prediction for transaction descriptions.
"""

import os
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")

# Lazy-load model to handle case where model hasn't been trained yet
_model = None
_vectorizer = None


def _load_model():
    global _model, _vectorizer
    if _model is None:
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            _model = joblib.load(MODEL_PATH)
            _vectorizer = joblib.load(VECTORIZER_PATH)
        else:
            print("⚠️ Expense categorizer model not found. Run train.py first.")
            return False
    return True


# Keyword fallback for when the ML model isn't available
KEYWORD_MAP = {
    "rent": "Rent", "house rent": "Rent", "pg": "Rent", "accommodation": "Rent",
    "flat rent": "Rent", "room rent": "Rent", "maintenance": "Rent",
    "swiggy": "Food", "zomato": "Food", "food": "Food", "restaurant": "Food",
    "lunch": "Food", "dinner": "Food", "breakfast": "Food", "cafe": "Food",
    "biryani": "Food", "pizza": "Food", "burger": "Food", "tea": "Food",
    "coffee": "Food", "snack": "Food", "uber eats": "Food",
    "uber": "Transport", "ola": "Transport", "auto": "Transport",
    "metro": "Transport", "bus": "Transport", "petrol": "Transport",
    "diesel": "Transport", "cab": "Transport", "rapido": "Transport",
    "parking": "Transport", "toll": "Transport", "train": "Transport",
    "netflix": "Subscriptions", "spotify": "Subscriptions", "prime": "Subscriptions",
    "youtube premium": "Subscriptions", "hotstar": "Subscriptions",
    "subscription": "Subscriptions",
    "electricity": "Utilities", "water bill": "Utilities", "gas": "Utilities",
    "broadband": "Utilities", "internet": "Utilities", "mobile recharge": "Utilities",
    "wifi": "Utilities", "airtel": "Utilities", "jio": "Utilities",
    "bigbasket": "Groceries", "blinkit": "Groceries", "zepto": "Groceries",
    "groceries": "Groceries", "vegetables": "Groceries", "fruits": "Groceries",
    "dmart": "Groceries", "milk": "Groceries", "grocery": "Groceries",
    "amazon": "Shopping", "flipkart": "Shopping", "myntra": "Shopping",
    "shopping": "Shopping", "clothes": "Shopping", "shoes": "Shopping",
    "electronics": "Shopping",
    "movie": "Entertainment", "concert": "Entertainment", "pub": "Entertainment",
    "bowling": "Entertainment", "gaming": "Entertainment", "club": "Entertainment",
    "gym": "Health", "pharmacy": "Health", "doctor": "Health", "medicine": "Health",
    "hospital": "Health", "dentist": "Health", "health": "Health",
    "emi": "EMI", "loan": "EMI", "installment": "EMI",
    "sip": "Investments", "mutual fund": "Investments", "stock": "Investments",
    "invest": "Investments", "fd": "Investments", "ppf": "Investments",
    "course": "Education", "udemy": "Education", "tuition": "Education",
    "college": "Education", "book": "Education", "exam": "Education",
    "salary": "Salary", "bonus": "Salary", "incentive": "Salary",
    "freelance": "Freelance", "upwork": "Freelance", "fiverr": "Freelance",
    "haircut": "Personal", "salon": "Personal", "laundry": "Personal",
    "gift": "Personal", "donation": "Personal",
}


def predict_category(text: str) -> str:
    """Predict the spending category for a transaction description."""
    if _load_model():
        try:
            tfidf_vec = _vectorizer.transform([text])
            prediction = _model.predict(tfidf_vec)[0]
            confidence = max(_model.predict_proba(tfidf_vec)[0])
            
            # If model confidence is low, fall back to keywords
            if confidence < 0.3:
                keyword_result = _keyword_fallback(text)
                if keyword_result != "Other":
                    return keyword_result
            
            return prediction
        except Exception as e:
            print(f"ML prediction error: {e}")
            return _keyword_fallback(text)
    else:
        return _keyword_fallback(text)


def _keyword_fallback(text: str) -> str:
    """Keyword-based fallback categorization."""
    text_lower = text.lower()
    for keyword, category in KEYWORD_MAP.items():
        if keyword in text_lower:
            return category
    return "Other"


def predict_with_confidence(text: str) -> dict:
    """Predict category with confidence score."""
    if _load_model():
        try:
            tfidf_vec = _vectorizer.transform([text])
            prediction = _model.predict(tfidf_vec)[0]
            probabilities = _model.predict_proba(tfidf_vec)[0]
            confidence = max(probabilities)

            # Get top 3 predictions
            top_indices = probabilities.argsort()[-3:][::-1]
            top_predictions = [
                {"category": _model.classes_[i], "confidence": round(float(probabilities[i]), 3)}
                for i in top_indices
            ]

            return {
                "category": prediction,
                "confidence": round(float(confidence), 3),
                "top_predictions": top_predictions,
            }
        except Exception:
            pass

    return {
        "category": _keyword_fallback(text),
        "confidence": 0.5,
        "top_predictions": [{"category": _keyword_fallback(text), "confidence": 0.5}],
    }
