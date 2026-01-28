from langchain.tools import tool

from core.pipeline import RAGManager
from utils.logging import logger

from pathlib import Path


rag_manager = RAGManager()


@tool
def store_documents(input_folder: Path):
    """
    Tool that stores into the RAG all the documents inside the input folder if requested by the user.

    Args:
        input_folder (Path): folder path from which the documents to upload will be taken.

    Returns:
        str: Success message or error message from the upload operation.

    Note:
        Currently supports PDF documents. The documents are split into chunks
        and stored in the vectorstore with chunk IDs for efficient retrieval.

    Example:
        >>> from pathlib import Path
        >>> store_documents(Path("data/"))
        'The documents have been successfully uploaded and indexed.'
    """
    try:
        logger.info(f"Loading documents from {input_folder}")
        result = rag_manager.process_and_store_documents(input_folder)
        logger.info("Documents successfully uploaded and indexed")
        return result
    except Exception as e:
        logger.warning(str(e))
        return str(e)


@tool
def query_rag(query: str):
    """
    Tool that answers user's questions using the data stored in the RAG.

    Args:
        query (str): User's query for which the agent needs to give an answer given the extracted RAG informations.

    Returns:
        str: The answer to the user's query based on the retrieved documents,
             or a message if no relevant information is found

    Note:
        Uses semantic search to find relevant documents from the vectorstore
        and generates responses using the configured LLM model.

    Example:
        >>> answer = query_rag("What is the capital of France?")
        >>> answer
        'The capital of France is Paris.'
    """
    try:
        logger.info(f"Processing query: {query}")
        response = rag_manager.query_documents(query)
        return response
    except Exception as e:
        logger.warning(str(e))
        return str(e)


@tool
def delete_document(document: str):
    """
    Tool that deletes all chunks associated with a specific book from the RAG.

    Args:
        document (str): The title (book name) of the document to delete.

    Returns:
        str: Success message indicating the number of chunks deleted.

    Note:
        This function searches for all documents with the matching title metadata
        and removes them from the vectorstore.

    Example:
        >>> delete_document("example_book")
        'Deleted 50 chunks from book "example_book".'
    """
    try:
        result = rag_manager.delete_document(document)
        return result
    except Exception as e:
        logger.warning(str(e))
        return str(e)
    

@tool
def get_documents():
    """
    Tool that returns all the titles of the documents stored in the RAG.

    Returns:
        list[str]: List of the titles of the stored documents.

    Note:
        This function searches for all documents in the db.
    """
    try:
        documents = rag_manager.get_all_documents()
        return documents
    except Exception as e:
        logger.warning(str(e))
        return str(e)
    
    
@tool
def flush_store():
    """
    Tool that empties completely the RAG database.
    """
    try:
        result = rag_manager.flush_db()
        return result
    except Exception as e:
        logger.warning(str(e))
        return str(e)
