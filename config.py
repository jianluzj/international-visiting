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
    author_name: str = "jianluzj"
    author_email: str = "jianluzj@gmail.com"
    monitored_urls: list[str] = [
        "https://podcasts.apple.com/us/podcast/the-investors-podcast-we-study-billionaires-the/id928933489?l=zh-Hans-CN"
    ]
    
    # Speaker to Voice mapping (Role Separation)
    # Default mapping: SPEAKER_A (usually host), SPEAKER_B (usually guest)
    speaker_voice_map: dict[str, str] = {
        "HOST": "zh-CN-YunxiNeural",
        "GUEST": "zh-CN-XiaoxiaoNeural",
        "UNKNOWN": "zh-CN-XiaoxiaoNeural"
    }
    
    # Translation Glossary (Term -> Translation)
    glossary: dict[str, str] = {
        "Fiscal Dominance": "财政主导",
        "Treasuries": "国债",
        "Inflation": "通货膨胀",
        "Bitcoin": "比特币",
        "Lyn Alden": "琳·阿尔登",
        "Stig Brodersen": "史蒂格·布罗德森"
    }
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
