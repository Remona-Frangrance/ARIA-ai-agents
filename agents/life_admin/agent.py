from agents.life_admin.calendar import schedule_events
from models.task_priority.predict import predict_priority
from shared.llm_client import ask_llm
from agents.life_admin.email import open_gmail
from agents.life_admin.email_advanced import clean_emails


def handle_task(task:str):
    #Detect calender intent
    if "meeting" in task.lower() or "schedule" in task.lower() or "appointment" in task.lower():
        event = schedule_events(task)
        return{
            "type":"calender",
            "result":event
        }
    #Detect gmail intent
    elif "email" in task.lower() or "gmail" in task.lower() or "open mail" in task.lower():
        email = open_gmail(task)
        return{
            "type":"email",
            "result":email
        }
    #Detect gmail advanced
    elif "clean my emails" in task.lower():
        emails = clean_emails()
        return{
            "type":"email_advanced",
            "result":emails
        }
    priority = predict_priority(task)

    #create  a prompt for LLM
    prompt = f"""
    Task: {task}
    Priority Level: {priority}

    Explain in 2-3 lines why this task has this priority and what the user should do .
    """
    explanation = ask_llm(prompt)

    return {
        "type":"task",
        "task":task,
        "priority":priority,
        "message":explanation
    }