# AI Terminal Command Agent

> An AI-powered developer tool that translates natural language into terminal commands while applying an AI-based safety and risk classification layer.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Gemini](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange)
![Gradio](https://img.shields.io/badge/UI-Gradio-green)
![OpenAI SDK](https://img.shields.io/badge/API-OpenAI%20Compatible-black)

## Overview

**AI Terminal Command Agent** is an AI-powered application designed to make command-line interactions more accessible.

Instead of remembering terminal syntax, users can describe what they want to do in natural language. The application sends the request to an LLM, generates an appropriate terminal command, and evaluates the potential risk level before presenting the result.

For example:

> **User:** "Create a folder named reports"

```bash
mkdir reports
```

The project combines **LLM integration, prompt engineering, structured AI responses, safety classification, and a simple interactive UI**.

---

## Key Features

* Convert natural language into terminal commands
* Powered by **Gemini 2.5 Flash**
* OpenAI-compatible API integration
* AI-based command risk classification
* Structured `GREEN | ORANGE | RED` responses
* External prompt management using `prompt.md`
* Interactive web UI built with Gradio
* Environment-based API key management
* Modern Python dependency management with UV

---

## Architecture

```text
┌──────────────┐
│     User     │
│ Natural Lang │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Gradio    │
│      UI      │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Prompt Template │
│    prompt.md     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Gemini 2.5     │
│      Flash       │
│                  │
│ OpenAI-Compatible│
│       API        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Structured Output│
│                  │
│ GREEN | command  │
│ ORANGE | command │
│ RED | message    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Risk Processing  │
│  & Final Output  │
└──────────────────┘
```

---

## How It Works

### 1. Natural Language Input

The user describes a task using plain language.

**Example:**

```text
Show all files in the current directory
```

---

### 2. Prompt Construction

The application loads a prompt template from `prompt.md`.

```python
with open("prompt.md", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE = f.read()
```

The user's request is dynamically injected into the prompt:

```python
PROMPT_TEMPLATE.replace("{user_input}", prompt)
```

Keeping the prompt outside the Python application makes the AI behavior easier to maintain, test, and improve independently.

---

### 3. LLM Request

The application communicates with Google Gemini through its OpenAI-compatible API.

```python
client = OpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=gemini_key
)
```

The model processes the user's request and returns a structured response.

---

### 4. Structured AI Response

The expected format is:

```text
COLOR | RESULT
```

Examples:

```text
GREEN | mkdir reports
```

```text
ORANGE | rm -rf temporary_files
```

```text
RED | This request cannot be safely converted into a terminal command.
```

---

### 5. Risk Classification

The application processes the AI response based on its classification.

| Level     | Description                   | Application Behavior |
| --------- | ----------------------------- | -------------------- |
| 🟢 GREEN  | Safe command                  | Return the command   |
| 🟠 ORANGE | Potentially risky command     | Display a warning    |
| 🔴 RED    | Unsafe or unsupported request | Block the result     |

This creates a simple separation between **command generation** and **command safety evaluation**.

---

## Project Structure

```text
myProject/
│
├── main.py
│   └── Application logic and Gradio interface
│
├── prompt.md
│   └── AI instructions and output rules
│
├── pyproject.toml
│   └── Python project configuration
│
├── uv.lock
│   └── Locked dependency versions
│
├── .python-version
│   └── Python version configuration
│
├── .gitignore
│
└── README.md
```

---

## Technology Stack

| Technology                  | Purpose                         |
| --------------------------- | ------------------------------- |
| **Python**                  | Core application                |
| **Google Gemini 2.5 Flash** | Large Language Model            |
| **OpenAI SDK**              | API client                      |
| **Gradio**                  | Interactive web interface       |
| **python-dotenv**           | Environment variable management |
| **UV**                      | Dependency management           |

---

## Installation

### Prerequisites

* Python 3.12+
* A Google Gemini API key
* UV recommended

### Clone the Repository

```bash
git clone https://github.com/shani01846/AI-Engineer.git
cd AI-Engineer/AI_ENGEENIER/myProject
```

### Install Dependencies

Using UV:

```bash
uv sync
```

Or using pip:

```bash
pip install gradio openai python-dotenv
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_gemini_api_key
```

The application loads the API key at runtime:

```python
load_dotenv()

gemini_key = os.getenv("OPENAI_API_KEY")
```

> **Security Note:** Never commit your `.env` file or API keys to source control.

---

## Running the Application

Using UV:

```bash
uv run python main.py
```

Or:

```bash
python main.py
```

After launching, Gradio provides a local URL where the application can be accessed through a browser.

---

## Example Usage

### Safe Request

**Input**

```text
Create a directory named projects
```

**Output**

```text
mkdir projects
```

---

### Medium-Risk Request

**Input**

```text
Delete the temporary files folder
```

**Output**

```text
⚠️ Warning (Medium Risk)

The suggested command is:

rm -rf temporary_files

Please review this command carefully before executing it.
```

---

### Unsupported Request

**Input**

```text
Write a Python application for me
```

**Output**

```text
❌ Blocked

This request is outside the scope of the Terminal Command Agent.
```

---

# AI Engineering Concepts Demonstrated

This project demonstrates practical AI Engineering concepts beyond simply calling an LLM API.

### Prompt Engineering

The model behavior is controlled through an external prompt template.

This makes it easier to:

* Experiment with prompts
* Add few-shot examples
* Improve output consistency
* Define safety rules
* Separate AI instructions from application logic

---

### Structured LLM Output

The model is expected to follow a predictable format:

```text
COLOR | RESULT
```

This allows application code to interpret the LLM response programmatically.

Structured outputs are important when integrating LLMs into real applications because free-form responses can be difficult to process reliably.

---

### AI Safety Layer

The project introduces a simple risk classification system:

```text
GREEN
ORANGE
RED
```

This demonstrates the concept of adding application-level safety controls around LLM-generated output.

The application does not automatically execute commands, allowing users to review generated commands before running them.

---

### OpenAI-Compatible API Integration

The project demonstrates how the OpenAI Python SDK can be used with an alternative LLM provider through a compatible API endpoint.

This design makes it easier to switch or experiment with AI providers without completely rewriting the client integration.

---

## Future Improvements

Potential improvements include:

* [ ] Detect the user's operating system automatically
* [ ] Generate OS-specific commands
* [ ] Add command explanations
* [ ] Add copy-to-clipboard functionality
* [ ] Add command history
* [ ] Improve error handling
* [ ] Replace delimiter parsing with structured JSON output
* [ ] Add Pydantic validation for AI responses
* [ ] Add automated tests
* [ ] Add logging and monitoring
* [ ] Add Docker support
* [ ] Add CI/CD using GitHub Actions
* [ ] Add a sandbox for command execution
* [ ] Add more granular risk categories
* [ ] Support multiple LLM providers

---

## Suggested Next Architecture

A future version could use a more robust architecture:

```text
User
 │
 ▼
Frontend / Gradio
 │
 ▼
Application Layer
 │
 ├── Prompt Builder
 │
 ├── LLM Client
 │
 ├── Output Validator
 │
 └── Risk Engine
 │
 ▼
Structured Response
 │
 ▼
User
```

Instead of parsing:

```text
GREEN | mkdir test
```

the LLM could return structured JSON:

```json
{
  "risk_level": "GREEN",
  "command": "mkdir test",
  "explanation": "Creates a new directory named test."
}
```

This would make the application more reliable and easier to scale.

---

## What I Learned

While building this project, I practiced:

* Integrating LLM APIs into Python applications
* Prompt engineering
* Few-shot prompting
* Structured AI outputs
* AI safety classification
* OpenAI-compatible API integration
* Environment variable management
* Building AI applications with Gradio
* Modern Python dependency management

---

## Disclaimer

AI-generated terminal commands should always be reviewed before execution.

The risk classification in this project is AI-based and should not be considered a complete security solution. Users are responsible for understanding the impact of commands before running them.

---

## Author

**Shani Kirzon**

Full Stack Developer & AI Engineer

Focused on building practical AI-powered applications using modern software engineering and Generative AI technologies.
