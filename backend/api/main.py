import os
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

# Import custom modules
from backend.models.llm_handler import LLMHandler
from backend.knowledge_graph.neo4j_client import Neo4jClient
from backend.rag.retrieval_pipeline import RAGPipeline

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Cybersecurity Domain Chatbot",
    description="A domain-specific chatbot for cybersecurity using LLMs and Knowledge Graphs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
@app.on_event("startup")
async def startup_event():
    app.state.neo4j_client = Neo4jClient()
    app.state.llm_handler = LLMHandler()
    app.state.rag_pipeline = RAGPipeline(
        neo4j_client=app.state.neo4j_client,
        llm_handler=app.state.llm_handler
    )

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "neo4j_client"):
        app.state.neo4j_client.close()

# Request and response models
class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None
    graph_data: Optional[Dict[str, Any]] = None

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Cybersecurity Chatbot API is running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Process the user query through the RAG pipeline
        result = app.state.rag_pipeline.process_query(
            query=request.query,
            chat_history=request.history
        )
        
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources"),
            graph_data=result.get("graph_data")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    # Perform health checks for all components
    health_status = {
        "api": "healthy",
        "knowledge_graph": "unhealthy",
        "llm": "unhealthy"
    }
    
    # Create components if they don't exist (for testing purposes)
    if not hasattr(app.state, "neo4j_client"):
        app.state.neo4j_client = Neo4jClient()
        
    if not hasattr(app.state, "llm_handler"):
        app.state.llm_handler = LLMHandler()
    
    # Check Neo4j connection
    if app.state.neo4j_client.test_connection():
        health_status["knowledge_graph"] = "healthy"
        
    # Check LLM availability
    if app.state.llm_handler.test_connection():
        health_status["llm"] = "healthy"
    
    return health_status

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)