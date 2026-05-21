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

def load_state(job_id: str = None) -> Dict:
    state_file = STATE_FILE if not job_id else f"state_{job_id}.json"
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            return json.load(f)
    return {"steps": {}}

def save_state(state: Dict, job_id: str = None):
    state_file = STATE_FILE if not job_id else f"state_{job_id}.json"
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def report_progress(job_id: str, status: str, progress: int, message: str):
    if not job_id:
        return
    # Only import here to avoid circular imports if run directly
    try:
        from tasks import update_job_status
        update_job_status(job_id, status, progress, message)
    except ImportError:
        pass

def run_pipeline(url: str, resume: bool = False, full: bool = False, job_id: str = None):
    state = load_state(job_id) if resume else {"steps": {}, "url": url}
    
    # 1. Download
    report_progress(job_id, "RUNNING", 10, "Downloading podcast audio and metadata...")
    if not state["steps"].get("download", {}).get("done"):
        logger.info("Step 1: Downloading podcast...")
        metadata = run_download(url, settings.download_dir)
        state["steps"]["download"] = {"done": True, "metadata": metadata}
        save_state(state, job_id)
    else:
        logger.info("Step 1: Skipping download (already done).")
        metadata = state["steps"]["download"]["metadata"]

    audio_path = metadata["local_audio_path"]
    
    if not full:
        snippet_path = os.path.join(settings.download_dir, "test_snippet.mp3")
        if not os.path.exists(snippet_path):
            logger.info("Creating 5-minute snippet for testing...")
            os.system(f"ffmpeg -y -ss 0 -t 300 -i \"{audio_path}\" -acodec copy \"{snippet_path}\"")
        audio_path = snippet_path

    # 2. Transcription
    report_progress(job_id, "RUNNING", 30, "Transcribing audio to text...")
    if not state["steps"].get("transcribe", {}).get("done"):
        logger.info("Step 2: Transcribing audio (this may take a while)...")
        transcription = run_transcription(audio_path, settings.whisper_model)
        state["steps"]["transcribe"] = {"done": True, "data": transcription}
        save_state(state, job_id)
    else:
        logger.info("Step 2: Skipping transcription (already done).")
        transcription = state["steps"]["transcribe"]["data"]

    # 3. Translation
    report_progress(job_id, "RUNNING", 60, "Translating text to Chinese with AI roles...")
    if not state["steps"].get("translate", {}).get("done"):
        logger.info("Step 3: Translating transcript (concurrently with glossary)...")
        translator = Translator(settings.llm_api_key, settings.llm_base_url, settings.llm_model, glossary=settings.glossary)
        import asyncio
        bilingual_data = asyncio.run(translator.run_translation(transcription))
        state["steps"]["translate"] = {"done": True, "data": bilingual_data}
        save_state(state, job_id)
    else:
        logger.info("Step 3: Skipping translation (already done).")
        bilingual_data = state["steps"]["translate"]["data"]

    # 4. Synthesis
    report_progress(job_id, "RUNNING", 80, "Synthesizing Chinese audio with multiple voices...")
    episodes_dir = os.path.join(settings.output_dir, "episodes")
    os.makedirs(episodes_dir, exist_ok=True)
    
    safe_guid = "".join([c for c in metadata["guid"] if c.isalnum()])
    output_audio = os.path.join(episodes_dir, f"{safe_guid}.mp3")
    
    if not state["steps"].get("synthesize", {}).get("done"):
        logger.info(f"Step 4: Synthesizing Chinese audio (role-based) -> {output_audio}")
        import asyncio
        asyncio.run(run_synthesis(bilingual_data, output_audio, settings.speaker_voice_map))
        state["steps"]["synthesize"] = {"done": True, "output_path": output_audio}
        save_state(state, job_id)
    else:
        logger.info("Step 4: Skipping synthesis (already done).")

    # 5. RSS & Web Data Generation
    report_progress(job_id, "RUNNING", 95, "Generating RSS feed and Web content...")
    logger.info("Step 5: Generating RSS feed and web data...")
    rss_path = generate_rss(metadata, bilingual_data, output_audio, settings.base_url)
    
    episode_data_path = os.path.join(episodes_dir, f"{safe_guid}.json")
    with open(episode_data_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": metadata,
            "segments": bilingual_data
        }, f, ensure_ascii=False, indent=2)
    
    # Also update processed_episodes DB so the frontend immediately shows it
    from monitor import load_db, save_db
    import time
    db = load_db()
    db[safe_guid] = {
        "podcast_title": metadata['podcast_title'],
        "episode_title": metadata['episode_title'],
        "episode_description": metadata['episode_description'],
        "guid": metadata['guid'],
        "pub_date": metadata['pub_date'],
        "image_url": metadata.get('image_url', ''),
        "audio_filename": f"{safe_guid}.mp3",
        "data_filename": f"{safe_guid}.json",
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    save_db(db)

    logger.info("="*40)
    logger.info("PIPELINE COMPLETE!")
    
    state_file = STATE_FILE if not job_id else f"state_{job_id}.json"
    if os.path.exists(state_file):
        os.remove(state_file)
    
    report_progress(job_id, "COMPLETED", 100, "Podcast is ready!")

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
