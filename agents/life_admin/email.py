import webbrowser

def open_gmail(task: str):
    url = "https://mail.google.com/mail/u/0/#inbox"
    webbrowser.open(url)
    return f"📧 Opening Gmail for: {task}"