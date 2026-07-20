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

## Visual Examples

### Structured Answer (LLM Saving)

<p align="center">
	<img src="assets/status%20structure.png" alt="Structured answer mode with reduced LLM usage" width="920" />
</p>

<p align="center">
	When the query matches structured signals, the workflow can answer from structured data and reduce unnecessary LLM calls.
</p>

### Rules View (Clean and Readable)

<p align="center">
	<img src="assets/rules%20for%20edit.png" alt="Rules-oriented response example" width="920" />
</p>

<p align="center">
	A clear rules-style answer format that keeps decisions, constraints, and guidance easy to scan.
</p>

> Tip:
> Use structured/rules-oriented prompts for predictable output and lower model cost.

## Troubleshooting

- אם האפליקציה לא עולה: בדקי API keys ב-`.env`.
- אם האפליקציה עולה אבל Gemini נכשל: השאירי `ALLOW_OFFLINE_FALLBACK=1` ותוכלי להמשיך לעבוד במצב fallback.
- אם אין תוצאות בכלל: ודאי שה-index וה-namespace בפיינקון נכונים ושיש בו נתונים.
