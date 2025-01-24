"""Unit tests for PDF Service."""

import os
import pytest
from unittest.mock import Mock, patch
from app.services.pdf_service import PDFService
from botocore.exceptions import ClientError

@pytest.fixture
def pdf_service():
    """Create a PDFService instance for testing."""
    with patch('boto3.client') as mock_boto3:
        service = PDFService('test-bucket')
        service.s3_client = mock_boto3.return_value
        return service

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    # Create a minimal PDF file
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n%EOF\n')
    return str(pdf_path)

class TestPDFService:
    """Test cases for PDFService."""

    def test_validate_pdf_nonexistent_file(self, pdf_service):
        """Test validation of non-existent file."""
        is_valid, error = pdf_service.validate_pdf("/nonexistent/path.pdf")
        assert not is_valid
        assert "File does not exist" in error

    def test_validate_pdf_size_limit(self, pdf_service, tmp_path):
        """Test validation of file exceeding size limit."""
        large_file = tmp_path / "large.pdf"
        with open(large_file, 'wb') as f:
            f.write(b'%PDF-1.4\n' + b'0' * (51 * 1024 * 1024) + b'\n%EOF\n')
        
        is_valid, error = pdf_service.validate_pdf(str(large_file))
        assert not is_valid
        assert "File size exceeds maximum limit" in error

    @patch('magic.Magic')
    def test_validate_pdf_invalid_mime(self, mock_magic, pdf_service, sample_pdf):
        """Test validation of file with invalid MIME type."""
        mock_magic.return_value.from_file.return_value = 'text/plain'
        is_valid, error = pdf_service.validate_pdf(sample_pdf)
        assert not is_valid
        assert "File is not a valid PDF" in error

    @patch('magic.Magic')
    def test_validate_pdf_valid(self, mock_magic, pdf_service, sample_pdf):
        """Test validation of valid PDF file."""
        mock_magic.return_value.from_file.return_value = 'application/pdf'
        is_valid, error = pdf_service.validate_pdf(sample_pdf)
        assert is_valid
        assert error == ""

    def test_upload_to_s3_success(self, pdf_service, sample_pdf):
        """Test successful S3 upload."""
        success, error = pdf_service.upload_to_s3(sample_pdf)
        assert success
        assert error == ""
        pdf_service.s3_client.upload_file.assert_called_once_with(
            sample_pdf, 'test-bucket', os.path.basename(sample_pdf)
        )

    def test_upload_to_s3_failure(self, pdf_service, sample_pdf):
        """Test S3 upload failure."""
        pdf_service.s3_client.upload_file.side_effect = ClientError(
            {'Error': {'Code': 'TestException', 'Message': 'Test error'}},
            'upload_file'
        )
        success, error = pdf_service.upload_to_s3(sample_pdf)
        assert not success
        assert "Upload failed" in error

    def test_extract_metadata_success(self, pdf_service, sample_pdf):
        """Test successful metadata extraction."""
        metadata = pdf_service.extract_metadata(sample_pdf)
        assert isinstance(metadata, dict)
        assert 'num_pages' in metadata
        assert 'encrypted' in metadata
        assert 'info' in metadata
        assert 'size' in metadata

    def test_extract_metadata_failure(self, pdf_service):
        """Test metadata extraction failure."""
        metadata = pdf_service.extract_metadata("/nonexistent/path.pdf")
        assert metadata == {}

    def test_process_pdf_upload_success(self, pdf_service, sample_pdf):
        """Test successful PDF processing."""
        with patch.object(pdf_service, 'validate_pdf', return_value=(True, "")), \
             patch.object(pdf_service, 'extract_metadata', return_value={'num_pages': 1}), \
             patch.object(pdf_service, 'upload_to_s3', return_value=(True, "")):
            
            success, message, metadata = pdf_service.process_pdf_upload(sample_pdf)
            assert success
            assert "PDF processed successfully" in message
            assert metadata == {'num_pages': 1}

    def test_process_pdf_upload_validation_failure(self, pdf_service, sample_pdf):
        """Test PDF processing with validation failure."""
        with patch.object(pdf_service, 'validate_pdf', return_value=(False, "Invalid PDF")):
            success, message, metadata = pdf_service.process_pdf_upload(sample_pdf)
            assert not success
            assert "Invalid PDF" in message
            assert metadata == {}