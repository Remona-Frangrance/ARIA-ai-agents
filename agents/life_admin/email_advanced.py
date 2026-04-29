from models.email_classifier.predict import predict_email

def clean_emails():
    # Simulated inbox (later replace with Gmail API)
    emails = [
    "Win a free iPhone now",
    "Meeting with client tomorrow",
    "50% discount on shoes",
    "Project deadline extended",
    "Claim your reward urgently"
    ]

    result = {
        "important": [],
        "promotion": [],
        "spam": []
    }

    for email in emails:
        category = predict_email(email)

        if category == "Important":
            result["important"].append(email)
        elif category == "Promotion":
            result["promotion"].append(email)
        else:
            result["spam"].append(email)

    return result