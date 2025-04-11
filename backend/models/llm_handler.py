import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import Generation, LLMResult
import requests
import json
import google.generativeai as genai

class LLMHandler:
    """Handler for LLM interactions using Gemini API."""
    
    def __init__(self):
        """Initialize the LLM handler."""
        load_dotenv()
        
        # Get API key from environment
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Initialize LLM
        if self.gemini_api_key:
            # Use a direct API implementation rather than LangChain's LLM
            self.use_mock = False
            self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
            self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
            
            # Configure Google Generative AI
            genai.configure(api_key=self.gemini_api_key)
            
            # Get the model
            try:
                self.genai_model = genai.GenerativeModel(self.model_name)
                print(f"Using Gemini model: {self.model_name} with temperature: {self.temperature}")
            except Exception as e:
                print(f"Error initializing Gemini model: {e}")
                self.use_mock = True
                
            # Create a mock LLM for LangChain compatibility (but we'll use direct API calls)
            self.llm = MockLLM()
        else:
            # Fallback to mock LLM if no API key
            self.use_mock = True
            print("Using Mock LLM (no Gemini API key provided)")
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
            if self.use_mock:
                return True
                
            # Use the Google AI client library instead of direct API calls
            prompt = "Say 'Connection successful' if you can read this"
            
            try:
                response = self.genai_model.generate_content(prompt)
                response_text = response.text
                return "connection successful" in response_text.lower()
            except Exception as e:
                print(f"Error testing LLM connection with Google AI client: {e}")
                return False
        except Exception as e:
            print(f"Error testing LLM connection: {e}")
            return False
    
    def get_llm_response(self, prompt: str) -> str:
        """
        Get a direct response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response from the LLM
        """
        if self.use_mock:
            return "LLM connection successful. This is a mock response."
        
        try:
            # Use the Google AI client library
            generation_config = {
                "temperature": self.temperature,
            }
            
            try:
                # Set generation config
                response = self.genai_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Check if the response has content
                if response and hasattr(response, 'text'):
                    return response.text
                
                return "No response generated from the model."
            except Exception as e:
                print(f"Error generating content with Google AI client: {e}")
                return f"I'm sorry, I encountered an error while generating your answer with the Gemini model. Error: {str(e)}"
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return f"I'm sorry, I encountered an error while generating your answer. Error: {str(e)}"
    
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
        
        # Create the full instruction
        instruction = f"{self.cybersecurity_system_prompt}\n\n"
        
        if history_text:
            instruction += f"Previous conversation:\n{history_text}\n\n"
            
        instruction += f"Knowledge Graph Context:\n{formatted_context}\n\nUser Query: {query}\n\nYour helpful answer:"
        
        # Either use the mock LLM or make a direct API call
        if self.use_mock:
            # Use LangChain with the mock LLM
            prompt_template = PromptTemplate(
                template="{instruction}",
                input_variables=["instruction"]
            )
            chain = LLMChain(llm=self.llm, prompt=prompt_template)
            result = chain.run(instruction=instruction)
            return result
        else:
            # Make a direct API call to Gemini
            return self.get_llm_response(instruction)
    
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
        
        # Create the full instruction
        instruction = f"{system_prompt}\n\n{structure_instructions}\n\n"
        
        if history_text:
            instruction += f"Previous conversation:\n{history_text}\n\n"
            
        instruction += f"Knowledge Graph Context:\n{formatted_context}\n\nUser Query: {query}\n\nYour helpful answer:"
        
        # Either use the mock LLM or make a direct API call
        try:
            if self.use_mock:
                # Use LangChain with the mock LLM
                prompt_template = PromptTemplate(
                    template="{instruction}",
                    input_variables=["instruction"]
                )
                chain = LLMChain(llm=self.llm, prompt=prompt_template)
                result = chain.run(instruction=instruction)
            else:
                # Make a direct API call to Gemini
                result = self.get_llm_response(instruction)
            
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
                "answer": f"I'm sorry, I encountered an error while generating your answer. Error: {str(e)}",
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
        """Mock implementation that returns responses based on the input prompt."""        
        prompt_lower = prompt.lower()
        
        if "hello" in prompt_lower or "hi" in prompt_lower or "greeting" in prompt_lower:
            return "Hello! I'm your cybersecurity assistant. How can I help you today?"
        
        elif "phishing" in prompt_lower:
            return """Phishing attacks are social engineering techniques that trick users into revealing sensitive information.
            
Common phishing methods include:
1. Email phishing - Sending deceptive emails that appear to be from legitimate sources
2. Spear phishing - Targeted attacks against specific individuals or organizations
3. Whaling - Targeting high-profile executives or senior leaders
4. Vishing - Voice phishing via phone calls
5. Smishing - SMS-based phishing attacks

The best defense against phishing is user education, email filtering, and multi-factor authentication.

ENTITIES:
- Phishing
- Spear phishing
- Whaling
- Vishing
- Smishing"""
        
        elif "ransomware" in prompt_lower:
            return """Ransomware is malicious software that encrypts files and demands payment for decryption.
            
Notable ransomware attacks include:
1. WannaCry (2017) - Exploited EternalBlue vulnerability
2. NotPetya (2017) - Started as a supply chain attack
3. REvil - Operates as Ransomware-as-a-Service (RaaS)
4. Ryuk - Targets large organizations and government entities
5. Conti - Known for double extortion tactics (encryption + data theft)

Prevention measures include regular backups, patching systems, network segmentation, and employee training.

ENTITIES:
- Ransomware
- WannaCry
- NotPetya
- REvil
- Ryuk
- Conti"""
        
        elif "ddos" in prompt_lower or "denial of service" in prompt_lower:
            return """Distributed Denial of Service (DDoS) attacks attempt to overwhelm systems by flooding them with traffic.
            
Common DDoS attack types:
1. Volume-based attacks - Overwhelm bandwidth (UDP floods, ICMP floods)
2. Protocol attacks - Target server resources (SYN floods)
3. Application layer attacks - Target specific applications or services
4. Amplification attacks - Use legitimate services to amplify attack traffic

Mitigation strategies include traffic filtering, rate limiting, and using DDoS protection services.

ENTITIES:
- DDoS
- UDP floods
- SYN floods
- Application layer attacks
- Amplification attacks"""
        
        else:
            # Default response for other queries
            return """Based on the cybersecurity knowledge graph, I can tell you that the most common cybersecurity threats include:

1. Phishing attacks - These are social engineering techniques used to trick users into revealing sensitive information.
2. Ransomware - Malicious software that encrypts files and demands payment for decryption.
3. Distributed Denial of Service (DDoS) attacks - Attempts to overwhelm systems by flooding them with traffic.
4. Data breaches - Unauthorized access to sensitive data, often leading to information theft.
5. Malware - Various forms of malicious software designed to damage or gain unauthorized access to systems.

These threats have been consistently among the top concerns for organizations across various industries.

ENTITIES:
- Phishing attacks
- Ransomware
- DDoS attacks
- Data breaches
- Malware"""
    
    def generate(
        self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs: Any
    ) -> LLMResult:
        """Generate method implementation required by LangChain."""
        return LLMResult(
            generations=[[Generation(text=self._call(prompt, stop=stop))] for prompt in prompts]
        )