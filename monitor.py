import json
import os
import time
import logging
from config import settings
from downloader import get_podcast_info
from main import run_pipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Monitor")

DB_FILE = os.path.join(settings.processed_dir, "processed_episodes.json")

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_db(db):
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

def check_for_updates():
    db = load_db()
    updated = False
    
    for apple_url in settings.monitored_urls:
        logger.info(f"Checking podcast: {apple_url}")
        try:
            info = get_podcast_info(apple_url)
            podcast_title = info['podcast_title']
            episode_guid = info['guid']
            episode_title = info['episode_title']
            
            key = f"{podcast_title}_{episode_guid}"
            
            if key not in db:
                logger.info(f"New episode found: {episode_title}")
                
                # Run the pipeline via function call
                # We use full=True for real monitoring
                try:
                    run_pipeline(apple_url, resume=False, full=True)
                    
                    # Store richer metadata for multi-episode support
                    db[key] = {
                        "podcast_title": info['podcast_title'],
                        "episode_title": info['episode_title'],
                        "episode_description": info['episode_description'],
                        "guid": info['guid'],
                        "pub_date": info['pub_date'],
                        "image_url": info.get('image_url', ''),
                        "audio_filename": f"{''.join([c for c in info['guid'] if c.isalnum()])}.mp3",
                        "data_filename": f"{''.join([c for c in info['guid'] if c.isalnum()])}.json",
                        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    updated = True
                    logger.info(f"Successfully processed {episode_title}")
                except Exception as e:
                    logger.error(f"Failed to process {episode_title}: {e}")
            else:
                logger.info(f"No new episodes for {podcast_title}.")
                
        except Exception as e:
            logger.error(f"Error checking {apple_url}: {e}")
            
    if updated:
        save_db(db)

if __name__ == "__main__":
    check_for_updates()
