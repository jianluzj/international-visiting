import requests
import feedparser
import os
import sys
import json
from urllib.parse import urlparse, parse_qs

def get_podcast_info(apple_url):
    """
    Extracts RSS feed URL and specific episode info from an Apple Podcasts URL.
    """
    # Extract Podcast ID from URL
    # Example: https://podcasts.apple.com/us/podcast/.../id928933489?...
    parsed_url = urlparse(apple_url)
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
    response = requests.get(lookup_url)
    response.raise_for_status()
    data = response.json()
    
    if not data.get('results'):
        raise ValueError("No results found for this Podcast ID")
    
    feed_url = data['results'][0].get('feedUrl')
    if not feed_url:
        raise ValueError("Could not find RSS feed URL in iTunes lookup")

    # Parse the RSS feed
    feed = feedparser.parse(feed_url)
    
    # Check if a specific episode ID was provided in the URL (i=...)
    query_params = parse_qs(parsed_url.query)
    episode_id = query_params.get('i', [None])[0]
    
    target_episode = None
    if episode_id:
        # Some RSS feeds use the 'guid' that matches the episode_id
        for entry in feed.entries:
            # Usually Apple Episode ID is the guid or part of it
            if episode_id in entry.get('guid', '') or episode_id in entry.get('id', ''):
                target_episode = entry
                break
    
    # If no episode ID or not found, just take the latest
    if not target_episode:
        target_episode = feed.entries[0]

    return {
        'podcast_title': feed.feed.title,
        'episode_title': target_episode.title,
        'episode_description': target_episode.description,
        'audio_url': target_episode.enclosures[0].href if target_episode.enclosures else None,
        'guid': target_episode.guid,
        'pub_date': target_episode.published
    }

def download_audio(url, output_path):
    print(f"Downloading audio from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <apple_podcast_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    try:
        info = get_podcast_info(url)
        print(f"Found Podcast: {info['podcast_title']}")
        print(f"Episode: {info['episode_title']}")
        
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        
        # Save metadata
        metadata_file = "downloads/metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        # Download audio
        audio_ext = info['audio_url'].split('.')[-1].split('?')[0] if info['audio_url'] else 'mp3'
        audio_path = f"downloads/original_audio.{audio_ext}"
        if info['audio_url']:
            download_audio(info['audio_url'], audio_path)
        else:
            print("No audio URL found.")
            
    except Exception as e:
        print(f"Error: {e}")
