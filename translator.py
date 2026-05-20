import asyncio
import json
import os
import sys
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class Translator:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o", max_concurrency: int = 5, glossary: Dict[str, str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url) if api_key else None
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.glossary = glossary or {}
        self.global_context = ""

    async def generate_global_context(self, full_text: str):
        """Generates a brief summary and key topics of the podcast for context."""
        if not self.client:
            return
        
        print("Generating global context summary...")
        prompt = (
            "Analyze the following podcast transcript snippet and provide a 2-line summary "
            "and a list of 5 key themes/topics discussed. This will be used as context for translating segments."
        )
        
        try:
            # We only need the first 2000 words for a good overview
            snippet = " ".join(full_text.split()[:2000])
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"{prompt}\n\nTranscript:\n{snippet}"}
                ],
                temperature=0.3
            )
            self.global_context = response.choices[0].message.content.strip()
            print(f"Context generated: {self.global_context[:100]}...")
        except Exception as e:
            print(f"Error generating context: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def translate_text(self, text: str) -> str:
        if not self.client:
            return "[MISSING API KEY] " + text
        
        glossary_str = "\n".join([f"- {k} -> {v}" for k, v in self.glossary.items()])
        
        system_prompt = (
            "You are a professional podcast translator. "
            "Translate the following English podcast transcript into natural, fluent Chinese.\n\n"
            f"GLOBAL CONTEXT:\n{self.global_context}\n\n"
            f"GLOSSARY (Strictly follow these translations):\n{glossary_str}\n\n"
            "IMPORTANT: Identify the speaker for each part. Use 'HOST' for the host and 'GUEST' for the guest(s). "
            "Return the result as a list of JSON-like entries, each with 'speaker' and 'text' keys. "
            "Example: [{\"speaker\": \"HOST\", \"text\": \"你好\"}, {\"speaker\": \"GUEST\", \"text\": \"谢谢\"}]"
            "Return ONLY the raw string representing this list, no markdown blocks."
        )
        
        async with self.semaphore:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()

    async def run_translation(self, transcription_data: Dict, chunk_size: int = 15) -> List[Dict]:
        segments = transcription_data.get('segments', [])
        full_text = transcription_data.get('text', '')
        
        # Phase 1: Pre-process global context
        await self.generate_global_context(full_text)
        
        # Phase 2: Concurrent translation
        chunks = []
        for i in range(0, len(segments), chunk_size):
            chunk = segments[i:i + chunk_size]
            chunks.append(chunk)
            
        print(f"Translating {len(chunks)} chunks with speaker identification...")
        
        async def translate_chunk(chunk, idx):
            chunk_text = " ".join([seg['text'] for seg in chunk])
            try:
                raw_translation = await self.translate_text(chunk_text)
                # Parse the JSON-like response safely
                import json
                try:
                    # Strip possible markdown code blocks if any
                    clean_raw = raw_translation.strip('`').replace('json\n', '', 1)
                    parsed_list = json.loads(clean_raw)
                    
                    # If it's a list, we might have multiple speaker segments in one chunk
                    # For simplicity in RSS, we can join them but for TTS we need them split
                    # Let's keep them as a sub-list or flattened list
                    translated_text = " ".join([item['text'] for item in parsed_list])
                    # We'll take the dominant speaker or the first one for this chunk for now
                    speaker = parsed_list[0]['speaker'] if parsed_list else "UNKNOWN"
                except:
                    # Fallback to old behavior if LLM fails format
                    translated_text = raw_translation
                    speaker = "UNKNOWN"
                
                print(f"Chunk {idx+1}/{len(chunks)} completed.")
            except Exception as e:
                print(f"Translation error on chunk {idx+1}: {e}")
                translated_text = f"[TRANSLATION FAILED] {chunk_text}"
                speaker = "UNKNOWN"
            
            return {
                'start': chunk[0]['start'],
                'end': chunk[-1]['end'],
                'original': chunk_text,
                'translated': translated_text,
                'speaker': speaker,
                'idx': idx
            }

        tasks = [translate_chunk(chunk, i) for i, chunk in enumerate(chunks)]
        results = await asyncio.gather(*tasks)
        
        # Sort by idx to maintain original order
        results.sort(key=lambda x: x['idx'])
        for r in results:
            del r['idx']
            
        return results

if __name__ == "__main__":
    # Internal test/CLI usage
    async def main():
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
        results = await translator.run_translation(data)
        
        output_dir = "processed"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "bilingual_data.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Bilingual data saved to {output_path}")

    asyncio.run(main())
