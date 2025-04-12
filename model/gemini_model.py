from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os
import google.generativeai as genai
import re
import json
from typing import Dict, List, Any, Optional

class GeminiChain:
    def __init__(self, metta_kb):
        # Get the API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # Configure with correct model name and endpoint
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",  # model name
            google_api_key=api_key,  # Explicitly pass the API key here
            temperature=0.3,
            convert_system_message_to_human=True,
        )
        self.metta_kb = metta_kb
        self.chain = self._create_chain()

    def _create_chain(self):
        prompt = ChatPromptTemplate.from_template(
            """Answer the question based only on the following context:
            {context}
            
            Question: {question}
            
            Provide a helpful response about cybersecurity using both the context and your general knowledge.
            Focus on explaining cybersecurity concepts clearly and accurately.
            
            You now have the ability to respond with multiple formats. When appropriate, include:
            - Images (provide a description and URL if relevant)
            - Links to helpful resources
            - Interactive elements like accordions for detailed explanations
            - Charts or diagrams when they help explain concepts
            
            FORMATTING GUIDELINES:
            1. Use proper paragraph breaks between different topics or ideas
            2. Use bullet points for lists
            3. Include appropriate spacing between sentences
            4. Bold important terms or headings using markdown (**term**)
            5. Organize information in a readable structure
            6. For any technical terms, provide a brief definition in parentheses
            7. Use short, clear sentences for better readability
            8. When mentioning diagrams, use [IMAGE:description:URL] format
            9. For useful links, use [LINK:title:URL] format
            10. For collapsible sections, use [ACCORDION:title:content] format
            11. For button elements, use [BUTTON:text:action] format"""
        )

        return (
            {"context": self._get_metta_context, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
            | self._format_response
        )

    def _get_metta_context(self, _):
        """Build comprehensive context from Cybersecurity MeTTa KB"""
        context = {
            'threat_entities': self.metta_kb.getthreatentities(),
            'defense_technologies': self.metta_kb.getdefensetechnologies(),
            'attack_vectors': self.metta_kb.getattackvectors(),
            'data_theft_threats': self.metta_kb.getdatatheftthreats(),
            'network_security_tools': self.metta_kb.getnetworksecuritytools(),
            'endpoint_security_tools': self.metta_kb.getendpointsecuritytools(),
            'security_monitoring_tools': self.metta_kb.getsecuritymonitoringtools(),
            'all_mitigations': self.metta_kb.getallmitigations(),
            'threat_detection_tools': self.metta_kb.getthreatdetectiontools(),
            'attack_vector_defenses': self.metta_kb.getdefensesforattackvector(),
            'network_security_domain_tools': self.metta_kb.gettoolsbysecuritydomain('NetworkSecurity'),
            'endpoint_security_domain_tools': self.metta_kb.gettoolsbysecuritydomain('EndpointSecurity'),
            'security_monitoring_domain_tools': self.metta_kb.gettoolsbysecuritydomain('SecurityMonitoring')
        }
        
        # Add mitigations by defense tools for important defense technologies
        defense_tools = ['Firewall', 'Antivirus', 'EDR', 'WAF', 'SIEM', 'DLP', 'MFA']
        defense_mitigations = {}
        for tool in defense_tools:
            mitigated_threats = self.metta_kb.findmitigationsbydefensetool(tool)
            if mitigated_threats:
                defense_mitigations[tool] = mitigated_threats
        
        context['defense_mitigations'] = defense_mitigations
        
        return self._build_prompt(context)

    def _build_prompt(self, context):
        """Format the context into the structured prompt"""
        prompt = f"""
        CYBERSECURITY KNOWLEDGE BASE CONTEXT:
        - Threat Entities: {', '.join(context['threat_entities'])}
        - Defense Technologies: {', '.join(context['defense_technologies'])}
        - Attack Vectors: {', '.join(context['attack_vectors'])}
        - Data Theft Threats: {', '.join(context['data_theft_threats'])}
        - Network Security Tools: {', '.join(context['network_security_tools'])}
        - Endpoint Security Tools: {', '.join(context['endpoint_security_tools'])}
        - Security Monitoring Tools: {', '.join(context['security_monitoring_tools'])}
        
        RELATIONSHIPS:
        - Threat Mitigations: {', '.join(context['all_mitigations'])}
        - Threat Detection: {', '.join(context['threat_detection_tools'])}
        - Attack Vector Defenses: {', '.join(context['attack_vector_defenses'])}
        
        SECURITY DOMAINS:
        - Network Security Domain Tools: {', '.join(context['network_security_domain_tools'])}
        - Endpoint Security Domain Tools: {', '.join(context['endpoint_security_domain_tools'])}
        - Security Monitoring Domain Tools: {', '.join(context['security_monitoring_domain_tools'])}
        
        DEFENSE TOOL CAPABILITIES:"""
        
        # Add defense tool capabilities section
        if 'defense_mitigations' in context and context['defense_mitigations']:
            for tool, mitigated_threats in context['defense_mitigations'].items():
                prompt += f"\n- {tool} mitigates: {', '.join(mitigated_threats)}"
        
        prompt += """

        INSTRUCTIONS:
        1. Be factual and use the cybersecurity context above
        2. Explain cybersecurity concepts clearly
        3. When discussing threats, also mention applicable defenses
        4. When discussing attack vectors, explain how they can be mitigated
        5. For technical questions, provide accurate and practical explanations
        6. Format your answer with proper spacing and structure
        7. Use markdown formatting for readability (headers, bold, lists)
        8. Create visually organized responses with clear sections
        9. Use multi-format elements when appropriate:
           - Include relevant images of cybersecurity concepts using [IMAGE:description:URL]
           - Add helpful resource links using [LINK:title:URL]
           - Use collapsible sections for detailed explanations with [ACCORDION:title:content]
           - Add interactive buttons with [BUTTON:text:action]
        """
        
        return prompt

    def _format_response(self, text):
        """Post-process the response to ensure proper formatting and extract multi-format elements"""
        if not text:
            return text
            
        # Extract multi-format elements
        images = self._extract_images(text)
        links = self._extract_links(text)
        accordions = self._extract_accordions(text)
        buttons = self._extract_buttons(text)
        
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
        
        # Ensure proper spacing between sentences
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\n\2', text)
        
        # Format bullet points consistently
        text = re.sub(r'^\s*[-*]\s*', '\n• ', text, flags=re.MULTILINE)
        
        # Format numbered lists consistently
        text = re.sub(r'^\s*(\d+)[.)] ', r'\n\1. ', text, flags=re.MULTILINE)
        
        # Ensure consistent paragraph breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Add spacing after colons if followed by text
        text = re.sub(r':\s*([A-Za-z])', r': \1', text)
        
        # Clean up any multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Add proper spacing around markdown elements
        text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)
        
        # Remove any leftover format markers from the text
        text = re.sub(r'\[IMAGE:[^\]]+\]', '', text)
        text = re.sub(r'\[LINK:[^\]]+\]', '', text)
        text = re.sub(r'\[ACCORDION:[^\]]+\]', '', text)
        text = re.sub(r'\[BUTTON:[^\]]+\]', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Create response object with text and multi-format elements
        response = {
            "text": text.strip(),
            "elements": {
                "images": images,
                "links": links,
                "accordions": accordions,
                "buttons": buttons
            }
        }
        
        return response

    def _extract_images(self, text):
        """Extract image elements from the text"""
        images = []
        image_pattern = r'\[IMAGE:([^:]+):([^\]]+)\]'
        for match in re.finditer(image_pattern, text):
            description, url = match.groups()
            images.append({
                "description": description.strip(),
                "url": url.strip()
            })
        return images

    def _extract_links(self, text):
        """Extract link elements from the text"""
        links = []
        link_pattern = r'\[LINK:([^:]+):([^\]]+)\]'
        for match in re.finditer(link_pattern, text):
            title, url = match.groups()
            links.append({
                "title": title.strip(),
                "url": url.strip()
            })
        return links

    def _extract_accordions(self, text):
        """Extract accordion elements from the text"""
        accordions = []
        accordion_pattern = r'\[ACCORDION:([^:]+):([^\]]+)\]'
        for match in re.finditer(accordion_pattern, text):
            title, content = match.groups()
            accordions.append({
                "title": title.strip(),
                "content": content.strip()
            })
        return accordions

    def _extract_buttons(self, text):
        """Extract button elements from the text"""
        buttons = []
        button_pattern = r'\[BUTTON:([^:]+):([^\]]+)\]'
        for match in re.finditer(button_pattern, text):
            text, action = match.groups()
            buttons.append({
                "text": text.strip(),
                "action": action.strip()
            })
        return buttons

    def generate_response(self, question):
        try:
            return self.chain.invoke(question)
        except Exception as e:
            raise RuntimeError(f"Generation failed: {str(e)}")




