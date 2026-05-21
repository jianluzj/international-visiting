from feedgen.feed import FeedGenerator
import json
import os
import sys
import mimetypes
from datetime import datetime
from email.utils import format_datetime
from pydub import AudioSegment
from typing import Dict, List

from config import settings

def add_episode_to_feed(fg, episode_meta: Dict, base_url: str):
    fe = fg.add_entry()
    fe.id(episode_meta['guid'])
    fe.title(episode_meta['episode_title'])
    
    # Load bilingual data to reconstruct show notes
    data_path = os.path.join("output", "episodes", episode_meta['data_filename'])
    show_notes = f"<p>{episode_meta['episode_description']}</p><h2>中英双语对照文本</h2>"
    
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                episode_data = json.load(f)
                bilingual_segments = episode_data.get('segments', [])
                for item in bilingual_segments:
                    show_notes += f"<p><strong>[EN]</strong>: {item['original']}</p>"
                    show_notes += f"<p><strong>[ZH]</strong>: {item['translated']}</p>"
                    show_notes += "<hr>"
        except Exception as e:
            show_notes += f"<p>无法加载双语字幕: {e}</p>"
    
    fe.description(show_notes)
    
    audio_url = f"{base_url}/episodes/{episode_meta['audio_filename']}"
    audio_path = os.path.join("output", "episodes", episode_meta['audio_filename'])
    
    if os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
        mime_type, _ = mimetypes.guess_type(audio_path)
        fe.enclosure(audio_url, str(file_size), mime_type or 'audio/mpeg')
        
        # Duration from audio file
        try:
            audio = AudioSegment.from_mp3(audio_path)
            fe.podcast.itunes_duration(int(len(audio) / 1000))
        except:
            pass

    fe.pubDate(episode_meta['pub_date'])

def generate_full_rss(db_data: Dict, base_url: str) -> str:
    fg = FeedGenerator()
    fg.load_extension('podcast')
    
    # Use info from the first episode or generic info
    first_ep = list(db_data.values())[0] if db_data else {}
    
    fg.title(f"[中文翻译] {first_ep.get('podcast_title', '跨国串门')}")
    fg.author({'name': settings.author_name, 'email': settings.author_email})
    fg.link(href=base_url, rel='alternate')
    fg.logo(first_ep.get('image_url', ''))
    fg.subtitle('英文播客自动中文化项目')
    fg.description('由 AI 自动翻译的优质英文播客集锦')
    fg.language('zh-cn')

    # Add episodes in reverse chronological order (latest first)
    sorted_episodes = sorted(db_data.values(), key=lambda x: x.get('pub_date', ''), reverse=True)
    
    for ep in sorted_episodes:
        add_episode_to_feed(fg, ep, base_url)
    
    output_path = os.path.join("output", "podcast.xml")
    fg.rss_file(output_path, encoding='UTF-8')
    return output_path

# Keep original generate_rss for backward compatibility in main.py
def generate_rss(metadata: Dict, bilingual_data: List[Dict], audio_path: str, base_url: str) -> str:
    # Now we just call generate_full_rss with updated DB
    from monitor import load_db
    db = load_db()
    return generate_full_rss(db, base_url)

if __name__ == "__main__":
    meta_path = "downloads/metadata.json"
    data_path = "processed/bilingual_data.json"
    audio_path = "output/chinese_podcast.mp3"
    
    base_url = settings.base_url
    
    if not all(os.path.exists(p) for p in [meta_path, data_path, audio_path]):
        print("Missing required input files.")
        sys.exit(1)
        
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    with open(data_path, 'r', encoding='utf-8') as f:
        bilingual_data = json.load(f)
        
    try:
        rss_file = generate_rss(metadata, bilingual_data, audio_path, base_url)
        print(f"RSS Feed generated at {rss_file}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
