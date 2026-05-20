import asyncio
import edge_tts
import json
import os
import sys
import tempfile
from pydub import AudioSegment
from typing import List, Dict

async def synthesize_chunk(text: str, output_path: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def split_text(text: str, max_chars: int = 4000) -> List[str]:
    """Splits text into chunks for Edge-TTS."""
    chunks = []
    current_chunk = ""
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 < max_chars:
            current_chunk += line + '\n'
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

from config import settings

async def run_synthesis(bilingual_data: List[Dict], output_path: str, voice_map: Dict[str, str] = None):
    if voice_map is None:
        voice_map = settings.speaker_voice_map

    print(f"Synthesizing Chinese audio for {len(bilingual_data)} segments concurrently...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        async def process_segment(i, item):
            text = item['translated']
            if "[TRANSLATION FAILED]" in text:
                return None
            
            speaker = item.get('speaker', 'UNKNOWN')
            voice = voice_map.get(speaker, voice_map.get('UNKNOWN', "zh-CN-XiaoxiaoNeural"))
            
            temp_mp3 = os.path.join(tmpdir, f"seg_{i}.mp3")
            await synthesize_chunk(text, temp_mp3, voice)
            return temp_mp3

        tasks = [process_segment(i, item) for i, item in enumerate(bilingual_data)]
        temp_files = await asyncio.gather(*tasks)
        
        print(f"Combining audio segments...")
        combined_audio = AudioSegment.empty()
        for temp_mp3 in temp_files:
            if temp_mp3:
                segment = AudioSegment.from_mp3(temp_mp3)
                combined_audio += segment
            
        print(f"Exporting final audio to {output_path}...")
        combined_audio.export(output_path, format="mp3", bitrate="192k")

if __name__ == "__main__":
    input_path = "processed/bilingual_data.json"
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)
        
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    final_output = os.path.join(output_dir, "chinese_podcast.mp3")
    
    voice = os.environ.get("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
    
    try:
        asyncio.run(run_synthesis(data, final_output, voice))
        print("Synthesis complete.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
