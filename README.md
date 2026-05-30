# LLMChatbot — Cybersecurity RAG Chatbot with Knowledge Graph

> A domain-specific AI chatbot for cybersecurity Q&A, combining a **Neo4j knowledge graph** with a **Retrieval-Augmented Generation (RAG)** pipeline for context-aware, verifiable answers.

![Python](https://img.shields.io/badge/Python-0d1117?style=flat-square&logo=python&logoColor=58a6ff)
![React](https://img.shields.io/badge/React-0d1117?style=flat-square&logo=react&logoColor=61dafb)
![Neo4j](https://img.shields.io/badge/Neo4j-0d1117?style=flat-square&logo=neo4j&logoColor=4db33d)
![LLM](https://img.shields.io/badge/Gemini_LLM-0d1117?style=flat-square&logo=google&logoColor=white)

---

## What it does

LLMChatbot goes far beyond a generic chatbot. Instead of relying solely on an LLM's training data, it queries a structured **Neo4j cybersecurity knowledge graph** to retrieve factual, up-to-date threat intelligence, then feeds it into a large language model to produce grounded, citation-rich answers.

**Example queries:**
- *"What are the top attack vectors targeting the finance sector in 2024?"*
- *"Show me recent vulnerabilities affecting the UK energy grid."*
- The system retrieves the relevant subgraph, visualizes it in the UI, and generates a structured natural-language answer.

---

## Architecture

```
User Query (React Chat Interface)
         ↓
  NER + Embedding Extraction
         ↓
  Neo4j Knowledge Graph Query
  (Countries → Industries → AttackTypes → Vulnerabilities → Defenses)
         ↓
  Subgraph Retrieval + Semantic Search
         ↓
  LLM (Google Gemini / Mock LLM) — RAG-augmented response
         ↓
  Answer + Graph Visualization (React Frontend)
```

---

## Key Components

### Knowledge Graph (`backend/knowledge_graph/`)
- Built on **Neo4j** with a rich cybersecurity schema
- Node types: `Countries`, `AttackTypes`, `Industries`, `AttackSources`, `Vulnerabilities`, `Defenses`, `Incidents`, `Years`
- Loaded via `cybersecurity_kg_loader.py` from structured CSV threat intelligence datasets
- Unique constraints + indexes for query performance

### RAG Pipeline (`backend/rag/retrieval_pipeline.py`)
- **Query Understanding** — Named Entity Recognition (NER) extracts key terms
- **Knowledge Retrieval** — Semantic + keyword Cypher queries identify the most relevant subgraph
- **Answer Generation** — LLM synthesizes a natural-language response, grounded in graph facts
- **Graph Packaging** — Relevant nodes and relationships are serialized for frontend visualization

### Frontend (`frontend/src/components/`)
- `ChatInterface.jsx` — Conversational UI with streaming responses
- `AboutSection.jsx` — Explains the knowledge graph architecture to users
- Live subgraph visualization rendered alongside each answer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python (83.5%) |
| Knowledge Graph | Neo4j + Cypher |
| LLM | Google Gemini (configurable) |
| NER & Embeddings | Python NLP pipeline |
| Frontend | React + JavaScript + CSS |
| Deployment | FastAPI / local server |

---

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
# Configure Neo4j connection in .env
python knowledge_graph/cybersecurity_kg_loader.py  # load graph data
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

Set credentials in `.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
GEMINI_API_KEY=your_key
```

---

## Related Projects

This chatbot's RAG pipeline architecture directly informed the multi-agent orchestration design in **[SmartDocMate](https://github.com/Mir-Inayat/inferno)** and **AuditIQ** (Deloitte Hacksplosion 2026 winner).
