from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # LLM Config
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    
    # Whisper Config
    whisper_model: str = "base"
    
    # TTS Config
    tts_voice: str = "zh-CN-XiaoxiaoNeural"
    
    # Project Config
    base_url: str = "http://localhost:8000"
    download_dir: str = "downloads"
    processed_dir: str = "processed"
    output_dir: str = "output"
    
    # App Config
    monitored_urls: list[str] = [
        "https://podcasts.apple.com/us/podcast/the-investors-podcast-we-study-billionaires-the/id928933489?l=zh-Hans-CN"
    ]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
