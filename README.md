# 🤖 AI Engineering Portfolio

> **Building intelligent applications with LLMs, RAG, AI Agents, Tools & Modern AI Architectures**

Welcome to my **AI Engineering portfolio**.

This repository contains hands-on projects focused on building practical applications with **Large Language Models, Retrieval-Augmented Generation, AI Agents, tool calling, semantic search and agentic workflows**.

My goal is not only to work with LLMs, but to understand how to turn them into **reliable software systems that can use data, tools and external services to solve real-world problems**.

---

## 🧠 What I Build

My AI Engineering work focuses on the intersection of:

```text
        ┌──────────────────┐
        │       LLMs       │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │   AI Agents      │
        │   & Workflows    │
        └────────┬─────────┘
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
    Tools       RAG      Memory
       │         │         │
       ▼         ▼         ▼
    APIs      Vectors    Context
       │         │         │
       └─────────┼─────────┘
                 ▼
        ┌──────────────────┐
        │  Real AI Apps    │
        └──────────────────┘
```

### Core Areas

* 🧠 Large Language Models
* 🤖 AI Agents & Agentic Workflows
* 🔎 Retrieval-Augmented Generation (RAG)
* 🛠️ Tool Calling & Function Calling
* 🔌 Model Context Protocol (MCP)
* 📚 Semantic Search
* 🧬 Embeddings & Vector Search
* 🌐 Web Search & Data Extraction
* 👤 Human-in-the-Loop Workflows
* ⚙️ AI-powered Automation
* 🔗 LLM Application Architecture

---

# 🚀 Featured Projects

## 1. 🧠 NotebookLM-Style Research Assistant

**Production-oriented AI research assistant built with LangChain and FastAPI.**

This is the main project in this repository.

The application allows users to provide sources, ask questions grounded in those sources, search the web when required, and generate structured artifacts.

### Architecture

```text
┌─────────────────────────────────────────────┐
│              Web Client                     │
│                                             │
│   Sources  │  Chat  │  Studio  │  Notes    │
└───────────────────┬─────────────────────────┘
                    │ HTTP / REST
                    ▼
┌─────────────────────────────────────────────┐
│              FastAPI Backend                │
├─────────────────────────────────────────────┤
│                                             │
│              AI Agent                      │
│       ┌──────────┼──────────┐               │
│       ▼          ▼          ▼               │
│      RAG       Tools      Memory            │
│       │          │                          │
│       ▼          ▼                          │
│ Vector Store  External APIs                 │
│                                             │
└───────┬──────────┬───────────┬──────────────┘
        │          │           │
        ▼          ▼           ▼
     Gemini      Cohere     Firecrawl
      LLM       Embeddings   Web Data
```

### Key Capabilities

* 💬 **Grounded conversational AI**
* 🔎 **Semantic search over sources**
* 📚 **Vector-based RAG**
* 🌐 **Web search and content extraction**
* 🛠️ **Tool-based AI Agent**
* 👤 **Human-in-the-Loop approval**
* 📝 **Notes & conversation memory**
* 📊 **AI-generated artifacts**
* 🔗 **Source citations**
* 📁 **Dynamic source management**

### AI Architecture

The agent integrates multiple capabilities through tools and services:

```text
User Question
      │
      ▼
   AI Agent
      │
      ├──► Search Sources
      │
      ├──► Semantic Retrieval
      │
      ├──► Web Search
      │
      ├──► Source Management
      │
      ├──► Artifact Generation
      │
      └──► Human Approval
              │
              ▼
        Grounded Response
          + Citations
```

### Technology Stack

| Layer              | Technologies          |
| ------------------ | --------------------- |
| Language           | Python                |
| Backend            | FastAPI, Uvicorn      |
| AI Framework       | LangChain             |
| LLM                | Google Gemini         |
| Embeddings         | Cohere Multilingual   |
| Retrieval          | Vector Search         |
| Vector Store       | InMemoryVectorStore   |
| Web                | Firecrawl             |
| Frontend           | HTML, CSS, JavaScript |
| Package Management | UV                    |

### Project Structure

```text
notebooklm-starter/
│
├── client/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── src/
│   ├── agents/
│   │   └── chat.py
│   │
│   ├── core/
│   │   ├── sources.py
│   │   ├── store.py
│   │   ├── web.py
│   │   └── firecrawl.py
│   │
│   └── api/
│       ├── app.py
│       ├── serve.py
│       ├── schemas.py
│       └── services.py
│
├── main.py
└── pyproject.toml
```

➡️ **[Explore the NotebookLM project](./LangChain%20-%20Project/notebooklm-starter)**

---

# 2. 🔎 RAG with LlamaIndex

A hands-on **Retrieval-Augmented Generation** project exploring document ingestion, indexing, embeddings, retrieval and LLM-powered responses.

### Concepts

* Document ingestion
* Chunking
* Embeddings
* Vector indexing
* Semantic retrieval
* Context-aware generation
* RAG pipelines

➡️ **[Explore the project](./Rag_with_LlambadaIndex_PROJECT)**

---

# 3. 🔌 MCP + Playwright

Exploring **Model Context Protocol (MCP)** and the connection between AI models and external tools.

The project demonstrates how an AI system can interact with external environments through structured tools and browser automation.

### Technologies

`Python` · `MCP` · `Playwright` · `AI Agents`

➡️ **[Explore the project](./MCP%20with%20Playwright%20-%20Project/project-template)**

---

# 4. 📁 File Browser AI Agent

An AI agent designed to interact with files through tools.

The project focuses on the connection between:

```text
LLM
 │
 ▼
Agent
 │
 ▼
Tools
 │
 ▼
File System
```

This demonstrates how LLMs can move beyond text generation and perform controlled actions through external tools.

➡️ **[Explore the project](./Skill%20-%20Project/files-browser-agent)**

---

# 5. ⚡ Task Manager Function Calling Agent

An AI-powered task manager demonstrating **LLM Function Calling** and tool-based execution.

The system translates natural-language instructions into structured function calls that interact with application logic.

### Example Architecture

```text
Natural Language
       │
       ▼
      LLM
       │
       ▼
Function Calling
       │
       ▼
Application Tool
       │
       ▼
Task Operation
```

➡️ **[Explore the project](./Task%20Manager%20Function%20Calling%20Agent)**

---

# 🧰 AI Engineering Tech Stack

### Languages

![Python](https://img.shields.io/badge/Python-3776AB?style=flat\&logo=python\&logoColor=white)

### LLM & AI

`LLMs` · `Generative AI` · `RAG` · `AI Agents` · `LangChain` · `LangGraph` · `LlamaIndex`

### Agent Engineering

`MCP` · `Function Calling` · `Tool Calling` · `Agent Workflows` · `Human-in-the-Loop`

### Retrieval

`Embeddings` · `Semantic Search` · `Vector Search` · `Vector Stores`

### AI APIs & Tools

`Google Gemini` · `OpenAI API` · `Anthropic API` · `Cohere` · `Firecrawl`

### Backend

`Python` · `FastAPI` · `REST APIs`

### Additional Technologies

`Docker` · `Git` · `GitHub` · `PostgreSQL` · `FAISS` · `ChromaDB`

---

# 🏗️ AI Engineering Principles

I focus on building AI applications that are:

### 🎯 Grounded

Responses should be based on relevant data rather than relying only on the model's internal knowledge.

### 🔧 Tool-Enabled

LLMs become significantly more useful when they can interact with tools, APIs and external systems.

### 🔎 Retrieval-Aware

RAG and semantic search allow AI systems to work with domain-specific knowledge.

### 👤 Human-Controlled

For sensitive or consequential operations, human approval can be incorporated into the agent workflow.

### 🧩 Modular

AI systems should separate agents, tools, retrieval, business logic and external integrations.

### 🚀 Production-Oriented

The goal is to move from isolated LLM experiments toward complete applications with APIs, services, state and user interfaces.

---

# 📈 Current Focus

I'm currently focusing on advancing my skills in:

* Agentic AI
* LLM application architecture
* Advanced RAG
* Multi-agent systems
* MCP
* Tool-enabled AI
* AI application backends
* AI + Full Stack integration

---

# 👩‍💻 About Me

I'm a **Full Stack & AI Engineer** interested in building modern software systems that combine traditional software engineering with Generative AI.

My background in full-stack development gives me a strong foundation in:

`Frontend` · `Backend` · `APIs` · `Databases` · `Architecture`

which I combine with:

`LLMs` · `RAG` · `Agents` · `Tools` · `Semantic Search`

to build intelligent end-to-end applications.

---

## 🔗 Connect

**GitHub:** [@shani01846](https://github.com/shani01846)

⭐ If you find these projects interesting, feel free to explore the individual project repositories.
