import os
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
import re

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
            
    def semantic_search(self, query: str, additional_entities: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a semantic search over the knowledge graph based on the query.
        
        Args:
            query: The user's query
            additional_entities: Additional entities to include in the search
            limit: Maximum number of results to return
            
        Returns:
            List of relevant knowledge graph entities with their properties and relationships
        """
        # Extract keywords from the query for a basic keyword search
        keywords = self._extract_keywords(query)
        
        # Add additional entities if provided
        if additional_entities:
            keywords.extend([entity.lower() for entity in additional_entities if entity])
        
        # Remove duplicates while preserving order
        unique_keywords = []
        for kw in keywords:
            if kw and kw not in unique_keywords and len(kw) > 2:  # Skip very short keywords
                unique_keywords.append(kw)
        
        if not unique_keywords:
            return []
        
        # Construct a Cypher query to find relevant nodes
        cypher_query = """
        // Search for entities matching keywords
        UNWIND $keywords AS keyword
        MATCH (n)
        WHERE (
            // Match on name property
            n.name IS NOT NULL AND toLower(n.name) CONTAINS toLower(keyword)
        )
        OR (
            // For Year nodes, match on value
            n:Year AND toString(n.value) CONTAINS keyword
        )
        
        // Return nodes with relevance score
        WITH n, count(n) AS relevance
        ORDER BY relevance DESC
        LIMIT $limit
        
        // Get related nodes too
        OPTIONAL MATCH (n)-[r]-(related)
        WHERE related.name IS NOT NULL
        
        // Return node with its properties and relationships
        RETURN 
            n.name AS name,
            labels(n) AS labels,
            properties(n) AS properties,
            collect({
                type: type(r),
                name: related.name,
                description: related.description
            }) AS relationships
        """
        
        try:
            results = self.execute_query(
                cypher_query, 
                {"keywords": unique_keywords, "limit": limit}
            )
            
            formatted_results = []
            for result in results:
                # Format the result
                formatted_result = {
                    "name": result["name"],
                    "labels": result["labels"],
                    "description": result["properties"].get("description", "") if result["properties"] else "",
                    "relationships": [r for r in result["relationships"] if r["name"] is not None]
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
        
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for search purposes."""
        # Remove special characters and split by spaces
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = cleaned_text.split()
        
        # Remove common stopwords
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 
                    'were', 'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for',
                    'with', 'by', 'about', 'like', 'through', 'over', 'before',
                    'after', 'between', 'under', 'above', 'of', 'from', 'up',
                    'down', 'into', 'during', 'until', 'after', 'than', 'this',
                    'that', 'these', 'those', 'what', 'which', 'who', 'whom',
                    'whose', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
                    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
                    'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
                    'very', 'can', 'will', 'just', 'should', 'now'}
        
        keywords = [word for word in words if word not in stopwords]
        
        # Add cybersecurity-specific terms to improve search
        cybersecurity_terms = ['attack', 'threat', 'vulnerability', 'breach', 'malware', 
                             'phishing', 'ransomware', 'ddos', 'exploit', 'virus',
                             'trojan', 'backdoor', 'security', 'firewall', 'encryption']
        
        # Check if any cybersecurity terms are in the text and prioritize them
        cyber_keywords = [term for term in cybersecurity_terms if term in cleaned_text]
        
        # Return prioritized keywords
        return cyber_keywords + keywords

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
            related.name AS related_name,
            related.description AS related_description
        LIMIT $limit
        """
        return self.execute_query(cypher_query, {"limit": limit})

    def get_visualization_subgraph(self, entities: List[str], max_nodes: int = 15) -> Dict[str, Any]:
        """
        Get a subgraph for visualization based on the provided entities.
        
        Args:
            entities: List of entity names to include in the subgraph
            max_nodes: Maximum number of nodes to include
            
        Returns:
            Dict with nodes and relationships for visualization
        """
        # Simplifying the implementation to avoid syntax errors
        if not entities or not isinstance(entities, list):
            return {"nodes": [], "relationships": []}
        
        # Filter out empty or None entries
        filtered_entities = [e for e in entities if e]
        
        if not filtered_entities:
            return {"nodes": [], "relationships": []}
        
        # Limit the number of entities to avoid creating too large visualizations
        filtered_entities = filtered_entities[:max_nodes]
        
        # Create a simpler Cypher query to avoid syntax issues
        query = """
        // Match nodes that have names containing any of our entities
        UNWIND $entities AS entity
        MATCH (n)
        WHERE n.name =~ ('(?i).*' + entity + '.*')
        
        // Collect up to max_nodes unique nodes
        WITH COLLECT(DISTINCT n) AS nodes LIMIT $maxNodes
        
        // For each node, find its direct relationships to other matched nodes
        UNWIND nodes AS n
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE m IN nodes
        
        // Return the nodes and relationships
        RETURN 
            collect(DISTINCT n) AS nodes,
            collect(DISTINCT r) AS relationships
        """
        
        try:
            result = self.execute_query(query, {"entities": filtered_entities, "maxNodes": max_nodes})
            
            if not result or len(result) == 0:
                # Return empty result if no matches
                return {"nodes": [], "relationships": []}
            
            # Format nodes for visualization
            formatted_nodes = []
            node_id_map = {}  # Map Neo4j IDs to our index for linking relationships
            
            # Process nodes
            for idx, node in enumerate(result[0].get("nodes", [])):
                # Save the internal ID mapping
                if hasattr(node, "id"):
                    node_id_map[node.id] = idx
                
                # Get node properties safely
                properties = {}
                if hasattr(node, "items"):
                    properties = dict(node.items())
                
                # Get node labels safely
                labels = ["Unknown"]
                if hasattr(node, "labels"):
                    labels = list(node.labels)
                
                # Create a formatted node
                formatted_node = {
                    "id": idx,
                    "label": properties.get("name", f"Node-{idx}"),
                    "type": labels[0] if labels else "Unknown",
                    "properties": properties
                }
                
                formatted_nodes.append(formatted_node)
            
            # Format relationships
            formatted_relationships = []
            for rel in result[0].get("relationships", []):
                # Skip if we can't determine source or target
                if not hasattr(rel, "start_node") or not hasattr(rel, "end_node"):
                    continue
                
                # Get the mapped IDs for start and end nodes
                if hasattr(rel.start_node, "id") and hasattr(rel.end_node, "id"):
                    source_id = node_id_map.get(rel.start_node.id)
                    target_id = node_id_map.get(rel.end_node.id)
                    
                    # Only include if both source and target were in our node set
                    if source_id is not None and target_id is not None:
                        # Get relationship properties
                        rel_props = {}
                        if hasattr(rel, "items"):
                            rel_props = dict(rel.items())
                        
                        # Get relationship type
                        rel_type = "RELATED_TO"
                        if hasattr(rel, "type"):
                            rel_type = rel.type
                        
                        formatted_rel = {
                            "source": source_id,
                            "target": target_id,
                            "type": rel_type,
                            "properties": rel_props
                        }
                        
                        formatted_relationships.append(formatted_rel)
            
            # Return the formatted subgraph
            return {
                "nodes": formatted_nodes,
                "relationships": formatted_relationships
            }
            
        except Exception as e:
            print(f"Error getting visualization subgraph: {e}")
            # Return empty result in case of error
            return {"nodes": [], "relationships": []}
    
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