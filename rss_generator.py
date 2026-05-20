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

def generate_rss(metadata: Dict, bilingual_data: List[Dict], audio_path: str, base_url: str) -> str:
    fg = FeedGenerator()
    fg.load_extension('podcast')
    
    fg.title(f"[中文翻译] {metadata['podcast_title']}")
    fg.author({'name': settings.author_name, 'email': settings.author_email})
    fg.link(href=base_url, rel='alternate')
    fg.logo(metadata.get('image_url', ''))
    fg.subtitle('英文播客自动中文化项目')
    fg.description(f"由 AI 自动翻译自播客: {metadata['podcast_title']}")
    fg.language('zh-cn')

    fe = fg.add_entry()
    fe.id(metadata['guid'])
    fe.title(metadata['episode_title'])
    
    # Construct bilingual show notes
    show_notes = "<h2>中英双语对照文本</h2>"
    for item in bilingual_data:
        show_notes += f"<p><strong>[EN]</strong>: {item['original']}</p>"
        show_notes += f"<p><strong>[ZH]</strong>: {item['translated']}</p>"
        show_notes += "<hr>"
    
    fe.description(show_notes)
    
    audio_filename = os.path.basename(audio_path)
    audio_url = f"{base_url}/{audio_filename}"
    
    # Audio metadata
    file_size = os.path.getsize(audio_path)
    audio = AudioSegment.from_mp3(audio_path)
    duration_secs = int(len(audio) / 1000)
    
    mime_type, _ = mimetypes.guess_type(audio_path)
    mime_type = mime_type or 'audio/mpeg'
    
    fe.enclosure(audio_url, str(file_size), mime_type)
    
    # Standardize pubDate
    try:
        # Expected format: "Tue, 14 May 2026 00:00:00 +0000" or similar
        # If it's already a standard string, feedgen might handle it, 
        # but let's try to be safe.
        fe.pubDate(metadata['pub_date'])
    except:
        fe.pubDate(datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"))
        
    fe.podcast.itunes_duration(duration_secs)
    
    output_path = os.path.join(os.path.dirname(audio_path), "podcast.xml")
    fg.rss_file(output_path, encoding='UTF-8')
    return output_path

if __name__ == "__main__":
    meta_path = "downloads/metadata.json"
    data_path = "processed/bilingual_data.json"
    audio_path = "output/chinese_podcast.mp3"
    
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    
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
