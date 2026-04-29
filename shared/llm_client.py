import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def ask_llm(prompts:str, system: str="You are a helpful assistant.",model:str="llama-3.3-70b-versatile") -> str:
   """
   Send a prompt to Groq and get a response.
   This is the single function all 5 agents will use.
   """
   response = client.chat.completions.create(
    model=model,
    messages=[
        {"role" : "system", "content": system},
        {"role" : "user", "content": prompts}
    ],
    max_tokens=1000,
    temperature=0.7
   )
   return response.choices[0].message.content