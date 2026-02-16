import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from langgraph.checkpoint.memory import MemorySaver

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock cache
with patch('src.core.cache.init_llm_cache'):
    from src.app import app
    from src.core.api.chat import init_chat_dependencies, threads_store, threads_list


# Mock agent
class MockAgent:
    async def astream_events(self, *args, **kwargs):
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": MagicMock(content="Test response")},
            "metadata": {"langgraph_node": "model"}
        }


@pytest.fixture(scope="function")
def client():
    mock_agent = MockAgent()
    mock_checkpointer = MemorySaver()
    
    init_chat_dependencies(mock_agent, mock_checkpointer)
    
    with TestClient(app) as c:
        yield c


def test_status_endpoint(client):
    """Test the status endpoint"""
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "connected"}


def test_chat_endpoint_success(client):
    """Test the chat endpoint with valid input"""
    # Clear any existing threads for clean test
    threads_store.clear()
    threads_list.clear()
    
    payload = {
        "message": "Hello, how are you?",
        "thread_id": "test-thread-123"
    }
    
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    
    # Check if thread was created
    assert "test-thread-123" in threads_store


def test_create_thread(client):
    """Test creating a new thread"""
    payload = {
        "title": "Test Thread"
    }
    
    response = client.post("/threads", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test Thread"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["message_count"] == 0
    
    # Verify thread exists in store
    assert data["id"] in threads_store


def test_get_thread(client):
    """Test getting a specific thread"""
    # First create a thread
    payload = {"title": "Get Thread Test"}
    create_response = client.post("/threads", json=payload)
    thread_data = create_response.json()
    thread_id = thread_data["id"]
    
    assert create_response.status_code == 200
    
    # Get the thread
    response = client.get(f"/threads/{thread_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == thread_id
    assert data["title"] == "Get Thread Test"


def test_get_nonexistent_thread(client):
    """Test getting a non-existent thread"""
    response = client.get("/threads/nonexistent-thread-id")
    assert response.status_code == 404
    assert "Thread not found" in response.text


def test_list_threads(client):
    """Test listing threads"""
    # Clear existing threads
    threads_store.clear()
    threads_list.clear()
    
    # Create a few threads
    for i in range(3):
        payload = {"title": f"Test Thread {i}"}
        client.post("/threads", json=payload)
    
    response = client.get("/threads")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) <= 3  # Should have at most 3 threads
    
    titles = [t["title"] for t in data]
    for i in range(min(3, len(data))):
        assert f"Test Thread {i}" in titles


def test_delete_thread(client):
    """Test deleting a thread"""
    # Create a thread
    payload = {"title": "Delete Test Thread"}
    create_response = client.post("/threads", json=payload)
    thread_data = create_response.json()
    thread_id = thread_data["id"]
    
    assert create_response.status_code == 200
    assert thread_id in threads_store
    
    # Delete the thread
    response = client.delete(f"/threads/{thread_id}")
    assert response.status_code == 200
    assert response.json() == {"success": True}
    
    # Verify thread is deleted
    assert thread_id not in threads_store
    assert thread_id not in threads_list


def test_delete_nonexistent_thread(client):
    """Test deleting a non-existent thread"""
    response = client.delete("/threads/nonexistent-thread-id")
    assert response.status_code == 404
    assert "Thread not found" in response.text


def test_get_thread_messages(client):
    """Test getting messages from a thread"""
    # Create a thread
    payload = {"title": "Messages Test Thread"}
    create_response = client.post("/threads", json=payload)
    thread_data = create_response.json()
    thread_id = thread_data["id"]
    
    assert create_response.status_code == 200
    
    # Get messages from the thread (should be empty initially)
    response = client.get(f"/threads/{thread_id}/messages")
    assert response.status_code == 200
    assert response.json() == []

