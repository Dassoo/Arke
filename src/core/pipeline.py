from core.ingestion import DocumentProcessor
from core.storage import QdrantVectorRepository

from pathlib import Path


class RAGManager:
    """
    Manages the Retrieval-Augmented Generation (RAG) pipeline operations.
    
    This class serves as the main orchestrator for the RAG system, coordinating
    document processing, storage, retrieval, and management operations. It provides
    a high-level interface for interacting with the knowledge base.
    
    Attributes:
        document_manager (DocumentProcessor): Handles document loading and processing
        vector_store (QdrantVectorRepository): Manages vector storage and retrieval
    """
    def __init__(self):
        """
        Initialize a RAGManager instance.
        
        Sets up the document processor and vector store connection using 
        a vector database.
        """
        self.document_manager = DocumentProcessor()
        self.vector_store = QdrantVectorRepository()
    
    def process_and_store_documents(self, input_folder: Path) -> str:
        """
        Complete input pipeline: load, process, and store documents.
        
        Orchestrates the full document ingestion workflow:
        1. Load documents from directory
        2. Split into manageable chunks
        3. Index into the vector database
        
        Args:
            input_folder (Path): Path to directory containing documents to process
            
        Returns:
            str: Success message from the vector store
        """
        chunks = self.document_manager.process_documents(input_folder)
        result = self.vector_store.load_documents(chunks)
        return result
    
    def query_documents(self, query: str):
        """
        Query the RAG system and return generated response.
        
        Performs semantic search on the vector database and uses a language model
        to generate a response based on the retrieved context.
        
        Args:
            query (str): Search query to process
            
        Returns:
            str: AI-generated response content
        """
        response = self.vector_store.search(query)
        return response.content
    
    def delete_document(self, document_title: str) -> str:
        """
        Delete a specific document from the RAG system.
        
        Removes all chunks associated with the specified document title from
        the vector database.
        
        Args:
            document_title (str): Title of the document to delete
            
        Returns:
            str: Success message or not found indication
        """
        result = self.vector_store.delete_document(document_title)
        return result if result is not None else f"No document found with title '{document_title}'"
    
    def get_all_documents(self) -> list[str]:
        """
        Get list of all stored document titles.
        
        Returns:
            list[str]: Sorted list of document titles in the knowledge base
        """
        result = self.vector_store.get_documents()
        return result if result is not None else []
    
    def flush_db(self) -> str:
        """
        Clear all data from the RAG system.
        
        WARNING: This operation is irreversible and deletes all stored documents.
        
        Returns:
            str: Confirmation message indicating database has been cleared
        """
        return self.vector_store.flush_store()
    
    def update_document(self, input_folder: Path, document_title: str) -> str:
        """
        Update or add documents to the RAG system.
        
        If a document title is provided, it first deletes any existing chunks
        with that title before re-processing and storing the new content.
        
        Args:
            input_folder (Path): Path to directory containing updated documents
            document_title (str): Title of the document to update
            
        Returns:
            str: Success message from the vector store
        """
        if document_title:
            try:
                self.delete_document(document_title)
            except Exception:
                # Intentionally ignore errors if the document does not exist
                pass
                
        result = self.process_and_store_documents(input_folder)
        return result if result is not None else "Document update completed"
