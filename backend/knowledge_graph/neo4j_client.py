import os
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

class Neo4jClient:
    """Client for interacting with Neo4j knowledge graph database."""
    
    def __init__(self):
        """Initialize the Neo4j client with connection details from environment variables."""
        load_dotenv()
        
        # Get Neo4j connection details from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USERNAME", os.getenv("NEO4J_USER", "neo4j"))
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        print(f"Initializing Neo4j client with URI: {neo4j_uri}")
        
        # Initialize the driver (encryption is handled automatically by URI scheme)
        self.driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        
        # Set the database to use
        self.database = neo4j_database
        
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            
    def test_connection(self) -> bool:
        """Test if the Neo4j connection is working."""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS test")
                return result.single()["test"] == 1
        except Exception as e:
            print(f"Neo4j connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return the results."""
        if params is None:
            params = {}
            
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, params)
                return [record.data() for record in result]
        except Exception as e:
            print(f"Error executing Neo4j query: {e}")
            return []
            
    def semantic_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a semantic search in the knowledge graph.
        Uses vector similarity if embeddings are available, otherwise falls back to keyword search.
        """
        # Cypher query for semantic search using vector similarity
        cypher_query = """
        CALL db.index.vector.queryNodes('medical-embeddings', $limit, $query)
        YIELD node, score
        WITH node, score
        MATCH (node)-[r]-(related)
        RETURN 
            node.name AS name,
            node.description AS description,
            node.type AS type,
            labels(node) AS labels,
            score,
            collect({
                type: type(r),
                name: related.name,
                description: related.description,
                labels: labels(related)
            }) AS relationships
        ORDER BY score DESC
        LIMIT $limit
        """
        
        # Execute the query
        try:
            results = self.execute_query(cypher_query, {"query": query, "limit": limit})
            
            # If no results from vector search or vector index doesn't exist, fall back to keyword search
            if not results:
                return self.keyword_search(query, limit)
                
            return results
        except Exception as e:
            print(f"Error in semantic search: {e}")
            # Fall back to keyword search
            return self.keyword_search(query, limit)
            
    def keyword_search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform a keyword-based search in the knowledge graph."""
        # Create search terms by splitting the query
        search_terms = " OR ".join([f"node.name CONTAINS '{term}' OR node.description CONTAINS '{term}'" 
                                  for term in query.split() if len(term) > 3])
        
        # Cypher query for keyword search
        cypher_query = f"""
        MATCH (node)
        WHERE {search_terms}
        WITH node, 
             CASE WHEN node.name CONTAINS '{query}' THEN 3
                  WHEN node.description CONTAINS '{query}' THEN 2
                  ELSE 1
             END AS relevance
        MATCH (node)-[r]-(related)
        RETURN 
            node.name AS name,
            node.description AS description,
            node.type AS type,
            labels(node) AS labels,
            relevance AS score,
            collect({{
                type: type(r),
                name: related.name,
                description: related.description,
                labels: labels(related)
            }}) AS relationships
        ORDER BY relevance DESC
        LIMIT $limit
        """
        
        # Execute the query
        return self.execute_query(cypher_query, {"limit": limit})
    
    def get_subgraph_for_entities(self, entity_names: List[str], depth: int = 2) -> Dict[str, Any]:
        """
        Retrieve a subgraph centered around specified entities.
        Returns both nodes and relationships for visualization.
        """
        # Cypher query to get subgraph
        cypher_query = """
        MATCH (n)
        WHERE n.name IN $entity_names
        CALL apoc.path.subgraphAll(n, {maxLevel: $depth})
        YIELD nodes, relationships
        WITH collect(nodes) AS all_nodes, collect(relationships) AS all_rels
        RETURN 
            [node IN apoc.coll.flatten(all_nodes) | {
                id: id(node),
                labels: labels(node),
                properties: properties(node)
            }] AS nodes,
            [rel IN apoc.coll.flatten(all_rels) | {
                id: id(rel),
                type: type(rel),
                source: id(startNode(rel)),
                target: id(endNode(rel)),
                properties: properties(rel)
            }] AS relationships
        """
        
        # Execute the query
        try:
            results = self.execute_query(cypher_query, {"entity_names": entity_names, "depth": depth})
            if results and len(results) > 0:
                return results[0]  # Return the first result which contains nodes and relationships
            return {"nodes": [], "relationships": []}
        except Exception as e:
            print(f"Error getting subgraph: {e}")
            return {"nodes": [], "relationships": []}
            
    def create_healthcare_schema(self):
        """
        Create initial schema constraints and indexes for the healthcare knowledge graph.
        This should be run once when setting up the database.
        """
        # Create constraints to ensure uniqueness
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Treatment) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Medication) REQUIRE m.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Procedure) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:BodyPart) REQUIRE b.name IS UNIQUE"
        ]
        
        # Create indexes for improving search performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Disease) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Symptom) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Treatment) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Medication) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Procedure) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:BodyPart) ON (n.name)"
        ]
        
        # Execute all queries
        try:
            with self.driver.session(database=self.database) as session:
                for query in constraints + indexes:
                    session.run(query)
            return True
        except Exception as e:
            print(f"Error creating schema: {e}")
            return False
            
    def create_vector_index(self, dimension: int = 1536):
        """
        Create a vector index for semantic search.
        This requires Neo4j 5.11+ with vector search capabilities.
        """
        try:
            cypher_query = """
            CALL db.index.vector.createNodeIndex(
              'medical-embeddings',
              'Medical',
              'embedding',
              $dimension,
              'cosine'
            )
            """
            with self.driver.session(database=self.database) as session:
                session.run(cypher_query, {"dimension": dimension})
            return True
        except Exception as e:
            print(f"Error creating vector index: {e}")
            return False
    
    # Cybersecurity-specific methods
    
    def find_rdp_access(self, username: str) -> List[Dict]:
        """Find computers that a user can access via RDP."""
        cypher_query = """
        MATCH (u:User {name: $name})-[:CAN_RDP]->(r) 
        RETURN r.name as computer
        """
        return self.execute_query(cypher_query, {"name": username})
    
    def find_attack_paths(self, target_node: str) -> List[Dict]:
        """Find potential attack paths to a high-value target."""
        cypher_query = """
        MATCH path = shortestPath((u:User)-[:MemberOf|HasSession|AdminTo|CanRDP*1..]->(target))
        WHERE target.name = $target_name AND u.enabled = true
        RETURN 
            [node in nodes(path) | node.name] as path_nodes,
            [rel in relationships(path) | type(rel)] as path_relationships,
            length(path) as path_length
        ORDER BY path_length ASC
        LIMIT 10
        """
        return self.execute_query(cypher_query, {"target_name": target_node})
    
    def find_high_value_targets(self, limit: int = 10) -> List[Dict]:
        """Identify high-value targets in the network based on connections."""
        cypher_query = """
        MATCH (c:Computer)
        WITH c, size((c)<-[:AdminTo]-()) as inAdminCount
        ORDER BY inAdminCount DESC
        LIMIT $limit
        MATCH (c)<-[:AdminTo]-(u:User)
        RETURN 
            c.name as computer_name, 
            inAdminCount as admin_access_count,
            collect(u.name) as admin_users
        ORDER BY admin_access_count DESC
        """
        return self.execute_query(cypher_query, {"limit": limit})
    
    def find_user_group_memberships(self, username: str) -> List[Dict]:
        """Find all groups that a user is a member of."""
        cypher_query = """
        MATCH (u:User {name: $name})-[:MemberOf]->(g:Group)
        RETURN g.name as group_name, g.description as description
        """
        return self.execute_query(cypher_query, {"name": username})
    
    def find_domain_admins(self) -> List[Dict]:
        """Find all domain admin users."""
        cypher_query = """
        MATCH (u:User)-[:MemberOf]->(g:Group)
        WHERE g.name =~ '.*DOMAIN ADMINS.*'
        RETURN u.name as username, u.enabled as enabled, u.description as description
        """
        return self.execute_query(cypher_query)
    
    def find_kerberoastable_accounts(self) -> List[Dict]:
        """Find accounts that are vulnerable to Kerberoasting."""
        cypher_query = """
        MATCH (u:User)
        WHERE u.hasspn = true
        RETURN u.name as username, u.description as description
        """
        return self.execute_query(cypher_query)
    
    def create_cybersecurity_schema(self) -> bool:
        """
        Create initial schema constraints and indexes for the cybersecurity knowledge graph.
        This should be run once when setting up the database.
        """
        # Create constraints to ensure uniqueness
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Computer) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Group) REQUIRE g.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE"
        ]
        
        # Create indexes for improving search performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:User) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Computer) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Group) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Domain) ON (n.name)"
        ]
        
        # Execute all queries
        try:
            with self.driver.session(database=self.database) as session:
                for query in constraints + indexes:
                    session.run(query)
            return True
        except Exception as e:
            print(f"Error creating schema: {e}")
            return False