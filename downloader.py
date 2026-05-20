import requests
import feedparser
import os
import sys
import json
import mimetypes
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*'
}

def get_podcast_info(apple_url: str) -> Dict:
    """
    Extracts RSS feed URL and specific episode info from an Apple Podcasts URL.
    """
    parsed_url = urlparse(apple_url)
    if not parsed_url.netloc.endswith('podcasts.apple.com'):
        raise ValueError(f"Invalid Apple Podcasts URL: {apple_url}")

    path_parts = parsed_url.path.split('/')
    podcast_id = None
    for part in path_parts:
        if part.startswith('id'):
            podcast_id = part[2:]
            break
    
    if not podcast_id:
        raise ValueError("Could not find Podcast ID in URL")

    # Use iTunes Lookup API to find the RSS feed URL
    lookup_url = f"https://itunes.apple.com/lookup?id={podcast_id}&entity=podcast"
    response = requests.get(lookup_url, headers=DEFAULT_HEADERS, timeout=(10, 30))
    response.raise_for_status()
    data = response.json()
    
    if not data.get('results'):
        raise ValueError(f"No results found for Podcast ID: {podcast_id}")
    
    result = data['results'][0]
    feed_url = result.get('feedUrl')
    if not feed_url:
        raise ValueError("Could not find RSS feed URL in iTunes lookup")

    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    if feed.bozo:
        print(f"Warning: RSS feed parsing had issues: {feed.bozo_exception}")
    
    # Check if a specific episode ID was provided in the URL (i=...)
    query_params = parse_qs(parsed_url.query)
    episode_id = query_params.get('i', [None])[0]
    
    target_episode = None
    if episode_id:
        for entry in feed.entries:
            # GUID matching
            guid = entry.get('guid', '')
            if episode_id == guid or f"id{episode_id}" == guid or episode_id in guid:
                target_episode = entry
                break
    
    if not target_episode:
        if episode_id:
            print(f"Warning: Episode ID {episode_id} not found in feed. Taking latest.")
        target_episode = feed.entries[0]

    return {
        'podcast_title': feed.feed.get('title', 'Unknown Podcast'),
        'episode_title': target_episode.get('title', 'Unknown Episode'),
        'episode_description': target_episode.get('description', ''),
        'audio_url': target_episode.enclosures[0].href if target_episode.enclosures else None,
        'guid': target_episode.get('guid', ''),
        'pub_date': target_episode.get('published', ''),
        'image_url': target_episode.get('itunes_image', {}).get('href') or feed.feed.get('image', {}).get('url')
    }

def download_file(url: str, output_path: str):
    response = requests.get(url, headers=DEFAULT_HEADERS, stream=True, timeout=(10, 300))
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 8
    
    with open(output_path, 'wb') as f, tqdm(
        desc=os.path.basename(output_path),
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(block_size):
            size = f.write(data)
            bar.update(size)

def run_download(url: str, download_dir: str = "downloads") -> Dict:
    info = get_podcast_info(url)
    print(f"Found Podcast: {info['podcast_title']}")
    print(f"Episode: {info['episode_title']}")
    
    os.makedirs(download_dir, exist_ok=True)
    
    # Save metadata
    metadata_file = os.path.join(download_dir, "metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    
    if info['audio_url']:
        # Guess extension
        content_type = requests.head(info['audio_url'], headers=DEFAULT_HEADERS, timeout=10).headers.get('content-type', '')
        ext = mimetypes.guess_extension(content_type.split(';')[0]) or '.mp3'
        audio_path = os.path.join(download_dir, f"original_audio{ext}")
        
        download_file(info['audio_url'], audio_path)
        info['local_audio_path'] = audio_path
    else:
        print("No audio URL found.")
        info['local_audio_path'] = None
        
    return info

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <apple_podcast_url>")
        sys.exit(1)
    
    try:
        run_download(sys.argv[1])
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
