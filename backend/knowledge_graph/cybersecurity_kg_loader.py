"""
Utilities for loading and managing the cybersecurity knowledge graph.
"""
import os
import json
import csv
import pandas as pd
import subprocess
from pathlib import Path
from .neo4j_client import Neo4jClient

class CybersecurityKGLoader:
    """Class to handle loading and setup of the cybersecurity knowledge graph."""
    
    def __init__(self, neo4j_client: Neo4jClient):
        """Initialize with a Neo4j client instance."""
        self.client = neo4j_client
        
    def setup_cybersecurity_schema(self) -> bool:
        """Set up the necessary schema for the cybersecurity KG."""
        return self.client.create_cybersecurity_schema()
    
    def load_from_json(self, json_path: str) -> bool:
        """
        Load cybersecurity data from JSON file into Neo4j.
        
        Args:
            json_path: Path to the JSON file containing cybersecurity data
            
        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(json_path):
                print(f"Error: JSON file not found at {json_path}")
                return False
                
            # Read the JSON data line by line (BloodHound format)
            nodes = []
            relationships = []
            
            with open(json_path, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            item = json.loads(line.strip())
                            if item.get('type') == 'node':
                                nodes.append(item)
                            elif item.get('type') == 'relationship':
                                relationships.append(item)
                        except json.JSONDecodeError:
                            print(f"Warning: Could not parse line as JSON: {line[:50]}...")
            
            print(f"Loaded {len(nodes)} nodes and {len(relationships)} relationships from {json_path}")
            
            # Process nodes by label
            self._process_nodes_by_type(nodes)
            
            # Process relationships
            self._process_relationships(relationships)
            
            return True
            
        except Exception as e:
            print(f"Error loading data from JSON: {e}")
            return False

    def _process_nodes_by_type(self, nodes: list) -> None:
        """Process and create nodes by their label type."""
        # Group nodes by their first label
        nodes_by_label = {}
        for node in nodes:
            if 'labels' in node and node['labels']:
                label = node['labels'][0]
                if label not in nodes_by_label:
                    nodes_by_label[label] = []
                nodes_by_label[label].append(node)
        
        # Process each type of node
        for label, label_nodes in nodes_by_label.items():
            query = f"""
            UNWIND $nodes AS node
            MERGE (n:{label} {{name: node.properties.name}})
            SET n += node.properties
            WITH n, node
            CALL apoc.create.addLabels(n, node.labels) YIELD node as updatedNode
            RETURN count(updatedNode)
            """
            
            try:
                self.client.execute_query(query, {"nodes": label_nodes})
                print(f"Created {len(label_nodes)} {label} nodes")
            except Exception as e:
                # If APOC is not available, try a simpler approach without additional labels
                print(f"Warning: APOC not available or error occurred: {e}")
                simpler_query = f"""
                UNWIND $nodes AS node
                MERGE (n:{label} {{name: node.properties.name}})
                SET n += node.properties
                """
                self.client.execute_query(simpler_query, {"nodes": label_nodes})
                print(f"Created {len(label_nodes)} {label} nodes (without additional labels)")
    
    def _process_relationships(self, relationships: list) -> None:
        """Process and create relationships."""
        if not relationships:
            return
        
        # Group relationships by type
        rels_by_type = {}
        for rel in relationships:
            rel_type = rel.get('label', 'RELATED_TO')
            if rel_type not in rels_by_type:
                rels_by_type[rel_type] = []
            rels_by_type[rel_type].append(rel)
        
        # Process each type of relationship
        for rel_type, type_rels in rels_by_type.items():
            # Create a more flexible query that works with node IDs from the JSON
            query = f"""
            UNWIND $relationships AS rel
            MATCH (source) WHERE id(source) = rel.start.id
            MATCH (target) WHERE id(target) = rel.end.id
            MERGE (source)-[r:{rel_type}]->(target)
            """
            
            # Add properties if present
            query += """
            WITH r, rel
            WHERE rel.properties IS NOT NULL
            SET r += rel.properties
            """
            
            try:
                self.client.execute_query(query, {"relationships": type_rels})
                print(f"Created {len(type_rels)} {rel_type} relationships")
            except Exception as e:
                print(f"Error creating {rel_type} relationships: {e}")
                # Try an alternative approach for relationships
                for rel in type_rels:
                    try:
                        alt_query = f"""
                        MATCH (source) WHERE id(source) = {rel['start']['id']}
                        MATCH (target) WHERE id(target) = {rel['end']['id']}
                        MERGE (source)-[r:{rel_type}]->(target)
                        """
                        if 'properties' in rel and rel['properties']:
                            props_str = ', '.join([f"{k}: ${k}" for k in rel['properties'].keys()])
                            alt_query += f"\nSET r = {{{props_str}}}"
                            self.client.execute_query(alt_query, rel['properties'])
                        else:
                            self.client.execute_query(alt_query)
                    except Exception as inner_e:
                        print(f"Error creating individual relationship: {inner_e}")

    def load_from_dump(self, dump_path: str, neo4j_admin_path: str = None, database: str = None) -> bool:
        """
        Load cybersecurity data from a Neo4j dump file.
        
        Args:
            dump_path: Path to the Neo4j dump file
            neo4j_admin_path: Path to the neo4j-admin executable (optional)
            database: Name of the database to load data into (default is the one in the client)
            
        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(dump_path):
                print(f"Error: Dump file not found at {dump_path}")
                return False
            
            # If database is not specified, use the client's database
            if database is None:
                database = self.client.database
            
            # If neo4j_admin_path is not specified, try to find it
            if neo4j_admin_path is None:
                # Common paths for neo4j-admin
                common_paths = [
                    "/usr/bin/neo4j-admin",
                    "/usr/local/bin/neo4j-admin",
                    "C:\\Program Files\\Neo4j\\bin\\neo4j-admin.bat",
                    "C:\\Program Files\\Neo4j CE\\bin\\neo4j-admin.bat"
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        neo4j_admin_path = path
                        break
            
            if neo4j_admin_path is None or not os.path.exists(neo4j_admin_path):
                print("Error: neo4j-admin executable not found. Please specify the path.")
                return False
            
            # Build the command
            command = [
                neo4j_admin_path,
                "load",
                "--from", dump_path,
                "--database", database,
                "--force"  # Be careful with this option
            ]
            
            # Execute the command
            print(f"Running command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error loading dump file: {result.stderr}")
                return False
            
            print(f"Successfully loaded dump file: {result.stdout}")
            return True
            
        except Exception as e:
            print(f"Error loading data from dump file: {e}")
            return False
    
    def load_cypher_file(self, cypher_file_path: str) -> bool:
        """
        Execute Cypher statements from a file.
        
        Args:
            cypher_file_path: Path to the file containing Cypher statements
            
        Returns:
            bool: True if execution was successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(cypher_file_path):
                print(f"Error: Cypher file not found at {cypher_file_path}")
                return False
            
            # Read the file
            with open(cypher_file_path, 'r') as f:
                cypher_script = f.read()
            
            # Split by semicolon to get individual statements, ignoring empty ones
            statements = [stmt.strip() for stmt in cypher_script.split(';') if stmt.strip()]
            
            # Execute each statement
            for statement in statements:
                self.client.execute_query(statement)
            
            return True
            
        except Exception as e:
            print(f"Error executing Cypher file: {e}")
            return False
    
    def sample_data_exists(self) -> bool:
        """Check if the cybersecurity data is already loaded."""
        query = """
        MATCH (n:User) RETURN count(n) as count
        """
        result = self.client.execute_query(query)
        
        # If there are any users, assume data exists
        if result and result[0]['count'] > 0:
            return True
        return False
    
    def load_cybersecurity_threats_schema(self) -> bool:
        """Create schema for cybersecurity threats knowledge graph."""
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
            with self.client.driver.session(database=self.client.database) as session:
                for query in constraints + indexes:
                    session.run(query)
        except Exception as e:
            print(f"Error creating schema: {e}")
            success = False
        
        return success
    
    def load_from_csv(self, csv_path: str) -> bool:
        """
        Load cybersecurity threats data from CSV into Neo4j.
        
        Args:
            csv_path: Path to the CSV file
        
        Returns:
            bool: True if loading was successful, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(csv_path):
                print(f"Error: CSV file not found at {csv_path}")
                return False
            
            # Read the CSV file
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} incidents from CSV")
            
            # Create schema
            self.load_cybersecurity_threats_schema()
            
            # Create nodes for each entity type
            self._create_entity_nodes(df)
            
            # Create incident nodes and relationships
            self._create_incidents_and_relationships(df)
            
            print("Finished loading cybersecurity threats knowledge graph")
            return True
            
        except Exception as e:
            print(f"Error loading data from CSV: {e}")
            return False
    
    def _create_entity_nodes(self, df: pd.DataFrame) -> None:
        """Create nodes for each entity type in the dataset."""
        # Create Country nodes
        countries = df['Country'].unique().tolist()
        countries_query = """
        UNWIND $countries AS country
        MERGE (c:Country {name: country})
        """
        self.client.execute_query(countries_query, {"countries": countries})
        print(f"Created {len(countries)} Country nodes")
        
        # Create Year nodes
        years = df['Year'].unique().tolist()
        years_query = """
        UNWIND $years AS year
        MERGE (y:Year {value: year})
        """
        self.client.execute_query(years_query, {"years": years})
        print(f"Created {len(years)} Year nodes")
        
        # Create AttackType nodes
        attack_types = df['Attack Type'].unique().tolist()
        attack_types_query = """
        UNWIND $attackTypes AS attackType
        MERGE (a:AttackType {name: attackType})
        """
        self.client.execute_query(attack_types_query, {"attackTypes": attack_types})
        print(f"Created {len(attack_types)} AttackType nodes")
        
        # Create Industry nodes
        industries = df['Target Industry'].unique().tolist()
        industries_query = """
        UNWIND $industries AS industry
        MERGE (i:Industry {name: industry})
        """
        self.client.execute_query(industries_query, {"industries": industries})
        print(f"Created {len(industries)} Industry nodes")
        
        # Create AttackSource nodes
        sources = df['Attack Source'].unique().tolist()
        sources_query = """
        UNWIND $sources AS source
        MERGE (s:AttackSource {name: source})
        """
        self.client.execute_query(sources_query, {"sources": sources})
        print(f"Created {len(sources)} AttackSource nodes")
        
        # Create Vulnerability nodes
        vulnerabilities = df['Security Vulnerability Type'].unique().tolist()
        vulnerabilities_query = """
        UNWIND $vulnerabilities AS vulnerability
        MERGE (v:Vulnerability {name: vulnerability})
        """
        self.client.execute_query(vulnerabilities_query, {"vulnerabilities": vulnerabilities})
        print(f"Created {len(vulnerabilities)} Vulnerability nodes")
        
        # Create Defense nodes
        defenses = df['Defense Mechanism Used'].unique().tolist()
        defenses_query = """
        UNWIND $defenses AS defense
        MERGE (d:Defense {name: defense})
        """
        self.client.execute_query(defenses_query, {"defenses": defenses})
        print(f"Created {len(defenses)} Defense nodes")
    
    def _create_incidents_and_relationships(self, df: pd.DataFrame) -> None:
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
            
            self.client.execute_query(query, {"incidents": batch})
            print(f"Created {len(batch)} Incident nodes with relationships")

        # Create additional relationship between attack types and vulnerabilities
        attack_vulnerability_query = """
        MATCH (a:AttackType)<-[:USED_ATTACK]-(i:Incident)-[:EXPLOITED]->(v:Vulnerability)
        WITH a, v, count(i) AS frequency
        MERGE (a)-[r:EXPLOITS]->(v)
        SET r.frequency = frequency
        """
        self.client.execute_query(attack_vulnerability_query)
        
        # Create relationship between countries and attack sources
        country_source_query = """
        MATCH (c:Country)<-[:OCCURRED_IN]-(i:Incident)-[:ORIGINATED_FROM]->(s:AttackSource)
        WITH c, s, count(i) AS frequency
        MERGE (c)-[r:EXPERIENCED_ATTACKS_FROM]->(s)
        SET r.frequency = frequency
        """
        self.client.execute_query(country_source_query)
        
        # Create relationship between defense mechanisms and vulnerabilities
        defense_vulnerability_query = """
        MATCH (d:Defense)<-[:DEFENDED_WITH]-(i:Incident)-[:EXPLOITED]->(v:Vulnerability)
        WITH d, v, count(i) AS frequency
        MERGE (d)-[r:PROTECTS_AGAINST]->(v)
        SET r.frequency = frequency
        """
        self.client.execute_query(defense_vulnerability_query)
    
    def cybersecurity_threats_data_exists(self) -> bool:
        """Check if the cybersecurity threats data is already loaded."""
        query = """
        MATCH (i:Incident) RETURN count(i) as count
        """
        result = self.client.execute_query(query)
        
        # If there are any incidents, assume data exists
        if result and result[0]['count'] > 0:
            return True
        return False
    
    def get_common_cybersecurity_queries(self) -> list:
        """Return a list of common Cypher queries for the cybersecurity threats KG."""
        return [
            {
                "name": "Top Attack Types by Financial Loss",
                "query": """
                MATCH (a:AttackType)<-[:USED_ATTACK]-(i:Incident)
                WITH a.name AS attackType, sum(i.financial_loss) AS totalLoss
                RETURN attackType, totalLoss
                ORDER BY totalLoss DESC
                LIMIT 10
                """
            },
            {
                "name": "Most Targeted Industries",
                "query": """
                MATCH (i:Industry)<-[:TARGETED]-(incident:Incident)
                WITH i.name AS industry, count(incident) AS incidents
                RETURN industry, incidents
                ORDER BY incidents DESC
                """
            },
            {
                "name": "Most Common Vulnerabilities by Country",
                "query": """
                MATCH (c:Country)<-[:OCCURRED_IN]-(i:Incident)-[:EXPLOITED]->(v:Vulnerability)
                WITH c.name AS country, v.name AS vulnerability, count(*) AS frequency
                ORDER BY country, frequency DESC
                RETURN country, collect({vulnerability: vulnerability, frequency: frequency})[0..3] AS topVulnerabilities
                """
            },
            {
                "name": "Most Effective Defense Mechanisms",
                "query": """
                MATCH (d:Defense)<-[:DEFENDED_WITH]-(i:Incident)
                WITH d.name AS defense, avg(i.resolution_time) AS avgResolutionTime
                RETURN defense, avgResolutionTime
                ORDER BY avgResolutionTime ASC
                LIMIT 5
                """
            },
            {
                "name": "Attack Trends Over Time",
                "query": """
                MATCH (y:Year)<-[:HAPPENED_IN]-(i:Incident)-[:USED_ATTACK]->(a:AttackType)
                WITH y.value AS year, a.name AS attackType, count(*) AS attacks
                ORDER BY year, attacks DESC
                RETURN year, collect({attackType: attackType, count: attacks})[0..3] AS topAttacks
                ORDER BY year
                """
            },
            {
                "name": "Countries Most Targeted by Nation-states",
                "query": """
                MATCH (c:Country)<-[:OCCURRED_IN]-(i:Incident)-[:ORIGINATED_FROM]->(s:AttackSource {name: 'Nation-state'})
                WITH c.name AS country, count(i) AS incidents
                RETURN country, incidents
                ORDER BY incidents DESC
                LIMIT 10
                """
            }
        ]