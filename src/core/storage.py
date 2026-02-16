from langchain_openai import OpenAIEmbeddings
from langchain_classic.storage import LocalFileStore
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_core.messages import AIMessage
from langchain_core.documents import Document

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue

from src.core.config import settings, config_model
from src.core.prompts import SEARCH_PROMPT
from src.utils.logging import logger

import uuid


class QdrantVectorRepository:
    """
    Handles storage and retrieval of document chunks in a Qdrant vector database.

    This class provides an interface to:
    - Store document chunks as vector embeddings in Qdrant.
    - Retrieve relevant chunks using semantic search.
    - Add, delete, or query documents from the vector store.

    Designed with dependency injection in mind, it allows passing a custom 
    Qdrant client for testing or alternative environments.

    Attributes:
        index_name (str): Name of the Qdrant collection.
        qdrant_url (str): URL of the Qdrant server.
        client (QdrantClient): Qdrant client instance used for all operations.
    """
    def __init__(
            self, client: QdrantClient | None = None, 
            index_name: str = "my_docs", 
            url: str | None = None
        ):
            self.index_name = index_name
            self.qdrant_url = url or settings.qdrant_url
            self.client = client or QdrantClient(url=self.qdrant_url)
    
    @property
    def embedder(self) -> CacheBackedEmbeddings:
        """
        Create and return a cached OpenAI embedder.
        
        Uses local file storage for caching to avoid duplicate API calls for identical content.
        The cache is keyed by SHA-256 hash of the content and embedding model name.
        
        Returns:
            CacheBackedEmbeddings: Cached OpenAI embedding service instance
        """
        if not hasattr(self, '_cached_embedder'):
            store = LocalFileStore("./cache/")
            base = OpenAIEmbeddings(model=settings.embedding_model)

            self._cached_embedder = CacheBackedEmbeddings.from_bytes_store(
                base,
                store,
                namespace=base.model,
                key_encoder="sha256",
            )
        return self._cached_embedder
    
    @property
    def vectorstore(self) -> QdrantVectorStore:
        """
        Initialize and return a Qdrant vector store instance.
        
        Creates the collection if it doesn't exist with cosine distance metric and
        a dimensional vector configuration.
        
        Returns:
            QdrantVectorStore: Initialized Qdrant vector store instance
        """
        if not hasattr(self, '_cached_vectorstore'):
            embedder = self.embedder
            
            if not self.client.collection_exists(self.index_name):
                self.client.create_collection(
                    collection_name=self.index_name,
                    vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
                )
            
            self._cached_vectorstore = QdrantVectorStore.from_existing_collection(
                url=self.qdrant_url,
                collection_name=self.index_name,
                embedding=embedder,
            )
        return self._cached_vectorstore

    def load_documents(self, chunks: list[Document]) -> str:
        """
        Load and index document chunks into the Qdrant vector store.
        
        Handles collection creation if necessary and indexes document chunks with
        their metadata and embeddings.
        
        Args:
            chunks (list[Document]): List of document chunks to index
            
        Returns:
            str: Success message indicating number of chunks indexed
            
        Raises:
            ValueError: If no chunks are provided
            RuntimeError: If indexing fails
        """
        try:
            if not chunks:
                raise ValueError("No document chunks provided for indexing")

            vectorstore = self.vectorstore
            ids = [self.make_doc_id(chunk) for chunk in chunks]

            vectorstore.add_documents(documents=chunks, ids=ids)
            logger.info(f"Indexed {len(chunks)} document chunks into Qdrant vector store '{self.index_name}'.")

            return "Documents have been successfully stored in the knowledge base."
        except Exception as e:
            raise RuntimeError(f"Failed to load documents into vector store: {str(e)}")
    
    def get_documents(self) -> list[str]:
        """
        Get all unique document titles from the vector store.
        
        Uses Qdrant's scroll API to efficiently retrieve all document titles from
        the collection.
        
        Returns:
            list[str]: Sorted list of document titles in the store
        """
        titles = set()
        next_offset = None

        while True:
            points, next_offset = self.client.scroll(
                collection_name=self.index_name,
                limit=10000,
                with_payload=True,
                with_vectors=False,
                offset=next_offset,
            )
            
            for p in points:
                assert p.payload is not None
                titles.add(p.payload["metadata"]["title"])

            if next_offset is None:
                break

        return sorted(titles)
    
    def delete_document(self, document_title: str) -> str:
        """
        Delete all chunks associated with a specific document title.
        
        Uses Qdrant's filter-based deletion to remove all chunks matching the
        document title metadata.
        
        Args:
            document_title (str): Title of the document to delete
            
        Returns:
            str: Success message confirming deletion
        """
        self.client.delete(
            collection_name=self.index_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.title",
                        match=MatchValue(value=document_title)
                    )
                ]
            )
        )
        logger.info(f"Deleted all chunks from book '{document_title}'")
        return f"Deleted all chunks from book '{document_title}'"
    
    def search(self, query: str) -> AIMessage:
        """
        Perform semantic search and generate AI response.
        
        Finds relevant document chunks using semantic search, then uses a language model
        to generate a coherent response based on the retrieved context.
        
        Args:
            query (str): Search query to find relevant information
            
        Returns:
            AIMessage: AI-generated response with content and metadata
        """
        vectorstore = self.vectorstore
        
        qdrant_top_k = vectorstore.similarity_search(query, k=10)

        if not qdrant_top_k:
            return AIMessage(content="No relevant documents found in the knowledge base to answer this question.")

        context = "\n\n".join(chunk.page_content for chunk in qdrant_top_k)
        model = config_model(settings.rag_model)

        search_chain = SEARCH_PROMPT | model

        response = search_chain.invoke({
            "query": query,
            "context": context
        })
        
        return response
    
    def make_doc_id(self, chunk: Document) -> str:
        """
        Generate a unique identifier for a document chunk.
        
        Uses UUID v4 to generate random, unique identifiers for each chunk.
        
        Args:
            chunk (Document): Document chunk to generate ID for
            
        Returns:
            str: Unique chunk identifier
        """
        unique_id = uuid.uuid4()
        return str(unique_id)
    
    def flush_store(self) -> str:
        """
        Empty the entire Qdrant vector store.
        
        WARNING: This operation is irreversible and deletes all stored documents.
        
        Returns:
            str: Confirmation message indicating store has been cleared
        """
        self.client.delete(
            collection_name=self.index_name,
            points_selector=Filter(must=[])
        )
        return f"Qdrant DB for index '{self.index_name}' flushed - ready for fresh execution"
