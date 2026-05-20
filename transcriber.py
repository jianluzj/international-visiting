import whisper
import os
import json
import sys

def transcribe(audio_path, model_name="base"):
    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    
    print(f"Transcribing {audio_path}...")
    result = model.transcribe(audio_path, verbose=False)
    
    return result

if __name__ == "__main__":
    audio_path = sys.argv[1] if len(sys.argv) > 1 else "downloads/original_audio.mp3"
    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        sys.exit(1)
        
    output_dir = "processed"
    os.makedirs(output_dir, exist_ok=True)
    
    # Using 'base' for a balance of speed and accuracy on CPU
    result = transcribe(audio_path, model_name="base")
    
    output_path = os.path.join(output_dir, "transcription.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Transcription saved to {output_path}")
    print(f"Full text snippet: {result['text'][:200]}...")
