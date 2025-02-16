import React, { useState } from 'react';
import Header from '../components/Header';
import ProblemDisplay from '../components/ProblemDisplay';
import ChatBox from '../components/ChatBox';

function PhysicsProblemPage() {
  const [messages, setMessages] = useState([]);

  // Sample physics problem data
  const problem = {
    title: "Newton's Laws",
    description: "A 10kg block is on a 30° incline. Calculate the net force acting on the block if friction is negligible.",
    imageUrl: "" // Insert an image URL later if desired
  };

  const handleSendMessage = (text) => {
    // Add the user's message
    const userMessage = { sender: 'User', text };
    setMessages(prev => [...prev, userMessage]);
    
    // Simulate an AI response after 1 second
    setTimeout(() => {
      const aiResponse = { sender: 'AI', text: "This is a simulated AI response. Please ask for more details if needed." };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
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
