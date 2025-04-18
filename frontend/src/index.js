import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import ChatInterface from './components/ChatInterface';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ChatInterface />
  </React.StrictMode>
);