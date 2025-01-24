import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, Typography, Alert } from '@mui/material';
import { styled } from '@mui/material/styles';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

const ChatBox = styled(Paper)(({ theme }) => ({
  height: '600px',
  maxWidth: '800px',
  margin: '0 auto',
  display: 'flex',
  flexDirection: 'column',
  padding: theme.spacing(2),
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
  flexGrow: 1,
  overflowY: 'auto',
  marginBottom: theme.spacing(2),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(1),
}));

// PUBLIC_INTERFACE
const ChatContainer = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (message) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Add user message to chat
      const userMessage = { text: message, isUser: true };
      setMessages(prev => [...prev, userMessage]);

      // TODO: Implement actual API call here
      // For now, simulate a response
      const response = await new Promise(resolve => 
        setTimeout(() => resolve("I received your message: " + message), 1000)
      );

      // Add bot response to chat
      const botMessage = { text: response, isUser: false };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Error sending message:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ChatBox elevation={3}>
      <MessagesContainer>
        {messages.map((msg, index) => (
          <ChatMessage
            key={index}
            message={msg.text}
            isUser={msg.isUser}
          />
        ))}
        <div ref={messagesEndRef} />
      </MessagesContainer>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <ChatInput 
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </ChatBox>
  );
};

export default ChatContainer;