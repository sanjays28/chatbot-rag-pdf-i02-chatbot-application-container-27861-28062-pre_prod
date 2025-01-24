import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box } from '@mui/material';
import ChatContainer from './components/Chat/ChatContainer';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        <Container maxWidth="lg">
          <Box py={4}>
            <header className="App-header">
              <h1>Chatbot Functionality Component</h1>
            </header>
            <Box mt={4}>
              <ChatContainer />
            </Box>
          </Box>
        </Container>
      </div>
    </ThemeProvider>
  );
}

export default App;
