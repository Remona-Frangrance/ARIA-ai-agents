
import json
from datetime import timedelta
import webbrowser
import webbrowser
from shared.llm_client import ask_llm
from datetime import datetime



def schedule_events(task: str):
 
    prompt = f"""
    Extract:
    -title
    -date
    -time

    Task :"{task}"

    Return JSON:
    {{
        "title":"",
        "date":"",
        "time":""
    }}

    """
    

    response = ask_llm(prompt)
    start = response.find("{")
    end = response.rfind("}") + 1

    json_str = response[start:end]

    data = json.loads(json_str)

    title = data["title"]
    data_text = data["date"].lower()
    time_text = data["time"].lower()

    if data_text == "tomorrow":
        date_obj = (datetime.now() + timedelta(days=1))
    elif data_text == "today":
        date_obj = datetime.now()
    else:
        date_obj = datetime.strptime(data_text, "%Y-%m-%d")

    time_obj = datetime.strptime(time_text, "%I%p")
        
    final_datetime = date_obj.replace(hour=time_obj.hour, minute=0, second=0) 
   
    formatted = final_datetime.strftime("%Y%m%dT%H%M%S")

    url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={formatted}/{formatted}" 
    webbrowser.open(url) 
    return f"📅 Event ready: {title} at {final_datetime}"