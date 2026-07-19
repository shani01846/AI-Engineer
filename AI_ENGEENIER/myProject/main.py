import os
import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv

with open("prompt.md", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE = f.read()

# 1. טעינת קובץ ה-env
load_dotenv()
gemini_key = os.getenv("OPENAI_API_KEY")

# 2. אתחול הלקוח - מפנים את הפניות לשרת של גוגל
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=gemini_key
)

def get_command(prompt):
    if not gemini_key:
        return "❌ שגיאה: מפתח GEMINI_API_KEY לא נמצא בקובץ ה-.env"
        
    try:
        # פנייה למודל החינמי של גוגל דרך ממשק ה-OpenAI
        response = client.chat.completions.create(
            model="gemini-2.5-flash", 
            messages=[
                {"role": "user", "content": PROMPT_TEMPLATE.replace("{user_input}", prompt)}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # return f"❌ שגיאה בתקשורת: {str(e)}"
        raw_response = response.choices[0].message.content.strip()
        
        # --- כאן מתבצעת הבדיקה של רמת השאלה ---
        if "|" in raw_response:
            # פיצול התשובה לפי התו '|'
            color, result = raw_response.split("|", 1)
            color = color.strip().upper()
            result = result.strip()
            
            # לוגיקה לפי צבעים
            if color == "GREEN":
                return result  # מחזיר רק את הפקודה נקייה
                
            elif color == "ORANGE":
                return f"⚠️ אזהרה (סיכון בינוני):\nהפקודה המוצעת היא: {result}\nשים לב, הרצת פקודה זו עלולה להיות מסוכנת או למחוק מידע."
                
            elif color == "RED":
                return f"❌ חסימה:\n{result}"
                
        # גיבוי במקרה שהמודל לא החזיר את הפורמט עם התו '|'
        return raw_response
        
    except Exception as e:
        return f"❌ שגיאה בתקשורת: {str(e)}"

# ממשק Gradio
gr.Interface(
    fn=get_command,
    inputs=gr.Textbox(label="Describe what you want to do", placeholder="e.g. מה כתובת ה-IP שלי?"),
    outputs=gr.Textbox(label="Terminal Command"),
    title="Natural Language ➔ Terminal Command (Free Gemini)",
    description="Type a task in plain language and get the terminal command for free."
).launch()