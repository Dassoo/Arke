from pydantic_settings import BaseSettings, SettingsConfigDict
from langchain_openai import ChatOpenAI

from pydantic import SecretStr, Field
from typing import Literal

from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    # --- LLM settings ---
    agent_model: str = "gpt-4o"
    rag_model: str = "gpt-4o-mini"
    safety_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-large"
    
    # --- API settings ---
    openai_api_key: SecretStr = SecretStr(Field(alias="OPENAI_API_KEY", default=""))
    
    # --- Storage settings ---
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"
    
    # --- Splitter settings ---
    splitter_type: Literal["recursive", "token"] = "recursive"
    chunk_size: int = 800
    chunk_overlap: int = 100
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()


def config_model(model_name: str):
    return ChatOpenAI(
        model=model_name, 
        api_key=settings.openai_api_key,
        streaming=True,
        temperature=0,
)
