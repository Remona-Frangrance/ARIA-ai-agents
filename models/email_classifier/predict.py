import pickle
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, "model.pkl")
vectorizer_path = os.path.join(base_dir, "vectorizer.pkl")

with open(model_path, 'rb') as f:
    model = pickle.load(f)

with open(vectorizer_path, 'rb') as f:
    vectorizer = pickle.load(f)

def predict_email(text):
    X = vectorizer.transform([text])
    prediction = model.predict(X)[0]
    return prediction


if __name__ == "__main__":
    print(predict_email("Win a free iPhone now"))
    print(predict_email("Meeting with client tomorrow"))
    print(predict_email("50% discount on shoes"))
