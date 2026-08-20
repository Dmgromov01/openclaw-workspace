import os
from pathlib import Path
import pandas as pd
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import FSInputFile

UPLOAD_DIR = Path("/root/openclaw/storage/uploads")
REPORT_DIR = Path("/root/openclaw/storage/reports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def inspect_excel_file(file_path: str) -> str:
    """Извлекает первичную сводку по загруженному Excel-файлу."""
    try:
        xl = pd.ExcelFile(file_path)
        summary = [f"Листов найдено: {len(xl.sheet_names)}"]
        for sheet in xl.sheet_names[:5]:
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=3)
            cols = ", ".join(map(str, df.columns[:8]))
            summary.append(f"• Лист '{sheet}': колонки [{cols}]")
        return "\n".join(summary)
    except Exception as e:
        return f"Не удалось прочитать структуру: {e}"

async def handle_incoming_document(message: types.Message, bot: Bot):
    doc = message.document
    if not doc:
        return

    ext = Path(doc.file_name).suffix.lower()
    allowed_exts = {".xlsx", ".xls", ".csv", ".pdf"}
    
    if ext not in allowed_exts:
        await message.reply("Поддерживаются форматы: .xlsx, .xls, .csv, .pdf")
        return

    dest_path = UPLOAD_DIR / f"{message.from_user.id}_{doc.file_name}"
    await bot.download(doc, destination=dest_path)
    
    if ext in {".xlsx", ".xls", ".csv"}:
        info = inspect_excel_file(str(dest_path))
        await message.reply(
            f"Файл <b>{doc.file_name}</b> сохранён и готов к анализу.\n\n"
            f"<b>Структура:</b>\n{info}\n\n"
            f"<i>Задайте вопрос по данным (SQL, поиск или отчёт).</i>",
            parse_mode="HTML"
        )
    else:
        await message.reply(
            f"Документ <b>{doc.file_name}</b> загружен в систему обработки.",
            parse_mode="HTML"
        )

async def send_generated_report(chat_id: int, bot: Bot, file_path: str, caption: str = None, chart_image_path: str = None):
    """Отправляет сгенерированный Excel-файл и опциональный график в чат."""
    if chart_image_path and os.path.exists(chart_image_path):
        photo = FSInputFile(chart_image_path)
        await bot.send_photo(chat_id=chat_id, photo=photo, caption="График к отчету")

    if os.path.exists(file_path):
        doc = FSInputFile(file_path)
        await bot.send_document(chat_id=chat_id, document=doc, caption=caption or "Сгенерированный отчёт Excel")
