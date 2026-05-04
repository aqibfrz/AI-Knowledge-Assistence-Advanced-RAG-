from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Knowledge Assistant"
    groq_api_key: str = ""
    model_name: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_path: str = "./data/faiss_index"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
