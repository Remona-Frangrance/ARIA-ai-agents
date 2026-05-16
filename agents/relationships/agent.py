import json
from shared.llm_client import ask_llm
from agents.relationships.prompts import SYSTEM_PROMPT, RELATIONSHIP_ANALYSIS_PROMPT
from shared.relationship_db import get_contacts, add_interaction

def handle_task(task: str):
    # Check for logging interaction intent
    if "sent a message" in task.lower() or "called" in task.lower():
        contacts = get_contacts()
        # Find which contact name is in the task
        for c in contacts:
            if c['name'].lower() in task.lower():
                add_interaction(c['id'], 0.9, task)
                return {"type": "relationship", "result": f"Logged interaction with {c['name']}"}

    prompt = RELATIONSHIP_ANALYSIS_PROMPT.format(task=task)
    ai_response = ask_llm(prompt, system=SYSTEM_PROMPT)
    
    try:
        start = ai_response.find("{")
        end = ai_response.rfind("}") + 1
        ai_data = json.loads(ai_response[start:end])
    except:
        ai_data = {
            "type": "general",
            "person": "Unknown",
            "suggestions": ["Reach out and say hello"],
            "summary": ai_response
        }

    return {
        "type": "relationship",
        "task": task,
        "rel_type": ai_data.get("type", "general"),
        "person": ai_data.get("person", "Unknown"),
        "event_date": ai_data.get("event_date"),
        "steps": ai_data.get("suggestions", []),
        "message": ai_data.get("summary", ai_response)
    }

def get_social_intel():
    contacts = get_contacts()
    
    if not contacts:
        return {
            "contacts": [],
            "ai_suggestion": {"person_name": "None", "reason": "No contacts found. Add your first contact to see AI suggestions!", "suggested_message": "Hello!"}
        }

    # AI Logic: Social Suggestions
    intel_prompt = f"""
    Analyze these contacts and suggest one person to reach out to and why.
    Contacts: {json.dumps(contacts)}
    
    Return JSON: {{"person_name": "...", "reason": "...", "suggested_message": "..."}}
    """
    
    ai_suggestion = ask_llm(intel_prompt, system="You are a social intelligence expert.")
    try:
        start = ai_suggestion.find("{")
        end = ai_suggestion.rfind("}") + 1
        suggestion_data = json.loads(ai_suggestion[start:end])
    except:
        suggestion_data = {"person_name": "Sarah", "reason": "Consistency", "suggested_message": "Hi!"}
        
    return {
        "contacts": contacts,
        "ai_suggestion": suggestion_data
    }
