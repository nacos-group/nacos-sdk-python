from typing import List

class ConfigItem:
    def __init__(self, id: int, data_id: str, group: str, content: str, md5: str, tenant: str, appname: str):
        self.id = id
        self.data_id = data_id
        self.group = group
        self.content = content
        self.md5 = md5
        self.tenant = tenant
        self.appname = appname

class ConfigPage:
    def __init__(self, total_count: int, page_number: int, pages_available: int, page_items: List[ConfigItem]):
        self.total_count = total_count
        self.page_number = page_number
        self.pages_available = pages_available
        self.page_items = page_items

class ConfigListenContext:
    def __init__(self, group: str, md5: str, data_id: str, tenant: str):
        self.group = group
        self.md5 = md5
        self.data_id = data_id
        self.tenant = tenant

class ConfigContext:
    def __init__(self, group: str, data_id: str, tenant: str):
        self.group = group
        self.data_id = data_id
        self.tenant = tenant