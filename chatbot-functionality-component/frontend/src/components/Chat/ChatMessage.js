import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { styled } from '@mui/material/styles';

const MessageContainer = styled(Paper)(({ theme, isUser }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(1),
  maxWidth: '70%',
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  backgroundColor: isUser ? theme.palette.primary.light : theme.palette.grey[100],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
}));

// PUBLIC_INTERFACE
const ChatMessage = ({ message, isUser }) => {
  return (
    <Box display="flex" justifyContent={isUser ? 'flex-end' : 'flex-start'}>
      <MessageContainer isUser={isUser} elevation={1}>
        <Typography variant="body1">{message}</Typography>
      </MessageContainer>
    </Box>
  );
};

export default ChatMessage;