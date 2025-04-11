#!/usr/bin/env python
"""
Utility script to diagnose and fix issues with the Neo4j knowledge graph.
"""
import os
import sys
import time
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.knowledge_graph.neo4j_client import Neo4jClient
from backend.knowledge_graph.cybersecurity_kg_loader import CybersecurityKGLoader

def diagnose_neo4j_connection():
    """Diagnose Neo4j connection issues."""
    # Load environment variables
    load_dotenv()
    
    # Get Neo4j connection details from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    print("\n=== Neo4j Connection Diagnostics ===")
    print(f"URI: {neo4j_uri}")
    print(f"User: {neo4j_user}")
    print(f"Password: {'*' * len(neo4j_password)}")
    print(f"Database: {neo4j_database}")
    
    # Initialize Neo4j client
    client = Neo4jClient()
    
    # Test connection
    print("\nTesting Neo4j connection...")
    start_time = time.time()
    connection_success = client.test_connection()
    end_time = time.time()
    
    if connection_success:
        print(f"✅ Connection successful! (took {end_time - start_time:.2f} seconds)")
    else:
        print(f"❌ Connection failed! (after {end_time - start_time:.2f} seconds)")
        print("\nPossible issues:")
        print("1. Neo4j server is not running")
        print("2. Incorrect URI, username, or password")
        print("3. Network connectivity issues")
        print("4. Database doesn't exist")
        print("\nTo fix:")
        print("- Check if Neo4j is running (try accessing Neo4j Browser)")
        print("- Verify credentials in your .env file or environment variables")
        print("- Make sure the database exists and is accessible")
        return client, False
    
    return client, True

def check_schema_health(client):
    """Check if the knowledge graph schema is properly set up."""
    print("\n=== Schema Health Check ===")
    
    # Check constraints
    constraint_query = "SHOW CONSTRAINTS"
    constraints = client.execute_query(constraint_query)
    
    # Check indexes
    index_query = "SHOW INDEXES"
    indexes = client.execute_query(index_query)
    
    if not constraints:
        print("❌ No constraints found in the database.")
        return False
    
    if not indexes:
        print("❌ No indexes found in the database.")
        return False
    
    print(f"✅ Found {len(constraints)} constraints and {len(indexes)} indexes.")
    
    # Check for required node types
    node_types = [
        "Country", "Year", "AttackType", "Industry", 
        "AttackSource", "Vulnerability", "Defense", "Incident"
    ]
    
    for node_type in node_types:
        count_query = f"MATCH (n:{node_type}) RETURN count(n) as count"
        result = client.execute_query(count_query)
        count = result[0]['count'] if result else 0
        
        if count > 0:
            print(f"✅ {node_type} nodes: {count} found")
        else:
            print(f"❌ No {node_type} nodes found")
    
    # Check for relationships
    rel_query = "CALL db.schema.visualization()"
    schema = client.execute_query(rel_query)
    
    if schema and len(schema) > 0:
        relationships = set()
        if 'relationships' in schema[0]:
            for rel in schema[0]['relationships']:
                if 'type' in rel:
                    relationships.add(rel['type'])
        
        if relationships:
            print(f"✅ Found relationship types: {', '.join(relationships)}")
            return True
        else:
            print("❌ No relationships found in the schema.")
            return False
    else:
        print("❌ Could not retrieve schema information.")
        return False

def fix_knowledge_graph():
    """Fix issues with the knowledge graph."""
    # First diagnose connection
    client, connection_ok = diagnose_neo4j_connection()
    if not connection_ok:
        return
    
    # Check if schema is healthy
    schema_ok = check_schema_health(client)
    
    # Initialize loader
    loader = CybersecurityKGLoader(client)
    
    if not schema_ok:
        print("\n=== Schema Fix ===")
        print("Creating schema for cybersecurity knowledge graph...")
        
        schema_created = loader.load_cybersecurity_threats_schema()
        if schema_created:
            print("✅ Successfully created schema.")
        else:
            print("❌ Failed to create schema.")
            return
    
    # Check if data exists
    data_exists = loader.cybersecurity_threats_data_exists()
    
    if not data_exists:
        print("\n=== Data Loading ===")
        print("No cybersecurity data found. Loading from CSV...")
        
        csv_path = os.path.join("data", "raw", "Global_Cybersecurity_Threats_2015-2024.csv")
        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found at {csv_path}")
            return
        
        print(f"Loading data from {csv_path}...")
        success = loader.load_from_csv(csv_path)
        
        if success:
            print("✅ Successfully loaded cybersecurity knowledge graph.")
        else:
            print("❌ Failed to load cybersecurity knowledge graph.")
    else:
        print("\n=== Data Check ===")
        print("✅ Cybersecurity data already exists in the database.")
        
        # Check data completeness
        count_query = "MATCH (i:Incident) RETURN count(i) as count"
        result = client.execute_query(count_query)
        count = result[0]['count'] if result else 0
        
        if count > 0:
            print(f"✅ Found {count} incident nodes.")
        else:
            print("❓ Incident nodes reported to exist, but count returned zero.")
    
    # Verify knowledge graph health
    print("\n=== Knowledge Graph Health Summary ===")
    if schema_ok and (data_exists or success):
        print("✅ The knowledge graph appears to be healthy now.")
        print("\nYou can now run:")
        print("  python run.py")
        print("to start the application with a healthy knowledge graph.")
    else:
        print("❌ There are still issues with the knowledge graph.")
        print("  Please review the diagnostic information above.")
    
    # Close connection
    client.close()

if __name__ == "__main__":
    fix_knowledge_graph()