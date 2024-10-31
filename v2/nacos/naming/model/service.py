from pydantic import BaseModel


class ServiceList(BaseModel):
    count: int
    services: list[str]
