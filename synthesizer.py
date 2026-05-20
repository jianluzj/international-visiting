import asyncio
import edge_tts
import json
import os
import sys
from pydub import AudioSegment

async def synthesize(text, output_path, voice="zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

async def main():
    input_path = "processed/bilingual_data.json"
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)
        
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Combine all translated text
    full_chinese_text = "\n".join([item['translated'] for item in data])
    
    temp_mp3 = os.path.join(output_dir, "temp_chinese.mp3")
    print(f"Synthesizing Chinese audio...")
    await synthesize(full_chinese_text, temp_mp3)
    
    # Final output path
    final_output = os.path.join(output_dir, "chinese_podcast.mp3")
    
    # Use pydub to ensure it's a standard MP3 and maybe add some padding/metadata
    audio = AudioSegment.from_mp3(temp_mp3)
    audio.export(final_output, format="mp3", bitrate="192k")
    
    print(f"Chinese podcast saved to {final_output}")
    # Cleanup temp
    if os.path.exists(temp_mp3):
        os.remove(temp_mp3)

if __name__ == "__main__":
    asyncio.run(main())
