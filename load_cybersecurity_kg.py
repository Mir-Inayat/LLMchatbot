#!/usr/bin/env python
"""
Script to load the cybersecurity threats dataset into a Neo4j knowledge graph.
"""
import os
import csv
import pandas as pd
import sys
from pathlib import Path
from backend.knowledge_graph.neo4j_client import Neo4jClient

# Add more verbose output
def log(message):
    """Print log message and ensure it's flushed immediately"""
    print(message, flush=True)
    sys.stdout.flush()

def create_cybersecurity_threats_schema(client):
    """Create schema for cybersecurity threats knowledge graph."""
    log("Creating schema for cybersecurity knowledge graph...")
    # Create constraints to ensure uniqueness
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:AttackType) REQUIRE a.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:AttackSource) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vulnerability) REQUIRE v.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Defense) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (y:Year) REQUIRE y.value IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE"
    ]
    
    # Create indexes for improving search performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (c:Country) ON (c.name)",
        "CREATE INDEX IF NOT EXISTS FOR (a:AttackType) ON (a.name)",
        "CREATE INDEX IF NOT EXISTS FOR (i:Industry) ON (i.name)",
        "CREATE INDEX IF NOT EXISTS FOR (s:AttackSource) ON (s.name)",
        "CREATE INDEX IF NOT EXISTS FOR (v:Vulnerability) ON (v.name)",
        "CREATE INDEX IF NOT EXISTS FOR (d:Defense) ON (d.name)",
        "CREATE INDEX IF NOT EXISTS FOR (y:Year) ON (y.value)",
        "CREATE INDEX IF NOT EXISTS FOR (i:Incident) ON (i.id)"
    ]
    
    # Execute all queries
    success = True
    try:
        with client.driver.session(database=client.database) as session:
            for query in constraints + indexes:
                session.run(query)
        log("✅ Schema created successfully!")
    except Exception as e:
        log(f"❌ Error creating schema: {e}")
        success = False
    
    return success

def load_cybersecurity_csv(client, csv_path):
    """
    Load cybersecurity threats data from CSV into Neo4j.
    
    Args:
        client: Neo4jClient instance
        csv_path: Path to the CSV file
    """
    # Read the CSV file
    log(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path)
    log(f"✅ Loaded {len(df)} incidents from CSV")
    
    # Create nodes for each entity type
    log("Creating entity nodes...")
    create_entity_nodes(client, df)
    
    # Create incident nodes and relationships
    log("Creating incident nodes and relationships...")
    create_incidents_and_relationships(client, df)
    
    log("✅ Finished loading cybersecurity threats knowledge graph")

def create_entity_nodes(client, df):
    """Create nodes for each entity type in the dataset."""
    # Create Country nodes
    countries = df['Country'].unique().tolist()
    countries_query = """
    UNWIND $countries AS country
    MERGE (c:Country {name: country})
    """
    client.execute_query(countries_query, {"countries": countries})
    log(f"✅ Created {len(countries)} Country nodes")
    
    # Create Year nodes
    years = df['Year'].unique().tolist()
    years_query = """
    UNWIND $years AS year
    MERGE (y:Year {value: year})
    """
    client.execute_query(years_query, {"years": years})
    log(f"✅ Created {len(years)} Year nodes")
    
    # Create AttackType nodes
    attack_types = df['Attack Type'].unique().tolist()
    attack_types_query = """
    UNWIND $attackTypes AS attackType
    MERGE (a:AttackType {name: attackType})
    """
    client.execute_query(attack_types_query, {"attackTypes": attack_types})
    log(f"✅ Created {len(attack_types)} AttackType nodes")
    
    # Create Industry nodes
    industries = df['Target Industry'].unique().tolist()
    industries_query = """
    UNWIND $industries AS industry
    MERGE (i:Industry {name: industry})
    """
    client.execute_query(industries_query, {"industries": industries})
    log(f"✅ Created {len(industries)} Industry nodes")
    
    # Create AttackSource nodes
    sources = df['Attack Source'].unique().tolist()
    sources_query = """
    UNWIND $sources AS source
    MERGE (s:AttackSource {name: source})
    """
    client.execute_query(sources_query, {"sources": sources})
    log(f"✅ Created {len(sources)} AttackSource nodes")
    
    # Create Vulnerability nodes
    vulnerabilities = df['Security Vulnerability Type'].unique().tolist()
    vulnerabilities_query = """
    UNWIND $vulnerabilities AS vulnerability
    MERGE (v:Vulnerability {name: vulnerability})
    """
    client.execute_query(vulnerabilities_query, {"vulnerabilities": vulnerabilities})
    log(f"✅ Created {len(vulnerabilities)} Vulnerability nodes")
    
    # Create Defense nodes
    defenses = df['Defense Mechanism Used'].unique().tolist()
    defenses_query = """
    UNWIND $defenses AS defense
    MERGE (d:Defense {name: defense})
    """
    client.execute_query(defenses_query, {"defenses": defenses})
    log(f"✅ Created {len(defenses)} Defense nodes")

def create_incidents_and_relationships(client, df):
    """Create incident nodes and establish relationships with other entities."""
    # Prepare incident data
    incidents = []
    
    for index, row in df.iterrows():
        incident_id = f"incident-{index}"
        incident = {
            "id": incident_id,
            "financial_loss": float(row['Financial Loss (in Million $)']),
            "affected_users": int(row['Number of Affected Users']),
            "resolution_time": int(row['Incident Resolution Time (in Hours)']),
            "country": row['Country'],
            "year": int(row['Year']),
            "attack_type": row['Attack Type'],
            "industry": row['Target Industry'],
            "attack_source": row['Attack Source'],
            "vulnerability": row['Security Vulnerability Type'],
            "defense": row['Defense Mechanism Used']
        }
        incidents.append(incident)
    
    log(f"Preparing to create {len(incidents)} incident nodes with relationships")
    
    # Create incident nodes and relationships in batches
    batch_size = 100
    for i in range(0, len(incidents), batch_size):
        batch = incidents[i:i+batch_size]
        
        # Create the query for this batch
        query = """
        UNWIND $incidents AS incident
        
        // Create the incident node
        CREATE (i:Incident {
            id: incident.id,
            financial_loss: incident.financial_loss,
            affected_users: incident.affected_users,
            resolution_time: incident.resolution_time
        })
        
        // Connect to country
        WITH i, incident
        MATCH (c:Country {name: incident.country})
        CREATE (i)-[:OCCURRED_IN]->(c)
        
        // Connect to year
        WITH i, incident
        MATCH (y:Year {value: incident.year})
        CREATE (i)-[:HAPPENED_IN]->(y)
        
        // Connect to attack type
        WITH i, incident
        MATCH (a:AttackType {name: incident.attack_type})
        CREATE (i)-[:USED_ATTACK]->(a)
        
        // Connect to industry
        WITH i, incident
        MATCH (ind:Industry {name: incident.industry})
        CREATE (i)-[:TARGETED]->(ind)
        
        // Connect to attack source
        WITH i, incident
        MATCH (s:AttackSource {name: incident.attack_source})
        CREATE (i)-[:ORIGINATED_FROM]->(s)
        
        // Connect to vulnerability
        WITH i, incident
        MATCH (v:Vulnerability {name: incident.vulnerability})
        CREATE (i)-[:EXPLOITED]->(v)
        
        // Connect to defense
        WITH i, incident
        MATCH (d:Defense {name: incident.defense})
        CREATE (i)-[:DEFENDED_WITH]->(d)
        """
        
        client.execute_query(query, {"incidents": batch})
        log(f"✅ Created {len(batch)} Incident nodes with relationships")

    # Create additional relationships
    log("Creating additional relationships between entities...")
    
    # Create additional relationship between attack types and vulnerabilities
    attack_vulnerability_query = """
    MATCH (a:AttackType)<-[:USED_ATTACK]-(i:Incident)-[:EXPLOITED]->(v:Vulnerability)
    WITH a, v, count(i) AS frequency
    MERGE (a)-[r:EXPLOITS]->(v)
    SET r.frequency = frequency
    """
    client.execute_query(attack_vulnerability_query)
    log("✅ Created EXPLOITS relationships between attack types and vulnerabilities")
    
    # Create relationship between countries and attack sources
    country_source_query = """
    MATCH (c:Country)<-[:OCCURRED_IN]-(i:Incident)-[:ORIGINATED_FROM]->(s:AttackSource)
    WITH c, s, count(i) AS frequency
    MERGE (c)-[r:EXPERIENCED_ATTACKS_FROM]->(s)
    SET r.frequency = frequency
    """
    client.execute_query(country_source_query)
    log("✅ Created EXPERIENCED_ATTACKS_FROM relationships between countries and attack sources")
    
    # Create relationship between defense mechanisms and vulnerabilities
    defense_vulnerability_query = """
    MATCH (d:Defense)<-[:DEFENDED_WITH]-(i:Incident)-[:EXPLOITED]->(v:Vulnerability)
    WITH d, v, count(i) AS frequency
    MERGE (d)-[r:PROTECTS_AGAINST]->(v)
    SET r.frequency = frequency
    """
    client.execute_query(defense_vulnerability_query)
    log("✅ Created PROTECTS_AGAINST relationships between defense mechanisms and vulnerabilities")

def check_graph_statistics(client):
    """Run queries to check the knowledge graph statistics."""
    log("\n📊 Knowledge Graph Statistics:")
    
    # Check node counts
    node_counts_query = """
    MATCH (n)
    RETURN labels(n)[0] AS nodeType, count(n) AS count
    ORDER BY count DESC
    """
    results = client.execute_query(node_counts_query)
    log("\nNode counts:")
    for result in results:
        log(f"  - {result['nodeType']}: {result['count']} nodes")
    
    # Check relationship counts
    rel_counts_query = """
    MATCH ()-[r]->()
    RETURN type(r) AS relType, count(r) AS count
    ORDER BY count DESC
    """
    results = client.execute_query(rel_counts_query)
    log("\nRelationship counts:")
    for result in results:
        log(f"  - {result['relType']}: {result['count']} relationships")
    
    # Check a sample incident
    sample_query = """
    MATCH (i:Incident)-[:OCCURRED_IN]->(c:Country)
    MATCH (i)-[:USED_ATTACK]->(a:AttackType)
    MATCH (i)-[:TARGETED]->(ind:Industry)
    RETURN i.id, c.name, a.name, ind.name
    LIMIT 1
    """
    results = client.execute_query(sample_query)
    if results:
        result = results[0]
        log(f"\nSample incident: {result['i.id']}")
        log(f"  - Country: {result['c.name']}")
        log(f"  - Attack Type: {result['a.name']}")
        log(f"  - Target Industry: {result['ind.name']}")

def main():
    """Main function to load the cybersecurity threats dataset."""
    log("🔄 Starting cybersecurity knowledge graph creation process")
    
    # Initialize Neo4j client
    log("Initializing Neo4j client...")
    client = Neo4jClient()
    
    # Test connection
    log("Testing Neo4j connection...")
    if not client.test_connection():
        log("❌ Failed to connect to Neo4j. Please check your connection settings.")
        log("Ensure you have set the following environment variables:")
        log("  - NEO4J_URI (default: bolt://localhost:7687)")
        log("  - NEO4J_USERNAME (default: neo4j)")
        log("  - NEO4J_PASSWORD (default: password)")
        log("  - NEO4J_DATABASE (default: neo4j)")
        return
    
    log("✅ Successfully connected to Neo4j")
    
    # Check if data already exists
    check_query = """
    MATCH (i:Incident) RETURN count(i) as count
    """
    result = client.execute_query(check_query)
    existing_count = result[0]['count'] if result else 0
    
    if existing_count > 0:
        log(f"⚠️ Found {existing_count} existing incident nodes in the database.")
        log("To avoid duplicate data, consider clearing the database before loading again.")
        user_input = input("Continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            log("Operation cancelled by user.")
            client.close()
            return
    
    # Create schema
    if not create_cybersecurity_threats_schema(client):
        log("❌ Failed to create schema. Exiting.")
        client.close()
        return
    
    # Load CSV data
    csv_path = os.path.join("data", "raw", "Global_Cybersecurity_Threats_2015-2024.csv")
    if not os.path.exists(csv_path):
        log(f"❌ CSV file not found at {csv_path}")
        client.close()
        return
    
    load_cybersecurity_csv(client, csv_path)
    
    # Check graph statistics
    check_graph_statistics(client)
    
    # Close connection
    client.close()
    log("✅ Done! Cybersecurity knowledge graph has been successfully created.")

if __name__ == "__main__":
    main()