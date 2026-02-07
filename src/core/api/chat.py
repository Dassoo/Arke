from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import time
import uuid

router = APIRouter()

# ---------- Models ----------

class ChatRequest(BaseModel):
    message: str
    thread_id: str

class CreateThreadRequest(BaseModel):
    title: Optional[str] = None

class ThreadResponse(BaseModel):
    id: str
    title: str
    created_at: int
    updated_at: int
    message_count: int

class MessageResponse(BaseModel):
    role: str
    content: str


# ---------- In-memory storage ----------

threads_store: dict[str, dict] = {}
threads_list: list[str] = []

def init_chat_dependencies(_agent, _checkpointer):
    global agent, checkpointer
    agent = _agent
    checkpointer = _checkpointer


# ---------- Chat endpoint ----------

@router.post("/chat")
async def chat(req: ChatRequest):
    request_config: RunnableConfig = {"configurable": {"thread_id": req.thread_id}}

    if req.thread_id not in threads_store:
        preview = req.message[:50] + "..." if len(req.message) > 50 else req.message
        threads_store[req.thread_id] = {
            "id": req.thread_id,
            "title": f"Chat: {preview}",
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "message_count": 0,
        }
        threads_list.insert(0, req.thread_id)

    async def generate():
        async for event in agent.astream_events(
            {"messages": [{"role": "user", "content": req.message}]},
            config=request_config,
            version="v2",
        ):  
            if event["event"] == "on_chat_model_stream" and "chunk" in event["data"]:
                chunk = event["data"]["chunk"]
                langgraph_node = event.get("metadata", {}).get("langgraph_node")
                if langgraph_node == 'model':
                    if chunk.content:
                        yield chunk.content
        
        # Update activity after streaming
        if req.thread_id in threads_store:
            threads_store[req.thread_id]["updated_at"] = int(time.time())
            threads_store[req.thread_id]["message_count"] += 1
            threads_store[req.thread_id]["title"] = req.message[:50] + "..." if len(req.message) > 50 else req.message

            if req.thread_id in threads_list:
                threads_list.remove(req.thread_id)
            threads_list.insert(0, req.thread_id)

            if threads_store[req.thread_id]["message_count"] == 0:
                await delete_thread(req.thread_id)

    return StreamingResponse(generate(), media_type="text/plain")


# ---------- Threads endpoints ----------

@router.get("/threads", response_model=list[ThreadResponse])
async def list_threads(limit: int = 100):
    return [threads_store[t] for t in threads_list[:limit] if t in threads_store]


@router.post("/threads", response_model=ThreadResponse)
async def create_thread(request: CreateThreadRequest):
    thread_id = str(uuid.uuid4())
    data = {
        "id": thread_id,
        "title": request.title or f"Chat {thread_id[:8]}",
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
        "message_count": 0,
    }

    threads_store[thread_id] = data
    threads_list.insert(0, thread_id)
    return data


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    if thread_id not in threads_store:
        raise HTTPException(404, "Thread not found")
    return threads_store[thread_id]


@router.get("/threads/{thread_id}/messages", response_model=list[MessageResponse])
async def get_thread_messages(thread_id: str):
    if thread_id not in threads_store:
        raise HTTPException(404, "Thread not found")

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    checkpoint = checkpointer.get(config)

    if not checkpoint:
        return []

    messages = checkpoint.get("channel_values", {}).get("messages", [])

    result = []
    
    # Filtering messages, removing tools and tool calls
    for m in messages:
        if isinstance(m, ToolMessage):
            continue
        if isinstance(m, HumanMessage):
            result.append({
                "role": "user",
                "content": m.content,
            })
        elif isinstance(m, AIMessage):
            if not m.content and m.tool_calls:
                continue
            result.append({
                "role": "assistant",
                "content": m.content,
            })
    return result


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    if thread_id not in threads_store:
        raise HTTPException(404, "Thread not found")

    del threads_store[thread_id]
    threads_list.remove(thread_id)
    return {"success": True}


@router.get("/status")
async def get_status():
    return {"status": "connected"}