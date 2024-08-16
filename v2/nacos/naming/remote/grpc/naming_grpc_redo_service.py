from v2.nacos.transport.connection import Connection

class ConnectionEventListener():
  def __init__(self):
    pass

  def onConnected(self, connection:Connection):
    pass

  def onDisConnect(self, connection:Connection):
    pass


class NamingGrpcRedoService(ConnectionEventListener):
  def __init__(self):
    pass

  def isConnected(self):
    pass

  def cacheInstanceForRedo(self):
    pass

  def instanceRegistered(self):
    pass

  def instanceDeregister(self):
    pass

  def instanceDeregistered(self):
    pass

  def removeInstanceForRedo(self):
    pass

  def findInstanceRedoData(self):
    pass

  def cacheSubscriberForRedo(self):
    pass

  def subscriberRegistered(self):
    pass

  def isSubscriberRegistered(self):
    pass

  def removeSubscriberForRedo(self):
    pass

  def findSubscriberRedoData(self):
    pass

  def getRegisteredInstancesByKey(self):
    pass

  def shutdown(self):
    pass

