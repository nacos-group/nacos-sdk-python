from v2.nacos.exception.nacos_exception import NacosException
from v2.nacos.naming.dtos.instance import Instance
from v2.nacos.naming.dtos.service_info import ServiceInfo


class Balancer:
    @staticmethod
    def get_host_by_random_weight(hosts: list) -> Instance:
        if not hosts:
            return None

        hosts_with_weight = []
        for host in hosts:
            if host.is_healthy():
                hosts_with_weight.append({"item": host, "weight": host.get_weight()})  # todo 改pair

    class RandomByWeight:
        @staticmethod
        def select_all(service_info: ServiceInfo) -> list:
            hosts = service_info.get_hosts()

            if not hosts:
                raise NacosException("no host to srv for service_info: " + service_info.get_name())

            return hosts

        @staticmethod
        def select_host(dom: ServiceInfo) -> Instance:
            hosts = Balancer.RandomByWeight.select_all(dom)

            if not hosts:
                raise NacosException("no host to srv for service: " + dom.get_name())

            return Balancer.get_host_by_random_weight(hosts)
