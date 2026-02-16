from unittest.mock import MagicMock
from src.core.pipeline import RAGManager
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.messages import AIMessage

chunks = [
    Document(page_content="Text 1", metadata={"title": "mock1"}),
    Document(page_content="Text 2", metadata={"title": "mock2"}),
    Document(page_content="Text 3", metadata={"title": "mock3"}),
]
ai_message = AIMessage(content="AI response")


def test_process_and_store_documents():
    """Test processing and storing documents using mocked document processor and vector store."""
    mock_doc_processor = MagicMock()
    mock_vector_store = MagicMock()
    mock_doc_processor.process_documents.return_value = chunks
    mock_vector_store.load_documents.return_value = "Stored successfully"
    
    manager = RAGManager()
    manager.document_manager = mock_doc_processor
    manager.vector_store = mock_vector_store
    
    result = manager.process_and_store_documents(Path("/fake/path"))
    
    mock_doc_processor.process_documents.assert_called_once()
    mock_vector_store.load_documents.assert_called_once_with(chunks)
    assert result == "Stored successfully"
    

def test_query_documents():
    """Test querying documents using a mocked vector store and verify the AI response."""
    mock_vector_store = MagicMock()
    mock_vector_store.search.return_value = ai_message
    
    manager = RAGManager()
    manager.vector_store = mock_vector_store
    
    result = manager.query_documents("sample query")
    
    mock_vector_store.search.assert_called_once_with("sample query")
    assert result == "AI response"
    

def test_delete_document():
    """Test deleting a document using a mocked vector store and verify the deletion result."""
    mock_vector_store = MagicMock()
    mock_vector_store.delete_document.return_value = "Deleted Text 1"
    
    manager = RAGManager()
    manager.vector_store = mock_vector_store
    
    result = manager.delete_document("Text 1")
    
    mock_vector_store.delete_document.assert_called_once_with("Text 1")
    assert "Deleted Text 1" in result


def test_get_all_documents():
    """Test retrieving all documents using a mocked vector store and verify the returned list."""
    mock_vector_store = MagicMock()
    mock_vector_store.get_documents.return_value = ["Text 1", "Text 2"]
    
    manager = RAGManager()
    manager.vector_store = mock_vector_store
    
    result = manager.get_all_documents()
    
    mock_vector_store.get_documents.assert_called_once()
    assert result == ["Text 1", "Text 2"]
    

def test_flush_db():
    """Test flushing the database using a mocked vector store and verify the flush result."""
    mock_vector_store = MagicMock()
    mock_vector_store.flush_store.return_value = "DB cleared"
    
    manager = RAGManager()
    manager.vector_store = mock_vector_store
    
    result = manager.flush_db()
    
    mock_vector_store.flush_store.assert_called_once()
    assert result == "DB cleared"
    

def test_update_document():
    """Test updating a document by deleting and re-adding it using mocked components."""
    mock_doc_processor = MagicMock()
    mock_vector_store = MagicMock()
    
    mock_doc_processor.process_documents.return_value = chunks
    mock_vector_store.load_documents.return_value = "Updated successfully"
    
    manager = RAGManager()
    manager.document_manager = mock_doc_processor
    manager.vector_store = mock_vector_store
    
    result = manager.update_document(Path("/fake/path"), "Text 1")
    
    mock_vector_store.delete_document.assert_called_once_with("Text 1")
    mock_doc_processor.process_documents.assert_called_once()
    mock_vector_store.load_documents.assert_called_once()
    assert result == "Updated successfully"
