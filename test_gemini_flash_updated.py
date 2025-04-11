import os
from dotenv import load_dotenv
from backend.models.llm_handler import LLMHandler

def test_gemini_flash():
    print("=== Testing Gemini 2.0 Flash Model ===")
    
    # Load environment variables
    load_dotenv()
    
    # Get API key and model name from env
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
    
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    print(f"Using model: {model_name}")
    
    # Initialize LLM handler
    print("\nInitializing LLM handler...")
    try:
        llm_handler = LLMHandler()
        
        # Check if using mock
        if llm_handler.use_mock:
            print("⚠️ Using mock LLM - no valid API key or configuration")
            return False
            
        # Test connection
        print("\nTesting LLM connection...")
        if llm_handler.test_connection():
            print("✅ LLM connection successful!")
            
            # Test a simple query
            print("\nTesting a simple query...")
            test_query = "What is cybersecurity? Answer in one sentence."
            print(f"Query: '{test_query}'")
            
            response = llm_handler.get_llm_response(test_query)
            print("\nResponse:")
            print(response)
            
            if response and "I'm sorry, I encountered an error" not in response:
                print("\n✅ Gemini 2.0 Flash model is working properly!")
                return True
            else:
                print("\n❌ LLM returned an error response")
                return False
        else:
            print("\n❌ LLM connection test failed")
            return False
    except Exception as e:
        print(f"\n❌ Error testing LLM: {e}")
        return False

if __name__ == "__main__":
    test_gemini_flash()