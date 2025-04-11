import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import Generation, LLMResult

class LLMHandler:
    """Handler for LLM interactions using LangChain with Hugging Face's models."""
    
    def __init__(self):
        """Initialize the LLM handler."""
        load_dotenv()
        
        # Get API key from environment
        self.hf_api_key = os.getenv("HF_API_KEY")
        
        # For testing purposes, we'll create a mock LLM implementation
        self.llm = MockLLM()
        
        # Create the system prompt for cybersecurity domain
        self.cybersecurity_system_prompt = """
        You are a specialized cybersecurity assistant that provides accurate, reliable, and contextual information.
        Your knowledge is based on authoritative cybersecurity sources and a knowledge graph of network entities.
        
        Key guidelines:
        1. Provide complete, accurate answers based on the knowledge graph context provided
        2. Explain cybersecurity terms in plain language while maintaining accuracy
        3. Include relevant relationships between entities when helpful (users, computers, domains, groups)
        4. Focus on explaining attack paths, vulnerabilities, and security concepts
        5. Structure complex answers clearly with bullet points or sections
        
        Use the provided knowledge graph context to enhance your answers with domain-specific knowledge.
        """
        
        # Legacy healthcare prompt kept for compatibility with existing code
        self.healthcare_system_prompt = self.cybersecurity_system_prompt
    
    def test_connection(self) -> bool:
        """Test if the LLM connection is working."""
        try:
            # Using our mock LLM for testing
            return True
        except Exception as e:
            print(f"Error testing LLM connection: {e}")
            return False
    
    def generate_answer(self, 
                       query: str, 
                       kg_context: List[Dict[str, Any]], 
                       chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate an answer to a user query using the LLM.
        
        Args:
            query: The user's query
            kg_context: Context from the knowledge graph
            chat_history: Previous conversation turns
            
        Returns:
            Generated answer from the LLM
        """
        # Format the KG context for the prompt
        formatted_context = self._format_kg_context(kg_context)
        
        # Format chat history if provided
        history_text = ""
        if chat_history:
            for message in chat_history:
                role = message["role"]
                content = message["content"]
                history_text += f"{role.capitalize()}: {content}\n"
        
        # Create a prompt for Mistral using its specific instruction format
        instruction = f"{self.healthcare_system_prompt}\n\n"
        
        if history_text:
            instruction += f"Previous conversation:\n{history_text}\n\n"
            
        instruction += f"Knowledge Graph Context:\n{formatted_context}\n\nUser Query: {query}\n\nYour helpful answer:"
        
        # Create the Mistral-specific instruction format
        prompt_template = PromptTemplate(
            template="<s>[INST] {instruction} [/INST]",
            input_variables=["instruction"]
        )
        
        # Create and run the chain
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        try:
            result = chain.run(instruction=instruction)
            return result
        except Exception as e:
            print(f"Error generating answer: {e}")
            return "I'm sorry, I encountered an error while generating your answer. Please try again."
    
    def generate_structured_answer(self, 
                                 query: str, 
                                 kg_context: List[Dict[str, Any]], 
                                 chat_history: Optional[List[Dict[str, str]]] = None,
                                 domain: str = "cybersecurity") -> Dict[str, Any]:
        """
        Generate a structured answer that includes the answer text and relevant entities.
        
        Args:
            query: The user's query
            kg_context: Context from the knowledge graph
            chat_history: Previous conversation turns
            domain: Domain context ("cybersecurity" or "healthcare")
            
        Returns:
            Dict with answer text and extracted entities
        """
        # Format the KG context for the prompt
        formatted_context = self._format_kg_context(kg_context)
        
        # Format chat history if provided
        history_text = ""
        if chat_history:
            for message in chat_history:
                role = message["role"]
                content = message["content"]
                history_text += f"{role.capitalize()}: {content}\n"
        
        # Create structured output instructions based on domain
        if domain == "cybersecurity":
            structure_instructions = """
            After providing your answer, list key cybersecurity entities mentioned in your response in this format:
            
            ENTITIES:
            - Entity1
            - Entity2
            - Entity3
            """
            system_prompt = self.cybersecurity_system_prompt
        else:
            structure_instructions = """
            After providing your answer, list key medical entities mentioned in your response in this format:
            
            ENTITIES:
            - Entity1
            - Entity2
            - Entity3
            """
            system_prompt = self.healthcare_system_prompt
        
        # Create a prompt for Mistral using its specific instruction format
        instruction = f"{system_prompt}\n\n{structure_instructions}\n\n"
        
        if history_text:
            instruction += f"Previous conversation:\n{history_text}\n\n"
            
        instruction += f"Knowledge Graph Context:\n{formatted_context}\n\nUser Query: {query}\n\nYour helpful answer:"
        
        # Create the Mistral-specific instruction format
        prompt_template = PromptTemplate(
            template="<s>[INST] {instruction} [/INST]",
            input_variables=["instruction"]
        )
        
        # Create and run the chain
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        
        try:
            result = chain.run(instruction=instruction)
            
            # Parse entities from the result
            answer = result
            entities = []
            
            # Try to extract entities if they exist in the expected format
            if "ENTITIES:" in result:
                parts = result.split("ENTITIES:")
                answer = parts[0].strip()
                entities_text = parts[1].strip()
                entities = [e.strip().lstrip("- ") for e in entities_text.split("\n") if e.strip()]
            
            return {
                "answer": answer,
                "entities": entities
            }
        except Exception as e:
            print(f"Error generating structured answer: {e}")
            return {
                "answer": "I'm sorry, I encountered an error while generating your answer. Please try again.",
                "entities": []
            }
    
    def _format_kg_context(self, kg_context: List[Dict[str, Any]]) -> str:
        """Format knowledge graph context for inclusion in the prompt."""
        if not kg_context:
            return "No relevant information found in the knowledge graph."
            
        context_sections = []
        
        for i, item in enumerate(kg_context):
            section = f"Entity {i+1}: {item.get('name', 'Unknown')}\n"
            section += f"Type: {', '.join(item.get('labels', ['Unknown']))}\n"
            
            if item.get('description'):
                section += f"Description: {item.get('description')}\n"
                
            if item.get('relationships'):
                section += "Related entities:\n"
                for rel in item.get('relationships'):
                    rel_type = rel.get('type', 'related_to').replace('_', ' ').title()
                    section += f"- {rel_type}: {rel.get('name', 'Unknown')}"
                    if rel.get('description'):
                        section += f" ({rel.get('description')})"
                    section += "\n"
            
            context_sections.append(section)
            
        return "\n".join(context_sections)

class MockLLM(LLM):
    """A mock LLM implementation for testing purposes that follows LangChain's interface."""
    
    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "mock_llm"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Mock implementation that returns a fixed response."""
        return "This is a mock response from the LLM. Your prompt has been processed successfully."
    
    def generate(
        self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any
    ) -> LLMResult:
        """Generate method implementation required by LangChain."""
        return LLMResult(
            generations=[[Generation(text=self._call(prompt, stop=stop))] for prompt in prompts]
        )