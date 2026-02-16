from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_core.documents import Document
from kreuzberg import batch_extract_files_sync, ExtractionConfig, OcrConfig

from src.core.config import settings

from collections import defaultdict
from pathlib import Path


class DocumentProcessor:
    """
    Handles document processing operations including loading, splitting, and chunk management.
    
    This class provides a complete pipeline for processing documents from a directory,
    splitting them into manageable chunks, and adding metadata to facilitate retrieval.
    It supports multiple text splitter types and configures settings from the application
    configuration.
    
    Attributes:
        chunk_size (int): Size of each document chunk in characters or tokens
        chunk_overlap (int): Number of overlapping characters/tokens between consecutive chunks
        splitter_type (str): Type of text splitter to use ("recursive" or "token")
    """
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.splitter_type = settings.splitter_type
    
    def convert_to_lc_documents(self, results: list) -> list[Document]:
        """Convert raw extraction results from Kreuzberg into LangChain Document objects.
        
        Args:
            results (list): List of extraction results from Kreuzberg
            
        Returns:
            list[Document]: List of LangChain Document objects with extracted content and metadata
        """
        return [
                Document(
                    page_content=result.content,
                    metadata={
                        k: str(v)
                        for k, v in (result.metadata or {}).items()
                    },
                )
                for result in results
            ]
    
    def load_documents_from_directory(self, input_path: Path) -> list[Document]:
        """
        Load all files from a specified directory into LangChain Document objects.
        
        This method uses the Kreuzberg library to extract content from various file types
        (including PDFs, images, and office documents) with OCR support for image-based files.
        Extracted content is converted to LangChain Document objects with metadata.
        
        Args:
            input_path (Path): Path to the directory containing documents to load
            
        Returns:
            list[Document]: List of LangChain Document objects with extracted content and metadata
            
        Raises:
            RuntimeError: If loading or extraction fails for any reason
        """
        if not input_path.exists() or not input_path.is_dir():
            raise RuntimeError(f"Input path {input_path} does not exist or is not a directory")
        
        try:
            files: list[str | Path] = [f for f in input_path.glob("*") if f.is_file()]
            config = ExtractionConfig(
                ocr=OcrConfig(backend="tesseract", language="eng")
            )

            results = batch_extract_files_sync(files, config=config)
            return self.convert_to_lc_documents(results)
        except Exception as e:
            raise RuntimeError(f"Failed to load documents from {input_path}") from e
    
    def split_documents(self, docs: list[Document]) -> list[Document]:
        """
        Split loaded documents into manageable chunks using the configured text splitter.
        
        Supports two splitter types:
        - "recursive": RecursiveCharacterTextSplitter for semantic chunking
        - "token": TokenTextSplitter for token-based chunking
        
        Args:
            docs (list[Document]): List of Document objects to split
            
        Returns:
            list[Document]: List of split document chunks
            
        Raises:
            RuntimeError: If splitting fails
            ValueError: If an unsupported splitter type is configured
        """
        try:
            if self.splitter_type == "recursive":
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
            elif self.splitter_type == "token":
                text_splitter = TokenTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                )
            else:
                raise ValueError(f"Unsupported splitter type: {self.splitter_type}")

            return text_splitter.split_documents(docs)
        except Exception as e:
            raise RuntimeError(f"Failed to split documents: {str(e)}")
    
    def add_chunk_ids(self, chunks: list[Document], input_folder: Path) -> list[Document]:
        """
        Assign sequential chunk indices to document chunks from the same source.
        
        Each chunk is assigned a "chunk" metadata field with a sequential index
        relative to its source document. If no title metadata exists, it is derived
        from the input folder name.
        
        Args:
            chunks (list[Document]): List of document chunks to process
            input_folder (Path): Source folder path used for default title
            
        Returns:
            list[Document]: Chunks with chunk IDs added to metadata
            
        Raises:
            RuntimeError: If chunk ID assignment fails
        """
        try:
            counters = defaultdict(int)

            for chunk in chunks:
                if "title" not in chunk.metadata:
                    source = input_folder.stem
                    chunk.metadata["title"] = source
                else:
                    source = chunk.metadata["title"]

                key = f"{source}"

                chunk.metadata["chunk"] = counters[key]
                counters[key] += 1

            return chunks
        except Exception as e:
            raise RuntimeError(f"Failed to add chunk IDs: {str(e)}")
    
    def process_documents(self, input_path: Path) -> list[Document]:
        """
        Complete document processing pipeline: load -> split -> add chunk IDs.
        
        Orchestrates the full document processing workflow by calling the individual
        steps in sequence: loading documents from disk, splitting into chunks, and
        adding chunk metadata.
        
        Args:
            input_path (Path): Path to the directory containing documents to process
            
        Returns:
            list[Document]: Processed document chunks ready for storage
            
        Raises:
            RuntimeError: If any step in the processing pipeline fails
        """
        docs = self.load_documents_from_directory(input_path)
        chunks = self.split_documents(docs)
        processed_chunks = self.add_chunk_ids(chunks, input_path)
        return processed_chunks
