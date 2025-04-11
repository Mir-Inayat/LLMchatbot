import os
from dotenv import load_dotenv
from backend.models.llm_handler import LLMHandler

def test_llm():
    print("=== Testing LLM Connection ===")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize LLM handler
    print("Initializing LLM handler...")
    llm_handler = LLMHandler()
    
    # Check if using mock or real LLM
    if llm_handler.use_mock:
        print("Using mock LLM (no valid Gemini API key found)")
    else:
        print(f"Using Gemini model: {llm_handler.model_name}")
    
    # Test connection
    print("\nTesting direct connection...")
    connection_result = llm_handler.test_connection()
    print(f"Connection test result: {'Success' if connection_result else 'Failed'}")
    
    # Test a simple query
    print("\nTesting simple query...")
    test_query = "What is cybersecurity?"
    print(f"Query: '{test_query}'")
    
    response = llm_handler.get_llm_response(test_query)
    print("\nResponse:")
    print(response)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_llm()