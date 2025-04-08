import React, { useState } from 'react';
import Header from '../components/Header';
import ProblemDisplay from '../components/ProblemDisplay';
import ChatBox from '../components/ChatBox';
import API_URL from '../config/api';

function PhysicsProblemPage() {
  const [messages, setMessages] = useState([]);

  // Sample physics problem data
  const problem = {
    title: "Socratic Sample Problem",
    description: "What is the result of x + y?",
    imageUrl: "" // Insert an image URL later if desired
  };

  const handleSendMessage = async (text) => {
    // Add the user's message
    const userMessage = { sender: 'User', text };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Passing problem_id and the user's query
        body: JSON.stringify({
          problem_id: 1, // Adjust based on your actual problem identifier
          query: text,
        }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      const aiMessage = { sender: 'AI', text: data.response };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error fetching AI response:', error);
      const errorMessage = { sender: 'System', text: 'Error: Unable to get response from AI.' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div>
      <Header />
      <div style={{ padding: '1rem' }}>
        <ProblemDisplay problem={problem} />
        <ChatBox onSendMessage={handleSendMessage} messages={messages} />
      </div>
    </div>
  );
}

export default PhysicsProblemPage;
