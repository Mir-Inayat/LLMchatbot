"""
Neo4j setup and verification script.
This script helps with:
1. Checking if Neo4j is running
2. Setting up Neo4j if needed
3. Creating constraints and loading data
"""
import os
import sys
import time
import subprocess
import platform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_neo4j_running():
    """Check if Neo4j is running by attempting a connection."""
    from backend.knowledge_graph.neo4j_client import Neo4jClient
    
    client = Neo4jClient()
    return client.test_connection()

def start_neo4j():
    """Attempt to start Neo4j service."""
    system = platform.system()
    
    if system == "Windows":
        print("Attempting to start Neo4j service on Windows...")
        try:
            # Try to start the Neo4j Windows service
            subprocess.run(['net', 'start', 'neo4j'], check=True)
            print("Neo4j service started successfully.")
            return True
        except subprocess.CalledProcessError:
            print("Could not start Neo4j as a Windows service.")
            
            # Try to find Neo4j installation and start it
            possible_paths = [
                r'C:\Program Files\Neo4j\Neo4j\bin\neo4j.bat',
                r'C:\Program Files\Neo4j CE\bin\neo4j.bat',
                # Add more possible paths here
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    try:
                        print(f"Found Neo4j at {path}, attempting to start...")
                        subprocess.run([path, 'start'], check=True)
                        print("Neo4j started successfully.")
                        return True
                    except subprocess.CalledProcessError:
                        print(f"Failed to start Neo4j using {path}")
            
            print("\nCouldn't automatically start Neo4j. Please:")
            print("1. Open Neo4j Desktop if installed")
            print("2. Start your database")
            print("3. Run this script again once Neo4j is running")
            return False
    
    elif system == "Linux" or system == "Darwin":  # Darwin is macOS
        print(f"Attempting to start Neo4j service on {system}...")
        try:
            # Try systemctl first (for systemd-based Linux)
            subprocess.run(['systemctl', 'start', 'neo4j'], check=True)
            print("Neo4j service started successfully.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try service command (for non-systemd Linux or macOS)
                subprocess.run(['service', 'neo4j', 'start'], check=True)
                print("Neo4j service started successfully.")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("\nCouldn't automatically start Neo4j. Please:")
                print("1. Start Neo4j manually")
                print("2. Run this script again once Neo4j is running")
                return False
    
    print(f"Unsupported operating system: {system}")
    return False

def setup_neo4j():
    """Set up Neo4j with the correct password and database."""
    from backend.knowledge_graph.neo4j_client import Neo4jClient
    
    # Get credentials from .env
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print(f"Using Neo4j URI: {neo4j_uri}")
    print(f"Using username: {neo4j_user}")
    print(f"Using database: {neo4j_database}")
    
    # Initialize client with default password first to change it if needed
    client = Neo4jClient()
    
    # Check if we can connect with the configured password
    if client.test_connection():
        print("Successfully connected to Neo4j with configured credentials.")
        return True
    
    # If we can't connect, Neo4j might be using the default password
    print("Failed to connect with configured credentials.")
    print("Attempting to connect with default password to change it...")
    
    # Try to initialize with default password
    from neo4j import GraphDatabase
    try:
        # Default Neo4j password is typically 'neo4j'
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, "neo4j"))
        with driver.session() as session:
            # Change password
            session.run(f"ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO '{neo4j_password}'")
            print(f"Successfully changed password for user {neo4j_user}")
        driver.close()
        
        # Now try to connect with the new password
        client = Neo4jClient()
        if client.test_connection():
            print("Successfully connected with new password.")
            return True
    except Exception as e:
        print(f"Error setting up Neo4j: {e}")
    
    print("Failed to set up Neo4j with the correct credentials.")
    return False

def verify_llm_connection():
    """Verify that the LLM API connection is working."""
    from backend.models.llm_handler import LLMHandler
    
    print("\n=== Verifying LLM Connection ===")
    
    try:
        llm_handler = LLMHandler()
        
        # Simple test query
        test_prompt = "Hello, this is a test. Please respond with 'LLM connection successful' if you receive this."
        response = llm_handler.get_llm_response(test_prompt)
        
        if response and "LLM connection successful" in response:
            print("✅ LLM connection verified successfully.")
            return True
        else:
            print("⚠️ LLM connected but returned unexpected response:")
            print(response)
            return True  # Still return True as we got some response
    except Exception as e:
        print(f"❌ LLM connection failed: {e}")
        print("\nPossible issues:")
        print("1. Invalid API key")
        print("2. Network connectivity issues")
        print("3. Rate limiting or quota issues")
        print("\nTo fix:")
        print("- Verify your GEMINI_API_KEY in the .env file")
        print("- Check your network connection")
        print("- Check your API usage and limits")
        return False

def main():
    """Main function to set up and verify the system."""
    print("=== LLMchatbot Setup and Verification ===\n")
    
    # Check if Neo4j is running
    print("Checking if Neo4j is running...")
    if check_neo4j_running():
        print("✅ Neo4j is running.")
    else:
        print("❌ Neo4j is not running.")
        
        # Try to start Neo4j
        if not start_neo4j():
            print("\nPlease start Neo4j manually and run this script again.")
            return
        
        # Wait a bit for Neo4j to start
        print("Waiting for Neo4j to start up...")
        time.sleep(10)
        
        # Check again
        if not check_neo4j_running():
            print("❌ Neo4j still not running after startup attempt.")
            print("Please start Neo4j manually and run this script again.")
            return
    
    # Set up Neo4j with correct credentials
    if not setup_neo4j():
        print("Failed to set up Neo4j with the correct credentials.")
        print("Please verify your Neo4j installation and credentials.")
        return
    
    # Run the knowledge graph fix script
    print("\nRunning knowledge graph diagnostics and setup...")
    from fix_knowledge_graph import fix_knowledge_graph
    fix_knowledge_graph()
    
    # Verify LLM connection
    if not verify_llm_connection():
        print("Failed to verify LLM connection.")
        print("Please check your Gemini API key and network connection.")
        return
    
    print("\n=== Setup and Verification Complete ===")
    print("You can now run your LLMchatbot application:")
    print("  python run.py")

if __name__ == "__main__":
    main()