from typing import Optional

from pydantic import BaseModel


class Service(BaseModel):
    name: Optional[str]
    protectThreshold: float = 0
    appName: Optional[str]
    groupName: Optional[str]
    metadata: dict = {}

    def __str__(self):
        return "Service{name='" + self.name + "', protectThreshold=" + str(self.protectThreshold) + ", appName='" + \
            self.appName + "', groupName='" + self.groupName + "', metadata=" + str(self.metadata) + "}"
