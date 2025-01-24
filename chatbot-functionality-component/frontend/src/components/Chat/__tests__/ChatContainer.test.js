import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ChatContainer from '../ChatContainer';

const theme = createTheme();

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ChatContainer', () => {
  test('Manages chat history correctly', async () => {
    renderWithTheme(<ChatContainer />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await userEvent.type(input, 'Hello{enter}');
    
    // Wait for both user message and bot response
    await waitFor(() => {
      expect(screen.getByText('Hello')).toBeInTheDocument();
      expect(screen.getByText(/I received your message: Hello/)).toBeInTheDocument();
    });
  });

  test('Handles message sending', async () => {
    renderWithTheme(<ChatContainer />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await userEvent.type(input, 'Test message{enter}');
    
    // Check loading state
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    
    // Wait for response
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
      expect(screen.getByText(/I received your message: Test message/)).toBeInTheDocument();
    });
  });

  test('Implements auto-scroll behavior', async () => {
    const { container } = renderWithTheme(<ChatContainer />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    
    // Send multiple messages to test scrolling
    for (let i = 0; i < 3; i++) {
      await userEvent.type(input, `Message ${i}{enter}`);
    }
    
    // Wait for all messages to be displayed
    await waitFor(() => {
      expect(screen.getAllByText(/Message \d/)).toHaveLength(3);
    });
    
    const messagesContainer = container.querySelector('[class*="MessagesContainer"]');
    expect(messagesContainer.scrollHeight).toBeGreaterThan(messagesContainer.clientHeight);
  });

  test('Shows error states properly', async () => {
    // Mock console.error to prevent error logging
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    
    renderWithTheme(<ChatContainer />);
    
    // Force an error by mocking the Promise to reject
    jest.spyOn(global, 'Promise').mockImplementationOnce(() => {
      return {
        then: () => {
          throw new Error('Network error');
        }
      };
    });
    
    const input = screen.getByPlaceholderText('Type your message...');
    await userEvent.type(input, 'Error test{enter}');
    
    await waitFor(() => {
      expect(screen.getByText('Failed to send message. Please try again.')).toBeInTheDocument();
    });
    
    consoleError.mockRestore();
  });
});