import os
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import pickle

base_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(base_dir, "data.csv")
model_path = os.path.join(base_dir, "model.pkl")
vectorizer_path = os.path.join(base_dir, "vectorizer.pkl")

data = pd.read_csv(data_path)

X = data['text']
y = data['label']

vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)

model = MultinomialNB()
model.fit(X_vec,y)

with open(model_path, 'wb') as f:
    pickle.dump(model, f)

with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

print("Model saved successfully")