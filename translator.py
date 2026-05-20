import json
import os
import sys
from openai import OpenAI

def translate_text(text, api_key, base_url="https://api.openai.com/v1", model="gpt-4o"):
    if not api_key:
        return "[MISSING API KEY] " + text
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    system_prompt = (
        "You are a professional podcast translator. "
        "Translate the following English podcast transcript into natural, fluent Chinese. "
        "Maintain the original meaning and tone. Return only the translated Chinese text."
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[ERROR] {text}"

def process_transcription(input_json, api_key, base_url, model):
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = data.get('segments', [])
    translated_segments = []
    
    # To save API calls and maintain context, we can group segments into chunks
    # Let's say ~500 words or ~10 segments per chunk
    chunk_size = 15
    for i in range(0, len(segments), chunk_size):
        chunk = segments[i:i + chunk_size]
        chunk_text = " ".join([seg['text'] for seg in chunk])
        
        print(f"Translating chunk {i // chunk_size + 1}/{(len(segments) + chunk_size - 1) // chunk_size}...")
        translated_text = translate_text(chunk_text, api_key, base_url, model)
        
        # Distribute translated text back to segments (rough approximation or just keep as chunk)
        # For RSS show notes, chunked is fine.
        translated_segments.append({
            'start': chunk[0]['start'],
            'end': chunk[-1]['end'],
            'original': chunk_text,
            'translated': translated_text
        })
        
    return translated_segments

if __name__ == "__main__":
    input_path = "processed/transcription.json"
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)
        
    # Get configuration from environment variables
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4o")
    
    if not api_key:
        print("Warning: LLM_API_KEY not found in environment. Using placeholder translation.")
    
    results = process_transcription(input_path, api_key, base_url, model)
    
    output_path = "processed/bilingual_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Bilingual data saved to {output_path}")
