# LLMChatbot — Conversational AI Interface

> A lightweight conversational chatbot powered by large language models, built for exploring LLM integration patterns and prompt engineering workflows.

![Python](https://img.shields.io/badge/Python-0d1117?style=flat-square&logo=python&logoColor=58a6ff)
![LLM](https://img.shields.io/badge/LLM-0d1117?style=flat-square&logo=openai&logoColor=white)

---

## What it does

LLMChatbot is a Python-based conversational interface that integrates with large language model APIs to enable multi-turn dialogue, context retention, and prompt-driven response generation.

Built as a hands-on exploration of:
- LLM API integration patterns
- Prompt engineering and context window management
- Conversational state handling across turns

---

## Features

- **Multi-turn conversation** — maintains context across the session
- **Configurable system prompts** — easily swap personas or task instructions
- **Lightweight and modular** — minimal dependencies, easy to extend

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python |
| LLM Backend | LLM API (configurable) |
| Interface | CLI |

---

## Setup

```bash
git clone https://github.com/Mir-Inayat/LLMchatbot
cd LLMchatbot
pip install -r requirements.txt
python main.py
```

Set your API key in a `.env` file:
```
API_KEY=your_key_here
```

---

## Part of a broader AI stack

This chatbot was an early exploration that later informed the multi-agent orchestration and LLM pipeline work in [SmartDocMate](https://github.com/Mir-Inayat/inferno) and AuditIQ.
