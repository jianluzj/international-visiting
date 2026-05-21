import os
import sys
import json
import logging
import argparse
from typing import Dict, Optional

# Import refactored modules
from config import settings
from downloader import run_download
from transcriber import run_transcription
from translator import Translator
from synthesizer import run_synthesis
from rss_generator import generate_rss

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Pipeline")

STATE_FILE = "state.json"

def load_state() -> Dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"steps": {}}

def save_state(state: Dict):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def run_pipeline(url: str, resume: bool = False, full: bool = False):
    state = load_state() if resume else {"steps": {}, "url": url}
    
    # 1. Download
    if not state["steps"].get("download", {}).get("done"):
        logger.info("Step 1: Downloading podcast...")
        metadata = run_download(url, settings.download_dir)
        state["steps"]["download"] = {"done": True, "metadata": metadata}
        save_state(state)
    else:
        logger.info("Step 1: Skipping download (already done).")
        metadata = state["steps"]["download"]["metadata"]

    audio_path = metadata["local_audio_path"]
    
    # Optional snippet for testing
    if not full:
        snippet_path = os.path.join(settings.download_dir, "test_snippet.mp3")
        if not os.path.exists(snippet_path):
            logger.info("Creating 5-minute snippet for testing...")
            os.system(f"ffmpeg -y -ss 0 -t 300 -i \"{audio_path}\" -acodec copy \"{snippet_path}\"")
        audio_path = snippet_path

    # 2. Transcription
    if not state["steps"].get("transcribe", {}).get("done"):
        logger.info("Step 2: Transcribing audio (this may take a while)...")
        transcription = run_transcription(audio_path, settings.whisper_model)
        state["steps"]["transcribe"] = {"done": True, "data": transcription}
        save_state(state)
    else:
        logger.info("Step 2: Skipping transcription (already done).")
        transcription = state["steps"]["transcribe"]["data"]

    # 3. Translation
    if not state["steps"].get("translate", {}).get("done"):
        logger.info("Step 3: Translating transcript (concurrently with glossary)...")
        translator = Translator(settings.llm_api_key, settings.llm_base_url, settings.llm_model, glossary=settings.glossary)
        import asyncio
        bilingual_data = asyncio.run(translator.run_translation(transcription))
        state["steps"]["translate"] = {"done": True, "data": bilingual_data}
        save_state(state)
    else:
        logger.info("Step 3: Skipping translation (already done).")
        bilingual_data = state["steps"]["translate"]["data"]

    # 4. Synthesis
    episodes_dir = os.path.join(settings.output_dir, "episodes")
    os.makedirs(episodes_dir, exist_ok=True)
    
    # Use GUID for unique filename (sanitized)
    safe_guid = "".join([c for c in metadata["guid"] if c.isalnum()])
    output_audio = os.path.join(episodes_dir, f"{safe_guid}.mp3")
    
    if not state["steps"].get("synthesize", {}).get("done"):
        logger.info(f"Step 4: Synthesizing Chinese audio (role-based) -> {output_audio}")
        import asyncio
        asyncio.run(run_synthesis(bilingual_data, output_audio, settings.speaker_voice_map))
        state["steps"]["synthesize"] = {"done": True, "output_path": output_audio}
        save_state(state)
    else:
        logger.info("Step 4: Skipping synthesis (already done).")

    # 5. RSS & Web Data Generation
    logger.info("Step 5: Generating RSS feed and web data...")
    rss_path = generate_rss(metadata, bilingual_data, output_audio, settings.base_url)
    
    # Export for web player (individual episode data)
    episode_data_path = os.path.join(episodes_dir, f"{safe_guid}.json")
    with open(episode_data_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": metadata,
            "segments": bilingual_data
        }, f, ensure_ascii=False, indent=2)
    
    # Legacy support for the single index.html if needed
    with open(os.path.join(settings.output_dir, "data.json"), "w", encoding="utf-8") as f:
        json.dump(bilingual_data, f, ensure_ascii=False, indent=2)
    with open(os.path.join(settings.output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info("="*40)
    logger.info("PIPELINE COMPLETE!")
    logger.info(f"RSS Feed: {settings.base_url}/podcast.xml")
    logger.info(f"Web Player: {settings.base_url}/index.html")
    logger.info("="*40)
    
    # Cleanup state on success
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="International Visiting Podcast Pipeline")
    parser.add_argument("url", nargs="?", help="Apple Podcasts URL")
    parser.add_argument("--resume", action="store_true", help="Resume from last state")
    parser.add_argument("--full", action="store_true", help="Process full audio")
    
    args = parser.parse_args()
    
    if not args.url and not args.resume:
        parser.print_help()
        sys.exit(1)
        
    url = args.url
    if args.resume:
        state = load_state()
        url = state.get("url")
        if not url:
            logger.error("No state found to resume.")
            sys.exit(1)
            
    try:
        run_pipeline(url, args.resume, args.full)
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)
