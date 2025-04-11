import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';
import AboutSection from './AboutSection';

// Mock data for graph visualization - updated for cybersecurity domain
const mockGraphData = {
  nodes: [
    { id: 1, label: 'Ransomware', group: 'Threat' },
    { id: 2, label: 'Encryption', group: 'Defense' },
    { id: 3, label: 'Firewall', group: 'Protection' },
    { id: 4, label: 'Data Breach', group: 'Incident' },
    { id: 5, label: 'Zero Trust', group: 'Framework' },
  ],
  edges: [
    { from: 1, to: 2, label: 'Mitigated By' },
    { from: 1, to: 3, label: 'Blocked By' },
    { from: 1, to: 4, label: 'Causes' },
    { from: 5, to: 3, label: 'Implements' },
    { from: 5, to: 2, label: 'Requires' },
  ]
};

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to the Cybersecurity Knowledge Assistant. I can help with questions about threats, vulnerabilities, security frameworks, and best practices. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [showAbout, setShowAbout] = useState(true); // Show about section by default
  const [typing, setTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-focus the input field when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, [showAbout]);

  // Function to handle user input
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    // Add user message
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // Get chat history for context
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // Send request to backend API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          history: history
        }),
      });
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      const data = await response.json();
      
      // Add assistant response
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
      
      // Update graph data if available
      if (data.graph_data) {
        setGraphData(data.graph_data);
      } else {
        // Use mock data for demonstration
        setGraphData(mockGraphData);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Security alert: I encountered an error processing your request. Please try again or verify your connection is secure.' 
      }]);
    } finally {
      setLoading(false);
      // Focus the input field after response is received
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Show typing indicator when user is typing
  const handleInputChange = (e) => {
    setInput(e.target.value);
    if (!typing && e.target.value) {
      setTyping(true);
    } else if (typing && !e.target.value) {
      setTyping(false);
    }
  };

  return (
    <>
      {showAbout && <AboutSection onClose={() => setShowAbout(false)} />}
      
      <div className="chat-container">
        <div className="chat-header">
          <h2>Cybersecurity Knowledge Assistant</h2>
          <div className="header-actions">
            {typing && <span className="typing-indicator">Typing...</span>}
            <button className="info-button" onClick={() => setShowAbout(true)}>ℹ️</button>
          </div>
        </div>
        
        <div className="chat-body">
          <div className="messages-container">
            {messages.map((message, index) => (
              <div key={index} className={`message ${message.role}`}>
                <div className="message-bubble">
                  <div className="message-content">{message.content}</div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="message assistant">
                <div className="message-bubble">
                  <div className="message-content loading">
                    <div className="dot-typing"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          {graphData && (
            <div className="graph-container">
              <h3>Security Knowledge Graph</h3>
              <div className="graph-placeholder">
                {/* In a real implementation, you would render the graph here with D3.js or react-force-graph */}
                <div className="mock-graph">
                  <p>Security Graph Visualization</p>
                  <ul>
                    {graphData.nodes.slice(0, 5).map(node => (
                      <li key={node.id}>
                        {node.label || node.name} ({node.group || 'Entity'})
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
        
        <div className="chat-input">
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Ask about threats, vulnerabilities, security frameworks..."
            rows={2}
          />
          <button 
            className={input.trim() ? 'active' : ''} 
            onClick={handleSendMessage} 
            disabled={loading || !input.trim()}
          >
            {loading ? 'Analyzing...' : 'Send'}
          </button>
        </div>
      </div>
    </>
  );
};

export default ChatInterface;