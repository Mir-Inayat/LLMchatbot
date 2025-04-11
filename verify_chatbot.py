import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.knowledge_graph.neo4j_client import Neo4jClient
from backend.models.llm_handler import LLMHandler
from backend.rag.retrieval_pipeline import RAGPipeline

def main():
    print("=== Cybersecurity Chatbot Verification ===")
    load_dotenv()
    
    # Step 1: Verify Neo4j connection
    print("\nVerifying Neo4j connection...")
    try:
        neo4j_client = Neo4jClient()
        if neo4j_client.test_connection():
            print("✅ Neo4j connection successful")
            
            # Check if the cybersecurity data exists
            query = """
            MATCH (i:Incident) RETURN count(i) as count
            """
            result = neo4j_client.execute_query(query)
            incident_count = result[0]["count"] if result else 0
            
            if incident_count > 0:
                print(f"✅ Cybersecurity knowledge graph is populated ({incident_count} incidents found)")
            else:
                print("❌ Cybersecurity knowledge graph is empty. Please run 'python run.py --load-kg' first")
                return
        else:
            print("❌ Neo4j connection failed. Please check your connection settings")
            return
    except Exception as e:
        print(f"❌ Neo4j error: {e}")
        return
    
    # Step 2: Set up LLM handler (with graceful fallback to mock)
    print("\nSetting up LLM handler...")
    try:
        llm_handler = LLMHandler()
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if not gemini_key:
            print("⚠️ No Gemini API key found in environment variables.")
            print("   Will use Mock LLM for testing.")
            print("   To use Gemini, set GEMINI_API_KEY in your .env file.")
        else:
            print(f"Found Gemini API key. Will attempt to use model: {os.getenv('GEMINI_MODEL_NAME', 'gemini-pro')}")
            
            # Test connection only if we have an API key
            print("Testing Gemini API connection...")
            connection_ok = llm_handler.test_connection()
            
            if connection_ok:
                print("✅ Gemini API connection successful")
            else:
                print("❌ Gemini API connection failed. Will fall back to Mock LLM.")
                print("   - Check your Gemini API key")
                print("   - Verify the model name is correct")
                print("   - Ensure you have internet connectivity")
                # Force use of mock LLM
                llm_handler.use_mock = True
    except Exception as e:
        print(f"❌ Error setting up LLM handler: {e}")
        print("   Will create a new handler with Mock LLM")
        # Create new handler with Mock LLM only
        llm_handler = LLMHandler()
        llm_handler.use_mock = True
    
    # Step 3: Test RAG pipeline with a sample query
    print("\nTesting RAG pipeline with a sample query...")
    try:
        rag_pipeline = RAGPipeline(neo4j_client=neo4j_client, llm_handler=llm_handler)
        
        sample_query = "What are the most common cybersecurity threats?"
        print(f"Query: '{sample_query}'")
        
        print("Processing query (this may take a moment)...")
        result = rag_pipeline.process_query(query=sample_query)
        
        if result and "answer" in result and result["answer"]:
            print("✅ RAG pipeline successfully processed the query")
            print("\nSample response summary:")
            print(f"- Answer length: {len(result['answer'])} characters")
            print(f"- Sources: {len(result.get('sources', []))} context items used")
            graph_available = result.get('graph_data') and len(result['graph_data'].get('nodes', [])) > 0
            print(f"- Graph data: {'Available' if graph_available else 'Not available'}")
            
            print("\nSample answer snippet:")
            answer_preview = result["answer"][:150] + "..." if len(result["answer"]) > 150 else result["answer"]
            print(f"\"{answer_preview}\"")
        else:
            print("❌ RAG pipeline failed to process the query properly")
            if result:
                print(f"Result: {result}")
            return
    except Exception as e:
        print(f"❌ RAG pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Final confirmation
    print("\n=== Verification Complete ===")
    print("The chatbot appears to be functioning correctly.")
    print("\nTo run the chatbot:")
    print("1. Start the backend: python run.py")
    print("2. In a separate terminal, start the frontend: cd frontend && npm start")
    print("\nThe chatbot will be available at http://localhost:3000")

if __name__ == "__main__":
    main()
