import whisper
import torch
import os
import json
import sys
from typing import Dict, Optional

_loaded_models = {}

def get_whisper_model(model_name: str = "base"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    cache_key = f"{model_name}_{device}"
    
    if cache_key not in _loaded_models:
        print(f"Loading Whisper model '{model_name}' on {device}...")
        _loaded_models[cache_key] = whisper.load_model(model_name, device=device)
    
    return _loaded_models[cache_key]

def run_transcription(audio_path: str, model_name: str = "base") -> Dict:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    model = get_whisper_model(model_name)
    
    print(f"Transcribing {audio_path}...")
    # Use fp16=True only if CUDA is available
    use_fp16 = torch.cuda.is_available()
    result = model.transcribe(audio_path, verbose=False, fp16=use_fp16)
    
    return result

if __name__ == "__main__":
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "downloads/original_audio.mp3"
    model_name = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    try:
        result = run_transcription(audio_path, model_name)
        
        output_dir = "processed"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "transcription.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Transcription saved to {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
