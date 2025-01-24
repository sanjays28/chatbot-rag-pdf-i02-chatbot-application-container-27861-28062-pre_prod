"""Integration tests for system performance under various load conditions."""

import pytest
import time
import concurrent.futures
from io import BytesIO

def test_concurrent_uploads(test_client, init_database, auth_headers, tmp_path):
    """Test system performance with concurrent PDF uploads."""
    # Create multiple test PDFs
    pdf_files = []
    for i in range(5):
        pdf_path = tmp_path / f"test{i}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(f'%PDF-1.4\nTest content for concurrent upload {i}\n%EOF\n'.encode())
        pdf_files.append(pdf_path)
    
    def upload_file(pdf_path):
        with open(pdf_path, 'rb') as pdf_file:
            return test_client.post('/api/upload',
                                  data={'file': (pdf_file, pdf_path.name)},
                                  headers=auth_headers)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(upload_file, pdf) for pdf in pdf_files]
        responses = [future.result() for future in futures]
    
    end_time = time.time()
    upload_time = end_time - start_time
    
    # Verify all uploads were successful
    assert all(response.status_code == 200 for response in responses)
    assert upload_time < 30  # Maximum acceptable time for concurrent uploads

def test_concurrent_chat_sessions(test_client, init_database, auth_headers, sample_pdf):
    """Test system performance with multiple concurrent chat sessions."""
    # Create initial document
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    # Create multiple chat sessions
    session_ids = []
    for _ in range(5):
        response = test_client.post('/api/chat/sessions',
                                  json={'document_id': document_id},
                                  headers=auth_headers)
        assert response.status_code == 200
        session_ids.append(response.get_json()['session_id'])
    
    def send_message(session_id):
        return test_client.post(f'/api/chat/sessions/{session_id}/messages',
                              json={'message': 'Test concurrent message'},
                              headers=auth_headers)
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_message, session_id) 
                  for session_id in session_ids]
        responses = [future.result() for future in futures]
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Verify all messages were processed successfully
    assert all(response.status_code == 200 for response in responses)
    assert processing_time < 20  # Maximum acceptable time for concurrent messages

def test_large_document_processing(test_client, init_database, auth_headers, tmp_path):
    """Test system performance with large PDF documents."""
    # Create a large PDF file (5MB)
    large_pdf_path = tmp_path / "large.pdf"
    with open(large_pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n' + b'x' * (5 * 1024 * 1024) + b'\n%EOF\n')
    
    start_time = time.time()
    with open(large_pdf_path, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'large.pdf')},
                                  headers=auth_headers)
    
    assert response.status_code == 200
    document_id = response.get_json()['document_id']
    
    # Wait for processing to complete
    max_wait = 60  # Maximum wait time in seconds
    processed = False
    while time.time() - start_time < max_wait:
        with test_client.application.app_context():
            from app.models import Document
            doc = Document.query.get(document_id)
            if doc.status == 'processed':
                processed = True
                break
        time.sleep(1)
    
    assert processed
    processing_time = time.time() - start_time
    assert processing_time < max_wait

def test_system_recovery(test_client, init_database, auth_headers, sample_pdf):
    """Test system recovery after high load."""
    # Generate high load
    concurrent_requests = 10
    
    def make_request():
        with open(sample_pdf, 'rb') as pdf_file:
            return test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    
    # Execute concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
        responses = [future.result() for future in futures]
    
    # Test system recovery by making a normal request
    response = test_client.post('/api/upload',
                              data={'file': (open(sample_pdf, 'rb'), 'recovery.pdf')},
                              headers=auth_headers)
    assert response.status_code == 200
    
    # Verify chat functionality after load
    document_id = response.get_json()['document_id']
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': document_id},
                              headers=auth_headers)
    assert response.status_code == 200
    session_id = response.get_json()['session_id']
    
    response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                              json={'message': 'Test system recovery'},
                              headers=auth_headers)
    assert response.status_code == 200

def test_memory_usage(test_client, init_database, auth_headers, sample_pdf):
    """Test system memory usage under load."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Create multiple sessions and send messages
    num_sessions = 10
    messages_per_session = 5
    
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    sessions = []
    for _ in range(num_sessions):
        response = test_client.post('/api/chat/sessions',
                                  json={'document_id': document_id},
                                  headers=auth_headers)
        sessions.append(response.get_json()['session_id'])
    
    for session_id in sessions:
        for i in range(messages_per_session):
            response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                      json={'message': f'Test message {i}'},
                                      headers=auth_headers)
            assert response.status_code == 200
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Check memory increase is within acceptable limits (e.g., less than 500MB)
    assert memory_increase < 500 * 1024 * 1024  # 500MB in bytes