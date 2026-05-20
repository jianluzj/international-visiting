import json
import os
import sys
from typing import List, Dict, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class Translator:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def translate_text(self, text: str) -> str:
        if not self.client:
            return "[MISSING API KEY] " + text
        
        system_prompt = (
            "You are a professional podcast translator. "
            "Translate the following English podcast transcript into natural, fluent, and conversational Chinese. "
            "Maintain the original meaning, tone, and any humor. "
            "Keep technical terms or unique proper nouns in English with Chinese explanation in brackets if necessary. "
            "Return only the translated Chinese text."
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()

    def run_translation(self, transcription_data: Dict, chunk_size: int = 15) -> List[Dict]:
        segments = transcription_data.get('segments', [])
        translated_segments = []
        
        total_chunks = (len(segments) + chunk_size - 1) // chunk_size
        
        for i in range(0, len(segments), chunk_size):
            chunk = segments[i:i + chunk_size]
            chunk_text = " ".join([seg['text'] for seg in chunk])
            
            chunk_idx = i // chunk_size + 1
            print(f"Translating chunk {chunk_idx}/{total_chunks}...")
            
            try:
                translated_text = self.translate_text(chunk_text)
            except Exception as e:
                print(f"Translation error on chunk {chunk_idx}: {e}")
                translated_text = f"[TRANSLATION FAILED] {chunk_text}"
            
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
        
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4o")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    translator = Translator(api_key, base_url, model)
    results = translator.run_translation(data)
    
    output_dir = "processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "bilingual_data.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Bilingual data saved to {output_path}")
