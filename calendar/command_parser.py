#!/usr/bin/env python3
"""
Парсер команд календаря + отправки в Telegram.

Понимает формат:
  <действие/встреча/событие> [@ник / ник] <дата> <время> [отправить мем|<текст мема>]
  <действие> [@ник] <дата> <время> [отправить новости|<источник>]

Примеры:
  встреча с @ivanov 15.08.2026 14:00
  позвонить @petrov завтра в 10:00
  встреча с @sidorov 20.08.2026 15:00 отправить мем пошлый мем
  созвон @anna 21.08.2026 11:30 отправить новости из Медузы

Возвращает структурированный результат: summary, дата, адресат, команда (invite|meme|news), аргумент команды.
"""

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def _clean_summary(text: str) -> str:
    """Оставляет только описание события, убирая даты, время, ники, служебные слова."""
    t = text
    # убираем ники (но @name не трогаем как часть названия? нет — уберём, адресат отдельно)
    t = re.sub(r"@[\w_]+", "", t)
    # убираем даты DD.MM.YYYY / DD.MM.YY
    t = re.sub(r"\d{1,2}\.\d{1,2}\.\d{2,4}", "", t)
    # убираем время HH:MM
    t = re.sub(r"\b\d{1,2}:\d{2}\b", "", t)
    # убираем относительные слова и предлоги (НЕ трогаем слово "встреча" — оно часто часть названия)
    t = re.sub(r"\b(сегодня|завтра|послезавтра|на)\b", " ", t, flags=re.IGNORECASE)
    # убираем ведущее "в" перед временем ("в 10:00") — уже убрано времени; уберём остаточное "в"
    t = re.sub(r"\bв\b", " ", t, flags=re.IGNORECASE)
    # убираем команды отправки (всё, что после "отправить ...")
    t = re.sub(r"отправить\s+(мем|новости).*$", "", t, flags=re.IGNORECASE)
    # убираем лишние пробелы / знаки
    t = re.sub(r"\s+", " ", t).strip()
    t = t.strip("., ").strip()
    # убираем хвостовые предлоги "с / на / в" в конце (остались после удаления ника)
    t = re.sub(r"\s+(с|на|в|со)$", "", t, flags=re.IGNORECASE).strip()
    t = t.strip("., ").strip()
    # если остался один "с" или пусто — "Новая встреча"
    t = re.sub(r"^с\s*$", "", t, flags=re.IGNORECASE).strip()
    return t or "Новая встреча"


def parse_command(text: str):
    """
    Разбирает команду. Возвращает dict:
      {ok, summary, datetime, username, action (add|invite|meme|news), action_arg, raw}
    """
    t = text.strip()
    low = t.lower()

    result = {
        "ok": False,
        "summary": None,
        "dt": None,
        "username": None,
        "action": "add",      # add = просто добавить в календарь
        "action_arg": None,
        "raw": text,
        "reason": None,
    }

    # 1) Определяем команду отправки (мем/новости)
    action = "add"
    action_arg = None
    m_meme = re.search(r"отправить\s+мем([\s,.]*(.+))?$", low)
    m_news = re.search(r"отправить\s+новости([\s,.]*(.+))?$", low)
    if m_meme:
        action = "meme"
        # что за мем (текст после "мем")
        arg = m_meme.group(2)
        action_arg = arg.strip().strip("., ") if arg else None
    elif m_news:
        action = "news"
        arg = m_news.group(2)
        # нормализуем "из Медузы" -> "Медуза"
        arg = re.sub(r"^(из|от|с)\s+", "", (arg or "").strip(), flags=re.IGNORECASE).strip().strip("., ")
        action_arg = arg or None

    # 2) Находим ник адресата
    username = None
    m_user = re.search(r"@([\w_]+)", t)
    if m_user:
        username = m_user.group(1)
    else:
        # ищем "с <слово>" — но осторожно, чтобы не захватить описание
        # приоритет: явный @
        pass

    # 3) Ищем дату и время
    dm = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", t)
    tm = re.search(r"(\d{1,2}):(\d{2})", t)

    now = datetime.now(MOSCOW_TZ)
    dt = None

    if dm:
        day, mon, year = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
        if year < 100:
            year = 2000 + year
        if not tm:
            # Дата есть, но время не указано — напоминаем указать время
            result["reason"] = (
                f"⚠️ Не указано время. Укажи время, например: Встреча с @ник {day:02d}.{mon:02d}.{year} 14:00"
            )
            return result
        hh, mm = int(tm.group(1)), int(tm.group(2))
        try:
            dt = datetime(year, mon, day, hh, mm, tzinfo=MOSCOW_TZ)
        except ValueError:
            result["reason"] = "Некорректная дата"
            return result
    else:
        # относительные
        target = None
        if "послезавтра" in low:
            target = now + timedelta(days=2)
        elif "завтра" in low:
            target = now + timedelta(days=1)
        elif "сегодня" in low:
            target = now
        if target and tm:
            hh, mm = int(tm.group(1)), int(tm.group(2))
            dt = target.replace(hour=hh, minute=mm, second=0, microsecond=0)

    if dt is None:
        result["reason"] = "Не найдена дата и время (нужно: ДД.ММ.ГГГГ ЧЧ:ММ или 'завтра/сегодня ЧЧ:ММ')"
        return result

    # 4) Summary — оставшийся текст
    summary = _clean_summary(t)

    result["ok"] = True
    result["summary"] = summary
    result["dt"] = dt
    result["username"] = username
    result["action"] = action
    result["action_arg"] = action_arg
    return result


if __name__ == "__main__":
    import sys, json
    tests = [
        "встреча с @ivanov 15.08.2026 14:00",
        "позвонить @petrov завтра в 10:00",
        "встреча с @sidorov 20.08.2026 15:00 отправить мем пошлый мем",
        "созвон @anna 21.08.2026 11:30 отправить новости из Медузы",
        "позвонить Иванову 15.08.2026 14:00",
        "купить молоко 21.08.2026 9:00",
        "встреча без адресата 22.08.2026 12:00 отправить новости",
        "просто текст без даты",
    ]
    for t in tests:
        r = parse_command(t)
        out = {k: (v.strftime("%d.%m.%Y %H:%M") if k == "dt" and v else v) for k, v in r.items()}
        print(json.dumps(out, ensure_ascii=False, default=str))
