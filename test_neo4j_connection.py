import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def test_neo4j_connection():
    """Test the Neo4j connection with detailed error reporting."""
    load_dotenv()
    
    # Get connection details
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER"))
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    neo4j_database = os.getenv("NEO4J_DATABASE")
    
    print(f"Attempting to connect to Neo4j at: {neo4j_uri}")
    print(f"Using user: {neo4j_user}")
    print(f"Database: {neo4j_database}")
    
    try:
        # For neo4j+s:// URIs, don't set encrypted explicitly
        driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        
        with driver.session(database=neo4j_database) as session:
            result = session.run("RETURN 1 AS test")
            test_result = result.single()["test"]
            
            if test_result == 1:
                print("✅ Connection successful!")
                return True
            else:
                print("❌ Connection failed: unexpected test result")
                return False
                
    except Exception as e:
        print(f"❌ Connection failed with error: {str(e)}")
        if "Unable to connect" in str(e):
            print("\nTroubleshooting tips:")
            print("1. Verify that the Aura instance is available")
            print("2. Wait 60 seconds after starting a new Aura instance before connecting")
            print("3. Make sure your network allows outbound connections to Neo4j Aura")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    test_neo4j_connection()