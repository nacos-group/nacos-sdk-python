from threading import RLock

from v2.nacos.naming.dtos.service_info import ServiceInfo
from v2.nacos.naming.event.instances_change_event import InstancesChangeEvent
from v2.nacos.naming.event.naming_event import NamingEvent
from v2.nacos.naming.ievent_listener import EventListener
from v2.nacos.naming.utils.naming_utils import NamingUtils


class InstancesChangeNotifier:
    def __init__(self):
        self.listener_map = {}
        self.lock = RLock()

    def register_listener(self, group_name: str, service_name: str, clusters: str, listener: EventListener) -> None:
        key = ServiceInfo.get_key(NamingUtils.get_grouped_name(service_name, group_name), clusters)
        if key not in self.listener_map.keys():
            with self.lock:
                event_listeners = []
                self.listener_map[key] = event_listeners
        else:
            event_listeners = self.listener_map[key]

        event_listeners.append(listener)

    def deregister_listener(self, group_name: str, service_name: str, clusters: str, listener: EventListener) -> None:
        key = ServiceInfo.get_key(NamingUtils.get_grouped_name(service_name, group_name), clusters)
        if key not in self.listener_map.keys():
            return

        event_listeners = self.listener_map[key]
        event_listeners.remove(listener)
        if not event_listeners:
            self.listener_map.pop(key)

    def is_subscribed(self, group_name: str, service_name: str, clusters: str) -> bool:
        key = ServiceInfo.get_key(NamingUtils.get_grouped_name(service_name, group_name), clusters)
        if key in self.listener_map.keys() and self.listener_map[key]:
            return True
        else:
            return False

    def get_subscribe_services(self) -> list:
        service_infos = []
        for key in self.listener_map.keys():
            service_infos.append(ServiceInfo.from_key(key))
        return service_infos

    def on_event(self, event: InstancesChangeEvent) -> None:
        key = ServiceInfo.get_key(
            NamingUtils.get_grouped_name(event.get_service_name(), event.get_group_name()), event.get_clusters()
        )
        if key not in self.listener_map.keys():
            return

        event_listeners = self.listener_map[key]

        naming_event = self.__transfer_to_naming_event(event)
        for listener in event_listeners:
            listener.on_event(naming_event)

    @staticmethod
    def __transfer_to_naming_event(instances_change_event: InstancesChangeEvent):
        naming_event = NamingEvent(
            instances_change_event.get_service_name(), instances_change_event.get_group_name(),
            instances_change_event.get_clusters(), instances_change_event.get_hosts()
        )
        return naming_event
