from v2.nacos.naming.remote.naming_client_proxy import NamingClientProxy
    

class NamingGrpcClientProxy():

    def __init__(self, namespace_id, security_proxy, server_list_factory, properties, service_info_holder):
        pass

    def start(self, server_list_factory, service_info_holder):
        pass

    def onEvent(self):
        pass

    def getRetainInstance(self):
        pass

    def compareIpAndPort(self):
        pass

    def doBatchRegisterService(self):
        pass

    def doRegisterService(self):
        pass

    def doRegisterServiceForPersistent(self):
        pass

    def deregisterService(self):
        pass

    def deregisterServiceForEphemeral(self):
        pass

    def doDeregisterService(self):
        pass

    def doDeregisterServiceForPersistent(self):
        pass

    def updateInstance(self):
        pass

    def queryInstancesOfService(self):
        pass

    def queryService(self):
        pass

    def createService(self):
        pass

    def deleteService(self):
        pass

    def updateService(self):
        pass

    def getServiceList(self):
        pass

    def subscribe(self):
        pass

    def doSubscribe(self):
        pass

    def unsubscribe(self):
        pass

    def isSubscribed(self):
        pass

    def serverHealthy(self):
        pass

    def isAbilitySupportedByServer(self):
        pass

    def requestToServer(self):
        pass

    def recordRequestFailedMetrics(self):
        pass

    def shutdown(self):
        pass

    def shutDownAndRemove(self):
        pass

    def isEnable(self):
        pass
    
