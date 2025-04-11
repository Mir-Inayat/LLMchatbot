import os
import sys
import argparse

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.knowledge_graph.neo4j_client import Neo4jClient
from backend.knowledge_graph.cybersecurity_kg_loader import CybersecurityKGLoader

def load_cybersecurity_kg():
    """Load the cybersecurity knowledge graph from the CSV data."""
    # Initialize Neo4j client
    client = Neo4jClient()
    
    # Test connection
    if not client.test_connection():
        print("Failed to connect to Neo4j. Please check your connection settings.")
        print("Ensure you have set the following environment variables:")
        print("  - NEO4J_URI (default: bolt://localhost:7687)")
        print("  - NEO4J_USER (default: neo4j)")
        print("  - NEO4J_PASSWORD (default: password)")
        print("  - NEO4J_DATABASE (default: neo4j)")
        return
    
    # Initialize loader
    loader = CybersecurityKGLoader(client)
    
    # Check if data already exists
    if loader.cybersecurity_threats_data_exists():
        print("Cybersecurity threats data already exist in the database.")
        print("If you want to reload the data, please clear the database first.")
        return
    
    # Set up schema first - this is critical for a healthy knowledge graph
    print("Creating schema for cybersecurity knowledge graph...")
    schema_created = loader.load_cybersecurity_threats_schema()
    if not schema_created:
        print("Failed to create schema for cybersecurity knowledge graph.")
        return
    
    # Load CSV data
    csv_path = os.path.join("data", "raw", "Global_Cybersecurity_Threats_2015-2024.csv")
    if not os.path.exists(csv_path):
        print(f"CSV file not found at {csv_path}")
        return
    
    print(f"Loading data from {csv_path}...")
    success = loader.load_from_csv(csv_path)
    
    if success:
        print("Successfully loaded cybersecurity knowledge graph.")
        print("The knowledge graph is now healthy and ready for use.")
        # Print some example queries
        print("\nExample Cypher queries for analysis:")
        for i, query_info in enumerate(loader.get_common_cybersecurity_queries(), 1):
            print(f"\n{i}. {query_info['name']}:")
            print(query_info['query'])
    else:
        print("Failed to load cybersecurity knowledge graph.")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the LLM chatbot with cybersecurity knowledge graph')
    parser.add_argument('--load-kg', action='store_true', help='Load the cybersecurity knowledge graph')
    
    args = parser.parse_args()
    
    if args.load_kg:
        load_cybersecurity_kg()
    else:
        import uvicorn
        # Start the server with app as a string to enable reload
        uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)