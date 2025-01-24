import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ChatMessage from '../ChatMessage';

const theme = createTheme();

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ChatMessage', () => {
  test('Renders user message correctly', () => {
    const message = 'Hello, this is a user message';
    renderWithTheme(<ChatMessage message={message} isUser={true} />);
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  test('Renders bot message correctly', () => {
    const message = 'Hello, this is a bot message';
    renderWithTheme(<ChatMessage message={message} isUser={false} />);
    expect(screen.getByText(message)).toBeInTheDocument();
  });

  test('Applies correct styling based on message type', () => {
    const message = 'Test message';
    const { container: userContainer } = renderWithTheme(
      <ChatMessage message={message} isUser={true} />
    );
    const { container: botContainer } = renderWithTheme(
      <ChatMessage message={message} isUser={false} />
    );

    const userMessage = userContainer.firstChild;
    const botMessage = botContainer.firstChild;

    expect(userMessage).toHaveStyle({ justifyContent: 'flex-end' });
    expect(botMessage).toHaveStyle({ justifyContent: 'flex-start' });
  });

  test('Handles markdown content properly', () => {
    const markdownMessage = '**Bold** and *italic* text';
    renderWithTheme(<ChatMessage message={markdownMessage} isUser={true} />);
    expect(screen.getByText(markdownMessage)).toBeInTheDocument();
  });
});