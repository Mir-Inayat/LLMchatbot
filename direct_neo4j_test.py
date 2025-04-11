import os
from dotenv import load_dotenv
from backend.knowledge_graph.neo4j_client import Neo4jClient

def test_neo4j():
    print("=== Testing Neo4j Connection ===")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Neo4j client
    print("Initializing Neo4j client...")
    try:
        neo4j_client = Neo4jClient()
        
        # Test connection
        print("Testing connection...")
        if neo4j_client.test_connection():
            print("✅ Neo4j connection successful!")
            
            # Check if cybersecurity data exists
            print("\nChecking for cybersecurity data...")
            query = "MATCH (n:Incident) RETURN COUNT(n) as count"
            result = neo4j_client.execute_query(query)
            count = result[0]['count'] if result else 0
            
            print(f"Found {count} incidents in the knowledge graph")
            
            if count > 0:
                print("✅ Knowledge graph is populated with data")
                
                # Get a sample of data
                print("\nSample of knowledge graph data:")
                sample_query = "MATCH (n:Incident) RETURN n.name AS name LIMIT 3"
                sample = neo4j_client.execute_query(sample_query)
                for i, item in enumerate(sample):
                    print(f"{i+1}. {item['name']}")
                    
                return True
            else:
                print("❌ Knowledge graph is empty. You need to load data.")
                return False
        else:
            print("❌ Neo4j connection failed")
            return False
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        return False

if __name__ == "__main__":
    test_neo4j()