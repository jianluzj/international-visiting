from feedgen.feed import FeedGenerator
import json
import os
import sys
from datetime import datetime

def generate_rss(metadata, bilingual_data, audio_filename, base_url):
    fg = FeedGenerator()
    fg.load_extension('podcast')
    
    fg.title(f"[中文版] {metadata['podcast_title']}")
    fg.author({'name': 'International Visiting Agent'})
    fg.link(href=base_url, rel='alternate')
    fg.logo(metadata.get('image_url', '')) # Placeholder if no image
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
    fe.content(show_notes)
    
    audio_url = f"{base_url}/{audio_filename}"
    # We need file size for enclosure
    audio_path = os.path.join("output", audio_filename)
    file_size = os.path.getsize(audio_path)
    
    fe.enclosure(audio_url, str(file_size), 'audio/mpeg')
    fe.pubDate(metadata['pub_date'])
    
    rss_path = os.path.join("output", "podcast.xml")
    fg.rss_file(rss_path, encoding='UTF-8')
    return rss_path

if __name__ == "__main__":
    meta_path = "downloads/metadata.json"
    data_path = "processed/bilingual_data.json"
    audio_filename = "chinese_podcast.mp3"
    
    # Placeholder base_url - user should replace this with their actual hosting URL
    base_url = os.environ.get("BASE_URL", "http://localhost:8000")
    
    if not os.path.exists(meta_path) or not os.path.exists(data_path):
        print("Missing required metadata or bilingual data files.")
        sys.exit(1)
        
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    with open(data_path, 'r', encoding='utf-8') as f:
        bilingual_data = json.load(f)
        
    rss_file = generate_rss(metadata, bilingual_data, audio_filename, base_url)
    print(f"RSS Feed generated at {rss_file}")
    print(f"To subscribe, use: {base_url}/podcast.xml")
