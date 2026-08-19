import urllib.parse
import urllib.request
import os
import time
import base64

def process_ai_photo(input_path: str, output_path: str, user_instruction: str = "") -> str:
    """
    AI Image-to-Image / Рестайлинг и редактирование фото через Flux (Pollinations).
    """
    default_style = (
        "masterpiece, award-winning photography, professional studio lighting, "
        "shot on 85mm f/1.4 lens, clean background, sharp focus, cinematic color grading, 8k uhd"
    )
    
    if user_instruction and user_instruction.strip():
        final_prompt = f"{user_instruction.strip()}, {default_style}"
    else:
        final_prompt = f"enhance to professional high-end studio photography, soft rim light, {default_style}"

    encoded_prompt = urllib.parse.quote(final_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux&seed={int(time.time())}"

    headers = {"User-Agent": "OpenClaw-Bot/1.0"}
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=90) as response, open(output_path, "wb") as out_file:
        out_file.write(response.read())
        
    return output_path
