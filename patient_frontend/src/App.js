// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [forceReload, setForceReload] = useState(true);
  const [newMessage, setNewMessage] = useState('');

  const apiUrl = process.env.REACT_APP_BFF_URL;

  useEffect(() => {
    if (forceReload) {
      fetch(`${apiUrl}/messages`)
        .then(response => response.json())
        .then(data => setMessages(data))
        .then(setForceReload(false))
        .catch(error => console.error('Error fetching messages:', error));
    }
  }, [forceReload]);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch(`${apiUrl}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: newMessage }),
    })
    .then(response => {
      if (response.ok) {
        setForceReload(true);
        setNewMessage('');
      } else {
        console.error('Failed to send message');
      }
    })
    .catch(error => console.error('Error posting message:', error));
  };

  return (
    <div className="App">
      <h1>Messages</h1>
      <ul>
        {messages.map((msg, index) => (
          <li key={index}>{msg.message}</li>
        ))}
      </ul>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Enter a message"
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default App;
