#!/usr/bin/env python3
"""Grok Imagine Image 2.0 via OpenRouter /images (стандарт генерации, $0.07/картинка).
Usage:
  gen_grok.py "<prompt>" [-o out.jpg] [-r ref.jpg] [-a 3:2] [-q medium|low]
Ключ читается из /root/.openclaw/credentials/openrouter.key.
"""
import json, base64, subprocess, sys, os, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", default="/root/openclaw/media/gen-grok.jpg")
    ap.add_argument("-r", "--ref", help="референс-фото (перекраска/редактирование)")
    ap.add_argument("-a", "--aspect", default="3:2")
    ap.add_argument("-q", "--quality", default="medium", choices=["low","medium"])
    a = ap.parse_args()

    key = open('/root/.openclaw/credentials/openrouter.key').read().strip()
    refs = []
    if a.ref:
        raw = open(a.ref,'rb').read()
        mime = "image/png" if a.ref.endswith(".png") else "image/jpeg"
        refs.append({"type":"image_url","image_url":{"url": f"data:{mime};base64," + base64.b64encode(raw).decode()}})
    payload = json.dumps({"model":"x-ai/grok-imagine-image-2.0","prompt":a.prompt,
        "aspect_ratio":a.aspect,"quality":a.quality,"input_references":refs})
    r = subprocess.run(["curl","-s","https://openrouter.ai/api/v1/images",
        "-H","Authorization: Bearer "+key,"-H","Content-Type: application/json","-d",payload],
        capture_output=True, text=True, timeout=300)
    d = json.loads(r.stdout)
    if 'data' in d:
        raw2 = base64.b64decode(d['data'][0]['b64_json'])
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        open(a.out,'wb').write(raw2)
        print(f"OK {a.out} ({len(raw2)}b, ${d.get('usage',{}).get('cost')})")
    else:
        print("ERROR:", str(d.get('error'))[:400]); sys.exit(1)

if __name__ == "__main__":
    main()
