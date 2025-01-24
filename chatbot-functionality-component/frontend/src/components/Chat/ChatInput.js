import React, { useState } from 'react';
import { Paper, InputBase, IconButton, CircularProgress } from '@mui/material';
import { Send as SendIcon } from '@mui/icons-material';
import { styled } from '@mui/material/styles';

const InputContainer = styled(Paper)(({ theme }) => ({
  padding: '2px 4px',
  display: 'flex',
  alignItems: 'center',
  width: '100%',
  marginTop: theme.spacing(2),
}));

// PUBLIC_INTERFACE
const ChatInput = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <InputContainer elevation={1}>
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={isLoading}
          multiline
          maxRows={4}
        />
        <IconButton 
          type="submit" 
          sx={{ p: '10px' }} 
          disabled={!message.trim() || isLoading}
          color="primary"
        >
          {isLoading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </InputContainer>
    </form>
  );
};

export default ChatInput;