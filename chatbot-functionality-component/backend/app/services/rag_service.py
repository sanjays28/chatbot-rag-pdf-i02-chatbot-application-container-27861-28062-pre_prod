"""RAG Service for handling text extraction, embedding generation, and vector storage."""

import os
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PyPDF2 import PdfReader
import faiss
from sentence_transformers import SentenceTransformer
from .pdf_service import PDFService

logger = logging.getLogger(__name__)

class RAGService:
    """Service class for handling RAG operations including text extraction and vector storage."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', chunk_size: int = 500):
        """Initialize the RAG service.
        
        Args:
            model_name (str): Name of the sentence-transformer model to use
            chunk_size (int): Size of text chunks for processing
        """
        self.model = SentenceTransformer(model_name)
        self.chunk_size = chunk_size
        self.pdf_service = PDFService()
        self.index = None
        self.text_chunks = []
        self.document_map = {}  # Maps chunk indices to document information

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from a PDF file.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        try:
            pdf = PdfReader(file_path)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of approximately equal size.
        
        Args:
            text (str): Text to split into chunks
            
        Returns:
            List[str]: List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_size += len(word) + 1  # +1 for space
            if current_size > self.chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks

    # PUBLIC_INTERFACE
    def process_document(self, file_path: str, document_id: str) -> Tuple[bool, str]:
        """Process a document for RAG operations.
        
        Args:
            file_path (str): Path to the PDF file
            document_id (str): Unique identifier for the document
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Validate PDF
            is_valid, error_msg = self.pdf_service.validate_pdf(file_path)
            if not is_valid:
                return False, error_msg

            # Extract text
            text = self._extract_text_from_pdf(file_path)
            if not text.strip():
                return False, "No text content found in document"

            # Create chunks
            chunks = self._chunk_text(text)
            
            # Generate embeddings
            embeddings = self.model.encode(chunks)
            
            # Initialize FAISS index if needed
            if self.index is None:
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
            
            # Add to index
            start_idx = len(self.text_chunks)
            self.index.add(embeddings)
            
            # Store chunks and document mapping
            self.text_chunks.extend(chunks)
            for i in range(len(chunks)):
                self.document_map[start_idx + i] = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            
            return True, "Document processed successfully"
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return False, f"Processing error: {str(e)}"

    # PUBLIC_INTERFACE
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant text chunks based on a query.
        
        Args:
            query (str): Search query
            k (int): Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of search results with text and metadata
        """
        try:
            if not self.index:
                return []

            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Search index
            distances, indices = self.index.search(query_embedding, k)
            
            # Format results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.text_chunks):
                    results.append({
                        'text': self.text_chunks[idx],
                        'score': float(distances[0][i]),
                        'document_info': self.document_map.get(idx, {})
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            return []

    # PUBLIC_INTERFACE
    def get_document_chunks(self, document_id: str) -> List[str]:
        """Get all text chunks for a specific document.
        
        Args:
            document_id (str): Document identifier
            
        Returns:
            List[str]: List of text chunks for the document
        """
        try:
            chunks = []
            for idx, chunk in enumerate(self.text_chunks):
                if self.document_map.get(idx, {}).get('document_id') == document_id:
                    chunks.append(chunk)
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {str(e)}")
            return []

    # PUBLIC_INTERFACE
    def clear_document(self, document_id: str) -> bool:
        """Remove a document's chunks and embeddings from storage.
        
        Args:
            document_id (str): Document identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Find indices to remove
            indices_to_remove = []
            for idx, info in self.document_map.items():
                if info['document_id'] == document_id:
                    indices_to_remove.append(idx)
            
            if not indices_to_remove:
                return True
            
            # Create new index without the document
            remaining_indices = [i for i in range(len(self.text_chunks)) 
                              if i not in indices_to_remove]
            
            if not remaining_indices:
                self.index = None
                self.text_chunks = []
                self.document_map = {}
                return True
            
            # Get remaining embeddings
            remaining_chunks = [self.text_chunks[i] for i in remaining_indices]
            embeddings = self.model.encode(remaining_chunks)
            
            # Create new index
            dimension = embeddings.shape[1]
            new_index = faiss.IndexFlatL2(dimension)
            new_index.add(embeddings)
            
            # Update storage
            self.index = new_index
            self.text_chunks = remaining_chunks
            self.document_map = {
                new_idx: self.document_map[old_idx]
                for new_idx, old_idx in enumerate(remaining_indices)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error clearing document: {str(e)}")
            return False