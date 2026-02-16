import pytest
from pathlib import Path
from collections import defaultdict

from langchain_core.documents import Document

from src.core.ingestion import DocumentProcessor


def test_ingestion_init():
    """Test initialization of DocumentProcessor with default values."""
    processor = DocumentProcessor()
    
    assert isinstance(processor.chunk_size, int)
    assert processor.chunk_size > 0
    
    assert isinstance(processor.chunk_overlap, int)
    assert processor.chunk_overlap >= 0
    
    assert isinstance(processor.splitter_type, str)
    assert processor.splitter_type in ["recursive", "token"]


def test_invalid_splitter_type():
    """Test that DocumentProcessor raises RuntimeError with invalid splitter type."""
    processor = DocumentProcessor()
    processor.splitter_type = "invalid_type"
    
    mock_docs = [Document(page_content="test", metadata={"title": "doc1"})]
    
    with pytest.raises(RuntimeError, match="Unsupported splitter type"):
        processor.split_documents(mock_docs)


def test_nonexistent_directory():
    """Test that loading documents from a nonexistent directory raises RuntimeError."""
    processor = DocumentProcessor()
    
    nonexistent_path = Path("tests/nonexistent_directory")
    
    with pytest.raises(RuntimeError):
        processor.load_documents_from_directory(nonexistent_path)


def test_empty_directory():
    """Test behavior with empty directory."""
    processor = DocumentProcessor()
    
    # Create a temporary empty directory for testing
    empty_dir = Path("tests/empty_test_dir")
    empty_dir.mkdir(exist_ok=True)
    
    try:
        documents = processor.load_documents_from_directory(empty_dir)
        assert isinstance(documents, list)
        assert len(documents) == 0
    finally:
        empty_dir.rmdir()
        

# Integration test, maybe moving it in a separate file later
def test_document_loading():
    """Test loading documents from the mock documents directory."""
    processor = DocumentProcessor()
    
    mock_path = Path("tests/mock_docs")
    documents = processor.load_documents_from_directory(mock_path)
    
    for doc in documents:
        assert hasattr(doc, 'page_content')
        assert len(doc.page_content) > 0
        assert hasattr(doc, 'metadata')


def test_convert_to_lc_documents():
    """Test conversion of mock results to LangChain documents with proper metadata handling."""
    processor = DocumentProcessor()

    class MockResult:
        def __init__(self, content, metadata):
            self.content = content
            self.metadata = metadata

    results = [
        MockResult("Text 1", {"page": 1}),
        MockResult("Text 2", {"page": 2}),
        MockResult("Text 3", None),
    ]

    docs = processor.convert_to_lc_documents(results)

    assert len(docs) == 3
    assert docs[0].metadata == {"page": "1"}
    assert docs[2].metadata == {}

    
def test_add_chunk_ids():
    """Test adding chunk IDs to documents with proper sequential numbering per document."""
    processor = DocumentProcessor()
    
    mock_path = Path("tests/mock_docs")
    documents = processor.load_documents_from_directory(mock_path)
    
    chunks_with_ids = processor.add_chunk_ids(documents, mock_path)
    
    assert isinstance(chunks_with_ids, list)
    assert len(chunks_with_ids) > 0
    
    # Check that all chunks have the expected metadata
    for chunk in chunks_with_ids:
        assert 'chunk' in chunk.metadata
        assert 'title' in chunk.metadata
        assert isinstance(chunk.metadata['chunk'], int)
        assert chunk.metadata['chunk'] >= 0
    
    # Group chunks by their source document to verify sequential numbering
    chunks_by_title = defaultdict(list)
    for chunk in chunks_with_ids:
        title = chunk.metadata['title']
        chunks_by_title[title].append(chunk)
    
    # Verify that chunk numbers are sequential starting from 0 for each document
    for title, chunks in chunks_by_title.items():
        chunk_numbers = [c.metadata['chunk'] for c in chunks]
        expected_numbers = list(range(len(chunks)))
        assert sorted(chunk_numbers) == expected_numbers


def test_process_documents():
    """Test processing documents from the mock documents directory with chunking and metadata."""
    processor = DocumentProcessor()
    
    mock_path = Path("tests/mock_docs")
    processed_docs = processor.process_documents(mock_path)
    
    assert isinstance(processed_docs, list)
    assert len(processed_docs) > 0
    
    for doc in processed_docs:
        assert hasattr(doc, 'page_content')
        assert len(doc.page_content) > 0
        assert hasattr(doc, 'metadata')
        assert 'chunk' in doc.metadata
        assert 'title' in doc.metadata
