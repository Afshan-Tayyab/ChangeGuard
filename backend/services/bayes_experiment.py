# backend/services/bayes_experiment.py
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import numpy as np

# 1. Create a small labelled dataset
# X = sentences, y = category
training_data = [
    ("Students may apply", "Modality"),
    ("Students must apply", "Modality"),
    ("You should submit", "Modality"),
    ("Submit by Friday", "Deadline"),
    ("Due before Monday", "Deadline"),
    ("Deadline is tomorrow", "Deadline"),
    ("Attendance above 75%", "Condition"),
    ("Score at least 60", "Condition"),
    ("Below 50 percent", "Condition"),
    ("Students are not allowed", "Negation"),
    ("You cannot apply", "Negation"),
    ("Never submit late", "Negation"),
    ("Only final-year students", "Restriction"),
    ("All students may apply", "Restriction"),
    ("Restricted to staff", "Restriction"),
    ("Unless you have a scholarship", "Exception"),
    ("Except for medical reasons", "Exception"),
    ("Excluding first years", "Exception")
]

X_train = [item[0] for item in training_data]
y_train = [item[1] for item in training_data]

# 2. Build the Naive Bayes Pipeline (Bag of Words + MultinomialNB)
model = make_pipeline(CountVectorizer(), MultinomialNB())

# 3. Train the model
model.fit(X_train, y_train)

# 4. Test the model with new sentences
test_sentences = [
    "Students must submit the form",
    "The deadline is Friday",
    "Attendance must be above 80%",
    "Students are not eligible",
    "Only staff can apply",
    "Unless they pay the fee",
    "Applications are due soon"
]

print("=== NAIVE BAYES CLASSIFIER EXPERIMENT ===\n")
print("Predicting categories for new sentences:\n")

for sentence in test_sentences:
    prediction = model.predict([sentence])[0]
    probabilities = model.predict_proba([sentence])[0]
    
    # Get the highest probability
    max_prob = np.max(probabilities)
    
    print(f"Sentence: '{sentence}'")
    print(f"  Predicted Category: {prediction} (Confidence: {max_prob*100:.2f}%)")