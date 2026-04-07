from pydantic import BaseModel


class ProcessingBody(BaseModel):
    """Текст входящего сообщения"""

    text: str
