import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import numpy as np
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# Import custom modules
from backend.knowledge_graph.neo4j_client import Neo4jClient
from backend.models.llm_handler import LLMHandler

class RAGPipeline:
    """
    Retrieval Augmented Generation (RAG) pipeline that combines
    knowledge graph retrieval with LLM generation.
    """
    
    def __init__(self, neo4j_client: Neo4jClient, llm_handler: LLMHandler):
        """
        Initialize the RAG pipeline.
        
        Args:
            neo4j_client: Client for Neo4j knowledge graph
            llm_handler: Handler for LLM interactions
        """
        self.neo4j_client = neo4j_client
        self.llm_handler = llm_handler
        
        # Load environment variables
        load_dotenv()
        
        # Initialize the embedding model
        self.embedding_model = SentenceTransformer(
            os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
        
        # Initialize NER model for entity extraction
        self.ner_model = None
        if os.getenv("USE_NER", "true").lower() == "true":
            try:
                self.ner_model = pipeline(
                    "ner", 
                    model=os.getenv("NER_MODEL", "medical-ner-model"),
                    aggregation_strategy="simple"
                )
            except:
                print("Warning: NER model not available, entity extraction disabled")
    
    def process_query(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a user query through the RAG pipeline.
        
        Args:
            query: The user's query
            chat_history: Previous conversation turns
            
        Returns:
            Dict containing answer and optional graph data
        """
        # Check if the query is cybersecurity-related
        if self._is_cybersecurity_query(query):
            return self._process_cybersecurity_query(query, chat_history)
        
        # Regular healthcare processing path
        # Step 1: Extract entities from query (if NER model is available)
        extracted_entities = self._extract_entities(query)
        
        # Step 2: Retrieve relevant information from knowledge graph
        kg_results = self.neo4j_client.semantic_search(query)
        
        # Step 3: Generate answer using the LLM and KG context
        structured_answer = self.llm_handler.generate_structured_answer(
            query=query,
            kg_context=kg_results,
            chat_history=chat_history
        )
        
        # Step 4: Get subgraph data for visualization
        graph_data = None
        entities_for_graph = []
        
        # Add entities from structured output
        if "entities" in structured_answer and structured_answer["entities"]:
            # If the entities field is a string, split it into a list
            if isinstance(structured_answer["entities"], str):
                entity_list = [e.strip() for e in structured_answer["entities"].split(",")]
                entities_for_graph.extend(entity_list)
            # If it's already a list
            elif isinstance(structured_answer["entities"], list):
                entities_for_graph.extend(structured_answer["entities"])
        
        # Add entities from knowledge graph search
        for result in kg_results:
            if result.get("name"):
                entities_for_graph.append(result["name"])
        
        # Add extracted entities from NER
        entities_for_graph.extend(extracted_entities)
        
        # Remove duplicates and get the top 5 entities
        unique_entities = list(set(entities_for_graph))
        if unique_entities:
            graph_data = self.neo4j_client.get_subgraph_for_entities(unique_entities[:5])
        
        # Prepare the final response
        return {
            "answer": structured_answer.get("answer", "No answer generated"),
            "sources": kg_results,
            "graph_data": graph_data
        }
    
    def _is_cybersecurity_query(self, query: str) -> bool:
        """
        Determine if a query is related to cybersecurity.
        
        Args:
            query: The user's query
            
        Returns:
            Boolean indicating if the query is cybersecurity-related
        """
        # Keywords for cybersecurity classification
        cybersecurity_keywords = [
            'attack', 'path', 'vulnerability', 'cyber', 'security', 'network', 
            'rdp', 'access', 'admin', 'domain', 'BloodHound', 'kerberos', 
            'user', 'computer', 'group', 'password', 'hack', 'breach', 'permission',
            'exploit', 'active directory', 'ad', 'windows', 'session', 'threat',
            'privilege', 'escalation', 'lateral movement'
        ]
        
        # Lowercase the query for case-insensitive matching
        query_lower = query.lower()
        
        # Check if any of the keywords are in the query
        return any(keyword.lower() in query_lower for keyword in cybersecurity_keywords)
    
    def _process_cybersecurity_query(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a cybersecurity-related query.
        
        Args:
            query: The user's query
            chat_history: Previous conversation turns
            
        Returns:
            Dict containing answer and optional graph data
        """
        # Extract potential entities or usernames from the query
        potential_users = self._extract_potential_users(query)
        
        # Start with a general context
        cypher_results = []
        
        # If we have potential users mentioned, check their access paths
        if potential_users:
            for user in potential_users:
                # Find RDP access
                rdp_results = self.neo4j_client.find_rdp_access(user)
                if rdp_results:
                    cypher_results.extend(rdp_results)
                    
                # Find group memberships
                group_results = self.neo4j_client.find_user_group_memberships(user)
                if group_results:
                    cypher_results.extend(group_results)
        
        # Check for attack path analysis in the query
        if 'attack' in query.lower() and 'path' in query.lower():
            # Default target for demonstration purposes
            target = "DC01.TESTCOMPANY.LOCAL"
            
            # Try to extract a potential target from the query
            potential_targets = self._extract_potential_computers(query)
            if potential_targets:
                target = potential_targets[0]
                
            # Find attack paths
            path_results = self.neo4j_client.find_attack_paths(target)
            if path_results:
                cypher_results.extend(path_results)
        
        # Check for high-value targets in the query
        if 'high value' in query.lower() or 'target' in query.lower():
            target_results = self.neo4j_client.find_high_value_targets()
            if target_results:
                cypher_results.extend(target_results)
        
        # Check for admin queries
        if 'admin' in query.lower() or 'administrator' in query.lower():
            admin_results = self.neo4j_client.find_domain_admins()
            if admin_results:
                cypher_results.extend(admin_results)
        
        # Check for kerberoasting vulnerabilities
        if 'kerberos' in query.lower() or 'vulnerability' in query.lower():
            kerb_results = self.neo4j_client.find_kerberoastable_accounts()
            if kerb_results:
                cypher_results.extend(kerb_results)
        
        # If we didn't get specific results, do a generic semantic search
        if not cypher_results:
            cypher_results = self.neo4j_client.keyword_search(query)
        
        # Generate an answer using the LLM and the retrieved context
        structured_answer = self.llm_handler.generate_structured_answer(
            query=query,
            kg_context=cypher_results,
            chat_history=chat_history,
            domain="cybersecurity"  # Add domain hint for the LLM
        )
        
        # Extract entities for graph visualization
        graph_data = None
        entities_for_graph = []
        
        # Add entities from structured output
        if "entities" in structured_answer and structured_answer["entities"]:
            if isinstance(structured_answer["entities"], str):
                entity_list = [e.strip() for e in structured_answer["entities"].split(",")]
                entities_for_graph.extend(entity_list)
            elif isinstance(structured_answer["entities"], list):
                entities_for_graph.extend(structured_answer["entities"])
        
        # Add potential users and computers
        entities_for_graph.extend(potential_users)
        entities_for_graph.extend(self._extract_potential_computers(query))
        
        # Add entities from cypher results
        for result in cypher_results:
            for key, value in result.items():
                if isinstance(value, str) and key not in ('description', 'properties'):
                    entities_for_graph.append(value)
        
        # Remove duplicates and get the top 5 entities
        unique_entities = list(set(entities_for_graph))
        if unique_entities:
            graph_data = self.neo4j_client.get_subgraph_for_entities(unique_entities[:5])
        
        # Prepare the final response
        return {
            "answer": structured_answer.get("answer", "No answer generated"),
            "sources": cypher_results,
            "graph_data": graph_data,
            "domain": "cybersecurity"  # Identify this as a cybersecurity response
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract medical entities from text using NER.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            List of extracted entity names
        """
        if not self.ner_model:
            return []
            
        try:
            # Run NER on the text
            ner_results = self.ner_model(text)
            
            # Extract entity names
            entities = []
            for entity in ner_results:
                # Only include entities with high confidence
                if entity["score"] > 0.7:
                    entities.append(entity["word"])
                    
            return entities
        except Exception as e:
            print(f"Error in entity extraction: {e}")
            return []
    
    def _extract_potential_users(self, text: str) -> List[str]:
        """
        Extract potential user names from text.
        
        Args:
            text: The text to extract usernames from
            
        Returns:
            List of potential usernames
        """
        # Simple heuristic: look for words with @ in them or that end with .local
        words = text.split()
        potential_users = []
        
        for word in words:
            # Clean the word of punctuation
            clean_word = word.strip(",.;:!?()[]{}\"'")
            
            # Check if it looks like a username
            if '@' in clean_word or clean_word.lower().endswith('.local'):
                potential_users.append(clean_word)
        
        # If no users were found with the simple heuristic, use a default demo user
        if not potential_users:
            potential_users.append("HilaryOlivia226@TestCompany.Local")
            
        return potential_users
    
    def _extract_potential_computers(self, text: str) -> List[str]:
        """
        Extract potential computer names from text.
        
        Args:
            text: The text to extract computer names from
            
        Returns:
            List of potential computer names
        """
        # Simple heuristic: look for words that look like computer names
        words = text.split()
        potential_computers = []
        
        for word in words:
            # Clean the word of punctuation
            clean_word = word.strip(",.;:!?()[]{}\"'")
            
            # Check if it looks like a computer name
            if clean_word.upper() == clean_word and len(clean_word) <= 4 and clean_word.isalnum():
                potential_computers.append(clean_word)
                
            # Check for FQDN format
            if clean_word.count('.') >= 2 and any(domain in clean_word.lower() for domain in ['.local', '.com', '.net', '.org']):
                potential_computers.append(clean_word)
        
        # If no computers were found, use a default demo computer
        if not potential_computers:
            potential_computers.append("DC01.TESTCOMPANY.LOCAL")
            
        return potential_computers
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of embedding values
        """
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []