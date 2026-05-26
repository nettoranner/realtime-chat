from sqlalchemy.orm import Mapped, mapped_column

from src.database.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]