import logging
from datetime import datetime
from sqlalchemy import select
from models import DigestArticle
from database import AsyncSessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("digest_pipeline")

def _clip_text(text: str, max_len: int = 400) -> str:
    if len(text) <= max_len:
        return text
    clipped = text[:max_len].rsplit(" ", 1)[0]
    return f"{clipped}..."

async def process_article(
    source: str,
    title: str,
    url: str,
    raw_content: str,
    llm_generate_fn
) -> DigestArticle | None:
    async with AsyncSessionLocal() as session:
        stmt = select(DigestArticle).where(DigestArticle.url == url)
        existing = await session.scalar(stmt)
        if existing:
            return None

    prompt = (
        f"Сделай краткое связное саммари для новости на русском языке. "
        f"Сохраняй факты, цифры и контекст, без воды.\n\n"
        f"Заголовок: {title}\n"
        f"Текст: {raw_content}"
    )

    try:
        raw_summary = await llm_generate_fn(prompt)
        summary = _clip_text(raw_summary.strip(), max_len=600)
    except Exception as e:
        logger.error(f"Ошибка вызова LLM для {url}: {e}")
        return None

    async with AsyncSessionLocal() as session:
        article = DigestArticle(
            source=source,
            title=title,
            url=url,
            summary=summary,
            published_at=datetime.utcnow()
        )
        session.add(article)
        await session.commit()
        await session.refresh(article)
        return article
