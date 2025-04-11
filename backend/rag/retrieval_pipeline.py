import os
from typing import List, Dict, Any, Optional
import re
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Import the CybersecurityKGLoader that was missing
from backend.knowledge_graph.cybersecurity_kg_loader import CybersecurityKGLoader
from backend.knowledge_graph.neo4j_client import Neo4jClient
from backend.models.llm_handler import LLMHandler

# Try to import the NER pipeline if available
try:
    from transformers import pipeline
except ImportError:
    print("Warning: transformers package not available, entity extraction will be limited")

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
        Determine if a query is cybersecurity-related.
        
        In this application, we treat all queries as cybersecurity-related
        since that's our domain focus.
        
        Args:
            query: The user's query
            
        Returns:
            True if the query appears to be cybersecurity-related (always true in this implementation)
        """
        # For this application, we'll assume all queries are cybersecurity-related
        # but we could implement more sophisticated detection if needed
        return True
    
    def _process_cybersecurity_query(self, query: str, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process a cybersecurity-related query with specialized handling.
        """
        # Step 1: Extract potential entities for improved context
        extracted_entities = self._extract_entities(query)
        potential_users = self._extract_potential_users(query)
        potential_computers = self._extract_potential_computers(query)
            
        # Step 2: Optimize query for the cybersecurity domain
        cybersecurity_terms = ["attack", "breach", "vulnerability", "threat", "malware", 
                               "phishing", "ransomware", "encryption", "firewall", "exploit"]
        
        # Check if query is asking for a specific cypher-based analysis
        if any(term in query.lower() for term in ["top attack", "most common", "statistics", "highest risk"]):
            # Run pre-defined analytical queries on the knowledge graph
            kg_loader = CybersecurityKGLoader(self.neo4j_client)
            predefined_queries = kg_loader.get_common_cybersecurity_queries()
            matching_queries = []
            
            for query_def in predefined_queries:
                if any(term in query.lower() for term in query_def["name"].lower().split()):
                    matching_queries.append(query_def)
            
            if matching_queries:
                # Execute the matching analytical query
                analytical_results = []
                for match in matching_queries[:1]:  # Just use the first match for now
                    result = self.neo4j_client.execute_query(match["query"])
                    analytical_results.append({
                        "query_name": match["name"],
                        "results": result
                    })
                
                # Format analytical results for LLM context
                cypher_results = [{
                    "name": f"Analysis: {ar['query_name']}",
                    "labels": ["Analysis", "Statistics"],
                    "description": f"Results from knowledge graph analysis: {str(ar['results'][:5])}"
                } for ar in analytical_results]
            else:
                # Perform semantic search if no pre-defined query matches
                cypher_results = self.neo4j_client.semantic_search(
                    query, 
                    additional_entities=[*extracted_entities, *potential_users, *potential_computers]
                )
        else:
            # Regular semantic search
            cypher_results = self.neo4j_client.semantic_search(
                query, 
                additional_entities=[*extracted_entities, *potential_users, *potential_computers]
            )
        
        # Step 3: Generate answer using the LLM and KG context
        structured_answer = self.llm_handler.generate_structured_answer(
            query=query,
            kg_context=cypher_results,
            chat_history=chat_history,
            domain="cybersecurity"  # Add domain hint for the LLM
        )
        
        # Step 4: Extract entities for graph visualization
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
        entities_for_graph.extend(potential_computers)
        
        # Add entities from cypher results
        for result in cypher_results:
            if result.get("name"):
                entities_for_graph.append(result["name"])
        
        # Only include if we have entities to visualize
        if entities_for_graph:
            # Get subgraph data for visualization
            graph_data = self.neo4j_client.get_visualization_subgraph([e for e in entities_for_graph if e])
        
        return {
            "answer": structured_answer["answer"],
            "sources": cypher_results,
            "graph_data": graph_data
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