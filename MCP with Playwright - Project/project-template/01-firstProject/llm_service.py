import os
from openai import OpenAI
from prompt import SYSTEM_PROMPT
from netfree_unstrict_ssl import unstrict_ssl
from dotenv import load_dotenv

# טיפול ב-SSL עבור נטפרי
unstrict_ssl()
load_dotenv()

# טעינת המפתח מהסביבה
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Missing GROQ_API_KEY in .env file")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)

def get_command(user_input):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content