from typing import Optional

from pydantic import BaseModel


class ConfigItem(BaseModel):
    id: str = ''
    dataId: str = ''
    group: str = ''
    content: str = ''
    md5: Optional[str] = ''
    tenant: str = ''
    appname: str = ''


class ConfigPage(BaseModel):
    totalCount: int = 0
    pageNumber: int = 0
    pagesAvailable: int = 0
    pageItems: list[ConfigItem] = []


class ConfigListenContext(BaseModel):
    group: str = ''
    md5: str = ''
    dataId: str = ''
    tenant: str = ''


class ConfigContext(BaseModel):
    group: str = ''
    dataId: str = ''
    tenant: str = ''


class CacheDataListener:
    def __init__(self, listener, last_md5):
        self.listener = listener
        self.last_md5 = last_md5
