from unittest.mock import MagicMock 
from langchain_core.documents import Document

from src.core.storage import QdrantVectorRepository

chunks = [
    Document(page_content="Text 1", metadata={"title": "mock1"}),
    Document(page_content="Text 2", metadata={"title": "mock2"}),
    Document(page_content="Text 3", metadata={"title": "mock3"}),
]

def test_qdrant_init():
    """Test initialization of QdrantVectorRepository with client and index name."""
    mock_client = MagicMock()
    repo = QdrantVectorRepository(client=mock_client, index_name="test_index")
    
    assert repo.index_name == "test_index"
    assert repo.client == mock_client


def test_load_documents():
    """Test loading documents into the repository and ensure vectorstore is used."""
    mock_vectorstore = MagicMock()
    mock_client = MagicMock()
    
    repo = QdrantVectorRepository(client=mock_client)
    # Inject the mock vectorstore
    repo._cached_vectorstore = mock_vectorstore
    
    result = repo.load_documents(chunks)
    
    # Ensure vectorstore.add_documents was called
    mock_vectorstore.add_documents.assert_called_once()
    assert "successfully stored" in result

    
def test_get_documents():
    """Test retrieving documents from the repository and ensure correct titles are returned."""
    mock_client = MagicMock()
    mock_client.scroll.side_effect = [
        ([MagicMock(payload={"metadata": {"title": "mock1"}})], None)
    ]
    
    repo = QdrantVectorRepository(client=mock_client)
    titles = repo.get_documents()
    
    assert titles == ["mock1"]
    
    
def test_delete_document():
    """Test deleting a document from the repository and ensure client.delete is called."""
    mock_client = MagicMock()
    repo = QdrantVectorRepository(client=mock_client)
    
    result = repo.delete_document("mock1")
    
    mock_client.delete.assert_called_once()
    assert "Deleted all chunks from book" in result
    

def test_search_no_results():
    """Test searching for a query that returns no results and ensure appropriate message is returned."""
    mock_vectorstore = MagicMock()
    mock_vectorstore.similarity_search.return_value = []
    
    mock_client = MagicMock()
    repo = QdrantVectorRepository(client=mock_client)
    repo._cached_vectorstore = mock_vectorstore
    
    response = repo.search("query")
    assert "No relevant documents found" in response.content
