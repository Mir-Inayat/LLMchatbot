# LLMchatbot for Cybersecurity

A domain-specific chatbot for cybersecurity that combines Large Language Models with a Neo4j Knowledge Graph for informed, contextual responses.

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- Neo4j 4.4+ (local or cloud instance)
- OpenAI API key (optional - a mock LLM is used if not provided)

### Installation

1. Clone the repository
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
```

4. Create a `.env` file using the template:

```bash
cp .env.template .env
```

5. Edit the `.env` file with your credentials:
   - Set your Neo4j database settings
   - Set your OpenAI API key (if you have one)
   - Configure any other settings as needed

### Setting up the Knowledge Graph

The chatbot uses a Neo4j knowledge graph with cybersecurity data. To set up the graph:

```bash
python run.py --load-kg
```

### Verify Everything is Working

To verify that all components are working correctly:

```bash
python verify_chatbot.py
```

This script checks the Neo4j connection, LLM service, and runs a test query.

## Running the Chatbot

1. Start the backend server:

```bash
python run.py
```

2. In a separate terminal, start the frontend:

```bash
cd frontend
npm start
```

3. Visit http://localhost:3000 in your browser to use the chatbot.

## Features

- Cybersecurity-focused responses leveraging a detailed knowledge graph
- Graph visualization of related entities
- Natural language understanding of cybersecurity queries
- Contextual awareness of cybersecurity concepts, threats, and defenses

## Architecture

- Backend: FastAPI with Neo4j database integration
- LLM: OpenAI's models (or built-in mock LLM for testing)
- Knowledge Graph: Neo4j populated with cybersecurity data
- Frontend: React with Material UI components
- RAG Pipeline: Retrieval Augmented Generation workflow