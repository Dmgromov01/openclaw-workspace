from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    """Пользователи и настройки."""
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DigestArticle(Base):
    """Готовые статьи дайджеста. Промпты и сырые тексты не сохраняются."""
    __tablename__ = "digest_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    url: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    summary: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
