"""Telegram document intake and report delivery helpers."""
from __future__ import annotations

import html
import os
from pathlib import Path

import pandas as pd
from aiogram import Bot, types
from aiogram.types import FSInputFile

from .file_security import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES, upload_path

UPLOAD_DIR = Path("/root/openclaw/storage/uploads")
REPORT_DIR = Path("/root/openclaw/storage/reports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def inspect_tabular_file(file_path: str, extension: str) -> str:
    """Extract a small, non-sensitive structural summary from a table file."""
    try:
        if extension == ".csv":
            df = pd.read_csv(file_path, nrows=3)
            cols = ", ".join(map(str, df.columns[:8]))
            return f"Строк-примеров: {len(df)}; колонки [{html.escape(cols)}]"

        xl = pd.ExcelFile(file_path)
        summary = [f"Листов найдено: {len(xl.sheet_names)}"]
        for sheet in xl.sheet_names[:5]:
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=3)
            cols = ", ".join(map(str, df.columns[:8]))
            summary.append(f"• Лист '{html.escape(str(sheet))}': колонки [{html.escape(cols)}]")
        return "\n".join(summary)
    except Exception as exc:
        return f"Не удалось прочитать структуру файла: {html.escape(str(exc))[:500]}"


async def handle_incoming_document(message: types.Message, bot: Bot):
    doc = message.document
    if not doc:
        return

    original_name = doc.file_name or "upload"
    ext = Path(original_name.replace("\\", "/")).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        await message.reply("Поддерживаются форматы: .xlsx, .xls, .csv, .pdf")
        return
    if doc.file_size and doc.file_size > MAX_UPLOAD_BYTES:
        await message.reply("Файл слишком большой. Максимальный размер — 25 МБ.")
        return

    user_id = message.from_user.id if message.from_user else 0
    dest_path = upload_path(UPLOAD_DIR, user_id, message.message_id, original_name)
    await bot.download(doc, destination=dest_path)

    safe_name = html.escape(Path(dest_path).name)
    if ext in {".xlsx", ".xls", ".csv"}:
        info = inspect_tabular_file(str(dest_path), ext)
        await message.reply(
            f"Файл <b>{safe_name}</b> сохранён и готов к анализу.\n\n"
            f"<b>Структура:</b>\n{info}\n\n"
            f"<i>Задайте вопрос по данным (SQL, поиск или отчёт).</i>",
            parse_mode="HTML",
        )
    else:
        await message.reply(
            f"Документ <b>{safe_name}</b> загружен в систему обработки.",
            parse_mode="HTML",
        )


async def send_generated_report(
    chat_id: int,
    bot: Bot,
    file_path: str,
    caption: str | None = None,
    chart_image_path: str | None = None,
):
    """Send a generated Excel file and an optional chart to a chat."""
    if chart_image_path and os.path.exists(chart_image_path):
        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(chart_image_path),
            caption="График к отчету",
        )

    if os.path.exists(file_path):
        await bot.send_document(
            chat_id=chat_id,
            document=FSInputFile(file_path),
            caption=caption or "Сгенерированный отчёт Excel",
        )
