import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import axios from 'axios';
import PDFUpload from '../PDFUpload';

jest.mock('axios');

const theme = createTheme();

const renderWithTheme = (component) => {
  return render(
    <ThemeProvider theme={theme}>
      {component}
    </ThemeProvider>
  );
};

describe('PDFUpload', () => {
  const createFile = (name, size, type) => {
    const file = new File([''], name, { type });
    Object.defineProperty(file, 'size', {
      get() {
        return size;
      }
    });
    return file;
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('Handles file drop correctly', async () => {
    const onUploadSuccess = jest.fn();
    const file = createFile('test.pdf', 1024 * 1024, 'application/pdf');
    
    axios.post.mockResolvedValueOnce({ data: { message: 'Upload successful' } });
    
    renderWithTheme(
      <PDFUpload onUploadSuccess={onUploadSuccess} onUploadError={() => {}} />
    );
    
    const dropzone = screen.getByText(/Drag and drop a PDF file here/);
    await userEvent.upload(dropzone, file);
    
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(axios.post).toHaveBeenCalledWith(
      '/api/upload-pdf',
      expect.any(FormData),
      expect.any(Object)
    );
  });

  test('Validates file type and size', async () => {
    const onUploadError = jest.fn();
    const invalidTypeFile = createFile('test.txt', 1024, 'text/plain');
    const largeFile = createFile('large.pdf', 11 * 1024 * 1024, 'application/pdf');
    
    renderWithTheme(
      <PDFUpload onUploadSuccess={() => {}} onUploadError={onUploadError} />
    );
    
    const dropzone = screen.getByText(/Drag and drop a PDF file here/);
    
    // Test invalid file type
    await userEvent.upload(dropzone, invalidTypeFile);
    expect(screen.getByText('Only PDF files are allowed')).toBeInTheDocument();
    expect(onUploadError).toHaveBeenCalledWith('Only PDF files are allowed');
    
    // Test file size limit
    await userEvent.upload(dropzone, largeFile);
    expect(screen.getByText('File size must be less than 10MB')).toBeInTheDocument();
    expect(onUploadError).toHaveBeenCalledWith('File size must be less than 10MB');
  });

  test('Shows upload progress', async () => {
    const file = createFile('test.pdf', 1024 * 1024, 'application/pdf');
    
    axios.post.mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ data: { message: 'Upload successful' } });
        }, 100);
      });
    });
    
    renderWithTheme(
      <PDFUpload onUploadSuccess={() => {}} onUploadError={() => {}} />
    );
    
    const dropzone = screen.getByText(/Drag and drop a PDF file here/);
    await userEvent.upload(dropzone, file);
    
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  test('Displays error messages', async () => {
    const onUploadError = jest.fn();
    const file = createFile('test.pdf', 1024 * 1024, 'application/pdf');
    
    axios.post.mockRejectedValueOnce({
      response: { data: { message: 'Upload failed' } }
    });
    
    renderWithTheme(
      <PDFUpload onUploadSuccess={() => {}} onUploadError={onUploadError} />
    );
    
    const dropzone = screen.getByText(/Drag and drop a PDF file here/);
    await userEvent.upload(dropzone, file);
    
    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
      expect(onUploadError).toHaveBeenCalledWith('Upload failed');
    });
  });
});