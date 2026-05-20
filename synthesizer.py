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

async def run_synthesis(bilingual_data: List[Dict], output_path: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    full_chinese_text = "\n".join([item['translated'] for item in bilingual_data if "[TRANSLATION FAILED]" not in item['translated']])
    
    chunks = split_text(full_chinese_text)
    combined_audio = AudioSegment.empty()
    
    print(f"Synthesizing Chinese audio in {len(chunks)} chunks...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, chunk in enumerate(chunks):
            print(f"Synthesizing chunk {i+1}/{len(chunks)}...")
            temp_mp3 = os.path.join(tmpdir, f"chunk_{i}.mp3")
            await synthesize_chunk(chunk, temp_mp3, voice)
            
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
