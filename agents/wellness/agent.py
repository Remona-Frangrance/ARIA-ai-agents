import json
from shared.llm_client import ask_llm
from agents.wellness.prompts import SYSTEM_PROMPT, WELLNESS_ANALYSIS_PROMPT
from shared.wellness_db import log_wellness, get_wellness_summary

def handle_task(task: str):
    # Check for logging intent
    if "drank" in task.lower() or "glass" in task.lower():
        # Simple extraction for demo, could use LLM
        log_wellness('hydration', 1)
        return {"type": "wellness", "result": "Logged 1 glass of water."}
    
    if "slept" in task.lower() or "hours" in task.lower():
        # Try to extract number
        import re
        nums = re.findall(r'\d+\.?\d*', task)
        if nums:
            val = float(nums[0])
            log_wellness('sleep', val)
            return {"type": "wellness", "result": f"Logged {val} hours of sleep."}
    
    prompt = WELLNESS_ANALYSIS_PROMPT.format(task=task)
    ai_response = ask_llm(prompt, system=SYSTEM_PROMPT)
    
    try:
        start = ai_response.find("{")
        end = ai_response.rfind("}") + 1
        ai_data = json.loads(ai_response[start:end])
        
        # Log the mood if analysis shows it
        if ai_data.get("type") == "mood":
            log_wellness('mood', ai_data.get("score", 50), ai_data.get("summary"))
            
    except:
        ai_data = {
            "type": "general",
            "sentiment": "Neutral",
            "score": 50,
            "actionable_advice": ["Monitor your daily habits"],
            "summary": ai_response
        }

    return {
        "type": "wellness",
        "task": task,
        "wellness_type": ai_data.get("type", "general"),
        "sentiment": ai_data.get("sentiment", "Neutral"),
        "score": ai_data.get("score", 50),
        "steps": ai_data.get("actionable_advice", []),
        "message": ai_data.get("summary", ai_response)
    }

def get_wellness_analytics():
    logs = get_wellness_summary()
    
    if not logs:
        return {
            "logs": [],
            "burnout": {"risk": "Low", "reason": "No data available yet. Start logging to see analysis.", "score": 0}
        }

    # ML/AI Logic: Predict Burnout
    history = "\n".join([f"{l['date']}: {l['type']}={l['value']}" for l in logs[:14]])
    
    burnout_prompt = f"""
    Analyze the following wellness history and predict burnout risk (Low/Medium/High).
    History:
    {history}
    
    Provide response in JSON: {{"risk": "Low|Medium|High", "reason": "Short explanation", "score": 0-100}}
    """
    
    analysis = ask_llm(burnout_prompt, system="You are a health data scientist.")
    try:
        start = analysis.find("{")
        end = analysis.rfind("}") + 1
        burnout_data = json.loads(analysis[start:end])
    except:
        burnout_data = {"risk": "Low", "reason": "Insufficient data", "score": 20}
        
    return {
        "logs": logs,
        "burnout": burnout_data
    }
