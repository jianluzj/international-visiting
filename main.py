import subprocess
import sys
import os
import argparse

def run_step(step_name, command):
    print(f"\n>>> Starting {step_name}...")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"!!! Error in {step_name}. Exiting.")
        sys.exit(result.returncode)
    print(f"--- {step_name} completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="International Visiting: English to Chinese Podcast Converter")
    parser.add_argument("url", help="Apple Podcasts URL")
    parser.add_argument("--llm-key", help="LLM API Key (optional if set in env)")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for hosting (default: http://localhost:8000)")
    parser.add_argument("--full", action="store_true", help="Process the full audio (default is test snippet)")
    
    args = parser.parse_args()
    
    python_bin = "./venv/bin/python3"
    
    # 1. Download
    run_step("Download", f"{python_bin} downloader.py \"{args.url}\"")
    
    audio_file = "downloads/original_audio.mp3"
    if not args.full:
        print(">>> Creating 5-minute snippet for testing...")
        snippet_file = "downloads/test_snippet.mp3"
        subprocess.run(f"ffmpeg -y -ss 0 -t 300 -i {audio_file} -acodec copy {snippet_file}", shell=True)
        audio_file = snippet_file

    # 2. Transcribe
    run_step("Transcription", f"{python_bin} transcriber.py {audio_file}")
    
    # 3. Translate
    env_vars = os.environ.copy()
    if args.llm_key:
        env_vars["LLM_API_KEY"] = args.llm_key
    
    # We pass the env to the subprocess for the key
    print("\n>>> Starting Translation...")
    # Using subprocess.run with env directly for translation step
    res = subprocess.run(f"{python_bin} translator.py", shell=True, env=env_vars)
    if res.returncode != 0:
        print("!!! Error in Translation. Exiting.")
        sys.exit(res.returncode)
    print("--- Translation completed successfully.")

    # 4. Synthesize
    run_step("Synthesis", f"{python_bin} synthesizer.py")
    
    # 5. RSS Generation
    env_vars["BASE_URL"] = args.base_url
    print("\n>>> Starting RSS Generation...")
    res = subprocess.run(f"{python_bin} rss_generator.py", shell=True, env=env_vars)
    if res.returncode != 0:
        print("!!! Error in RSS Generation. Exiting.")
        sys.exit(res.returncode)
    print("--- RSS Generation completed successfully.")

    print("\n" + "="*40)
    print("PROJECT COMPLETE!")
    print(f"Output files are in the 'output' directory.")
    print(f"1. Audio: output/chinese_podcast.mp3")
    print(f"2. RSS: output/podcast.xml")
    print(f"To host locally, run: cd output && python3 -m http.server 8000")
    print("="*40)

if __name__ == "__main__":
    main()
