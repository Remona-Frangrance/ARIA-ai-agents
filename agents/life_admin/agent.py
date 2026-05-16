from agents.life_admin.calendar import schedule_events
from models.task_priority.predict import predict_priority
from shared.llm_client import ask_llm
from agents.life_admin.email import open_gmail
from agents.life_admin.email_advanced import clean_emails


def handle_task(task:str):
    #Detect calendar intent
    if "meeting" in task.lower() or "schedule" in task.lower() or "appointment" in task.lower():
        event = schedule_events(task)
        return{
            "type":"calendar",
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

    # create a sophisticated prompt for LLM
    prompt = f"""
    You are ARIA's Life Admin Specialist. Analyze this task: "{task}"
    Priority Level (from model): {priority}

    Extract and structure the following in JSON:
    {{
        "category": "Bill | Meeting | Deadline | Subscription | Personal",
        "due_date": "YYYY-MM-DD or None",
        "actionable_steps": ["step 1", "step 2"],
        "summary": "2-line professional advice"
    }}
    """
    ai_response = ask_llm(prompt)
    
    # Try to parse JSON from AI response
    try:
        import json
        start = ai_response.find("{")
        end = ai_response.rfind("}") + 1
        ai_data = json.loads(ai_response[start:end])
    except:
        ai_data = {
            "category": "Task",
            "due_date": None,
            "actionable_steps": ["Complete the task as soon as possible"],
            "summary": ai_response
        }

    return {
        "type": "task",
        "task": task,
        "priority": priority,
        "category": ai_data.get("category", "Task"),
        "due_date": ai_data.get("due_date"),
        "steps": ai_data.get("actionable_steps", []),
        "message": ai_data.get("summary", ai_response)
    }