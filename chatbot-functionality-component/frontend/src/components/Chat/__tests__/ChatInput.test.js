import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import ChatInput from '../ChatInput';

const theme = createTheme();

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('ChatInput', () => {
  test('Handles user input correctly', async () => {
    const onSendMessage = jest.fn();
    renderWithTheme(<ChatInput onSendMessage={onSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await userEvent.type(input, 'Hello, world!');
    
    expect(input).toHaveValue('Hello, world!');
  });

  test('Submits message on enter key', async () => {
    const onSendMessage = jest.fn();
    renderWithTheme(<ChatInput onSendMessage={onSendMessage} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    await userEvent.type(input, 'Test message{enter}');
    
    expect(onSendMessage).toHaveBeenCalledWith('Test message');
    expect(input).toHaveValue('');
  });

  test('Shows loading state while sending', () => {
    renderWithTheme(<ChatInput onSendMessage={() => {}} isLoading={true} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const submitButton = screen.getByRole('button');
    
    expect(input).toBeDisabled();
    expect(submitButton).toBeDisabled();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('Handles empty input validation', async () => {
    const onSendMessage = jest.fn();
    renderWithTheme(<ChatInput onSendMessage={onSendMessage} isLoading={false} />);
    
    const submitButton = screen.getByRole('button');
    fireEvent.click(submitButton);
    
    expect(onSendMessage).not.toHaveBeenCalled();
  });
});