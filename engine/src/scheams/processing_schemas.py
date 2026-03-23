from pydantic import BaseModel


class ProcessingBody(BaseModel):
    text: str
