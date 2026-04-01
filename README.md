# 🧠 Helpdesk AI Triage System

## 📌 Overview

This project implements a multi-agent system based on LLMs to automate customer support ticket management.

The system is capable of:

* Classifying tickets (domain, subdomain, product, priority)
* Interpreting user problems and intent
* Retrieving relevant knowledge (RAG)
* Generating structured summaries
* Producing clear and actionable responses

---

## 🧱 Architecture

The system follows a modular pipeline:

```
Input Ticket
   ↓
Router Agent
   ↓
Domain Agent
   ↓
RAG Retrieval
   ↓
Summary Agent
   ↓
Response Agent
   ↓
Output
```

Each component has a well-defined responsibility, enabling scalability and traceability.

---

## 🗂️ Project Structure

```
project/
│
├── data/
│   ├── customer_support_tickets.csv
│   └── tickets.db
│
├── knowledge/
│   ├── domains/
│   ├── subdomains/
│   ├── products/
│   ├── cross/
│   ├── taxonomies/
│   └── templates/
│
├── src/
│   ├── agents/
│   ├── rag/
│   ├── db/
│   ├── utils/
│   └── llm/
│
├── main.py
├── requirements.txt
├── .env
└── README.md
```

---

## ⚙️ Setup

### 1. Create virtual environment

```
python -m venv .venv
```

### 2. Activate environment

```
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_key_here
HF_API_KEY=your_key_here
```

---

## 📦 Dependency Management

To update dependencies:

```
pip freeze > requirements.txt
```

This stores an exact snapshot of the current environment.

---

## 🚀 Project Status

🚧 In development

Next steps:

* Implement Router Agent
* Integrate hybrid RAG (metadata + semantic search)
* Orchestrate agents using LangGraph
* Add evaluation and logging

---

## 🧠 Goal

Build a scalable and modular system that simulates human-like decision-making in customer support workflows.
