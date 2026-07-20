import os
from openai import OpenAI
from prompt import SYSTEM_PROMPT
from netfree_unstrict_ssl import unstrict_ssl
from dotenv import load_dotenv

# טיפול ב-SSL עבור נטפרי
unstrict_ssl()
load_dotenv()

# טעינת המפתח מהסביבה
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in .env file")

client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=api_key
)

def get_command(user_input):
    preferred_model = (os.getenv("GEMINI_MODEL") or "").strip()
    models = [
        "gemini-flash-lite-latest",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-lite-001",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.5-flash",
    ]
    if preferred_model:
        models = [preferred_model] + [m for m in models if m != preferred_model]
    last_error = None

    for model_name in models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content
        except Exception as error:
            last_error = error
            error_text = str(error).lower()
            if "429" in error_text or "resource_exhausted" in error_text or "quota" in error_text:
                continue
            if "404" in error_text or "not found" in error_text or "unsupported" in error_text or "400" in error_text:
                continue
            raise

    if last_error and ("429" in str(last_error) or "RESOURCE_EXHAUSTED" in str(last_error) or "quota" in str(last_error).lower()):
        raise RuntimeError(
            "Gemini API quota is exhausted or unavailable for this project/key. "
            "Enable billing or use a key/project with active quota. "
            f"Last error: {last_error}"
        )

    raise RuntimeError(f"All configured Gemini models failed. Last error: {last_error}")