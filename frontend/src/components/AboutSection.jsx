import React, { useState } from 'react';
import './AboutSection.css';

const AboutSection = ({ onClose }) => {
  const [isVisible, setIsVisible] = useState(true);

  const handleClose = () => {
    setIsVisible(false);
    onClose();
  };

  return isVisible ? (
    <div className="about-overlay">
      <div className="about-container">
        <div className="about-header">
          <h2>Cybersecurity Knowledge Assistant</h2>
          <button className="close-button" onClick={handleClose}>×</button>
        </div>
        
        <div className="about-content">
          <div className="about-section">
            <h3>The Challenge</h3>
            <p>
              Traditional chatbots often rely solely on predefined responses or general-purpose AI models, 
              leading to shallow answers that lack domain-specific depth. They struggle to understand complex 
              relationships, hierarchies, and contextual dependencies within specialized fields like cybersecurity. 
              This results in inaccurate or incomplete responses, making them unreliable for industry-specific use cases.
            </p>
          </div>
          
          <div className="about-section">
            <h3>Our Solution</h3>
            <p>
              We've developed a domain-specific FAQ chatbot that integrates a knowledge graph for real-time 
              contextual understanding of cybersecurity concepts. The system:
            </p>
            <ul>
              <li>Integrates a knowledge graph for real-time contextual understanding</li>
              <li>Comprehends relationships, hierarchies, and dependencies within cybersecurity</li>
              <li>Provides insightful, structured, and fact-enriched answers beyond standalone AI models</li>
              <li>Supports real-time updates as new knowledge is added to the graph</li>
              <li>Enhances responses with definitions, examples, and contextual references from structured data</li>
            </ul>
          </div>
          
          <div className="about-section">
            <h3>Key Features</h3>
            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">🔄</div>
                <h4>Conversational AI + Knowledge Graph</h4>
                <p>Combines NLP (LLM) with structured cybersecurity data</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🔍</div>
                <h4>Context-Aware Answers</h4>
                <p>Leverages relationships and hierarchies for deeper insights</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">⚡</div>
                <h4>Real-Time Data Access</h4>
                <p>Fetches the latest domain-specific facts dynamically</p>
              </div>
              <div className="feature-card">
                <div className="feature-icon">🧠</div>
                <h4>Adaptive Learning</h4>
                <p>Updates the knowledge graph with new insights over time</p>
              </div>
            </div>
          </div>
          
          <div className="about-section">
            <h3>How It Works</h3>
            <div className="how-it-works">
              <div className="step">
                <div className="step-number">1</div>
                <p>User submits a cybersecurity question</p>
              </div>
              <div className="step-arrow">→</div>
              <div className="step">
                <div className="step-number">2</div>
                <p>System processes the query via NLP</p>
              </div>
              <div className="step-arrow">→</div>
              <div className="step">
                <div className="step-number">3</div>
                <p>Knowledge graph provides contextual data</p>
              </div>
              <div className="step-arrow">→</div>
              <div className="step">
                <div className="step-number">4</div>
                <p>AI generates enriched, context-aware response</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="about-footer">
          <button className="start-button" onClick={handleClose}>Start Using the Assistant</button>
        </div>
      </div>
    </div>
  ) : null;
};

export default AboutSection;