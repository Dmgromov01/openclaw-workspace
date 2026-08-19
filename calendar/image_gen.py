import sys
import urllib.parse
import urllib.request
import os
import time

def generate_image(prompt: str, width: int = 1024, height: int = 1024, model: str = "flux") -> str:
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&model={model}&seed={int(time.time())}"
    
    out_dir = "/root/openclaw/workspace/media/outbox"
    os.makedirs(out_dir, exist_ok=True)
    
    timestamp = int(time.time())
    file_path = os.path.join(out_dir, f"gen_{timestamp}.jpg")
    
    headers = {"User-Agent": "OpenClaw-Bot/1.0"}
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=60) as response, open(file_path, "wb") as out_file:
        out_file.write(response.read())
        
    return file_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 image_gen.py '<промпт>' [width] [height]")
        sys.exit(1)
        
    prompt_arg = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    h = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    
    saved_path = generate_image(prompt_arg, width=w, height=h)
    print(saved_path)
