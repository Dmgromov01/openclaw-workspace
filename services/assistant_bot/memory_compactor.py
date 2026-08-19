import os
import glob
import json
import logging
from datetime import datetime, timedelta
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("memory_compactor")

MEMORY_DIR = "/root/openclaw/memory"
MAIN_MEMORY_FILE = "/root/openclaw/MEMORY.md"
SECRETS_FILE = "/etc/openclaw/secrets.json"

def get_deepseek_key() -> str:
    if os.path.exists(SECRETS_FILE):
        try:
            with open(SECRETS_FILE) as f:
                return json.load(f).get("deepseek_key", "").strip()
        except Exception:
            pass
    cred_file = "/root/.openclaw/credentials/deepseek.key"
    if os.path.exists(cred_file):
        return open(cred_file).read().strip()
    return ""

def call_deepseek_sync(prompt: str, key: str) -> str:
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system", 
                "content": "Ты архивариус памяти ИИ. Твоя задача — извлечь долгосрочные знания, факты, договоренности и отбросить мелкий бытовой шум."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"].strip()

def compact_memory():
    key = get_deepseek_key()
    if not key:
        logger.error("Ключ DeepSeek не найден для компактизации.")
        return

    # Собираем файлы за последние 7 дней
    today = datetime.now()
    recent_texts = []
    
    for i in range(7):
        d_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        fpath = os.path.join(MEMORY_DIR, f"{d_str}.md")
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                recent_texts.append(f"### Дневник {d_str}:\n" + f.read())

    if not recent_texts:
        logger.info("Нет новых записей за прошедшую неделю.")
        return

    all_logs = "\n\n".join(recent_texts)

    prompt = (
        f"Ниже представлены дневниковые логи активности за неделю:\n\n"
        f"{all_logs}\n\n"
        f"Сделай следующее:\n"
        f"1. Отбрось разовый шум (напоминания 'купить хлеб', временные технические тесты, мелкую рутину).\n"
        f"2. Выдели фундаментальные факты: ключевые договоренности, инсайты из статей, решения по проектам, даты крупных событий.\n"
        f"3. Оформи результат в виде компактного Markdown-списка с датами (3-7 пунктов максимум)."
    )

    logger.info("Отправка логов на компактизацию в DeepSeek...")
    summary = call_deepseek_sync(prompt, key)

    # Дописываем выжимку в MEMORY.md
    archive_header = f"\n\n## 📦 Итоги недели ({today.strftime('%Y-%m-%d')})\n"
    with open(MAIN_MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(archive_header + summary + "\n")

    logger.info("✅ Долгосрочная память MEMORY.md успешно обновлена и компактизирована.")

if __name__ == "__main__":
    compact_memory()
