# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import uvicorn

from core.cache import init_llm_cache
from core.prompts import RAG_AGENT_PROMPT
from core.config import settings, config_model
from core.api.chat import router as chat_router, init_chat_dependencies
from agents.middleware import custom_middleware
from agents import tools


def validate_env(settings):
    required = ["OPENAI_API_KEY", "REDIS_URL", "QDRANT_URL"]
    missing = [v for v in required if not getattr(settings, v.lower())]
    if missing:
        raise EnvironmentError(f"Missing env vars: {missing}")


validate_env(settings)
init_llm_cache()

checkpointer = InMemorySaver()

agent = create_agent(
    model=config_model(settings.agent_model),
    checkpointer=checkpointer,
    tools=[
        tools.store_documents,
        tools.query_rag,
        tools.delete_document,
        tools.get_documents,
        tools.flush_store,
    ],
    middleware=custom_middleware,
    system_prompt=RAG_AGENT_PROMPT,
)

init_chat_dependencies(agent, checkpointer)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir="src",
    )
