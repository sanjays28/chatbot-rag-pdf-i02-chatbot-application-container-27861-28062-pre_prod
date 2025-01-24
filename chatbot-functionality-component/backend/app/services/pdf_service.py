"""PDF Service for handling PDF file operations including upload, validation, and storage."""

import os
import magic
import boto3
from typing import Tuple, Dict, Any
import logging
from PyPDF2 import PdfReader
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class PDFService:
    """Service class for handling PDF file operations."""
    
    def __init__(self, s3_bucket: str = os.getenv('AWS_S3_BUCKET')):
        """Initialize the PDF service.
        
        Args:
            s3_bucket (str): The name of the S3 bucket for storage. Defaults to AWS_S3_BUCKET env var.
        """
        self.s3_client = boto3.client('s3')
        self.s3_bucket = s3_bucket
        self.mime = magic.Magic(mime=True)
        self.max_file_size = 50 * 1024 * 1024  # 50MB max file size

    # PUBLIC_INTERFACE
    def validate_pdf(self, file_path: str) -> Tuple[bool, str]:
        """Validate a PDF file.
        
        Args:
            file_path (str): Path to the PDF file.
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False, f"File size exceeds maximum limit of {self.max_file_size/1024/1024}MB"
            
            # Check MIME type
            mime_type = self.mime.from_file(file_path)
            if mime_type != 'application/pdf':
                return False, "File is not a valid PDF"
            
            # Verify PDF structure
            try:
                PdfReader(file_path)
            except Exception as e:
                return False, f"Invalid PDF structure: {str(e)}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating PDF: {str(e)}")
            return False, f"Validation error: {str(e)}"

    # PUBLIC_INTERFACE
    def upload_to_s3(self, file_path: str, object_name: str = None) -> Tuple[bool, str]:
        """Upload a file to S3 bucket.
        
        Args:
            file_path (str): Path to the file to upload.
            object_name (str, optional): S3 object name. If not specified, file_path is used.
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.s3_client.upload_file(file_path, self.s3_bucket, object_name)
            return True, ""
        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return False, f"Upload failed: {str(e)}"

    # PUBLIC_INTERFACE
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a PDF file.
        
        Args:
            file_path (str): Path to the PDF file.
            
        Returns:
            Dict[str, Any]: Dictionary containing metadata
        """
        try:
            pdf = PdfReader(file_path)
            metadata = {
                'num_pages': len(pdf.pages),
                'encrypted': pdf.is_encrypted,
                'info': pdf.metadata if pdf.metadata else {},
                'size': os.path.getsize(file_path)
            }
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}

    # PUBLIC_INTERFACE
    def process_pdf_upload(self, file_path: str, object_name: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Process a PDF upload including validation, metadata extraction, and storage.
        
        Args:
            file_path (str): Path to the PDF file.
            object_name (str, optional): S3 object name. If not specified, file_path is used.
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (success, message, metadata)
        """
        # Validate PDF
        is_valid, error_msg = self.validate_pdf(file_path)
        if not is_valid:
            return False, error_msg, {}

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        if not metadata:
            return False, "Failed to extract metadata", {}

        # Upload to S3
        upload_success, upload_error = self.upload_to_s3(file_path, object_name)
        if not upload_success:
            return False, upload_error, {}

        return True, "PDF processed successfully", metadata