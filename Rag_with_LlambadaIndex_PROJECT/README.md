# RAG Workflow Engine (Gradio)

## Quick Start

1. Install dependencies:

```powershell
uv sync
```

2. Ensure `.env` contains:

```env
COHERE_API_KEY=...
PINECONE_API_KEY=...
GEMINI_API_KEY=...
PINECONE_INDEX_NAME=kiro-steering
PINECONE_NAMESPACE=kiro-steering
ALLOW_OFFLINE_FALLBACK=1
```

3. Run app:

```powershell
uv run workflow_engine.py
```

4. Open in browser:
- http://127.0.0.1:7860

## Runtime Modes

- `LLM מלא`: Gemini זמין, תשובה מלאה.
- `Fallback אחזור`: אם Gemini חסום (למשל SSL/NetFree), המערכת מחזירה סיכום מתוך מקורות Pinecone כדי לאפשר עבודה רציפה.

## Troubleshooting

- אם האפליקציה לא עולה: בדקי API keys ב-`.env`.
- אם האפליקציה עולה אבל Gemini נכשל: השאירי `ALLOW_OFFLINE_FALLBACK=1` ותוכלי להמשיך לעבוד במצב fallback.
- אם אין תוצאות בכלל: ודאי שה-index וה-namespace בפיינקון נכונים ושיש בו נתונים.
