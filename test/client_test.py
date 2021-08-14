# -*- coding: utf8 -*-

from __future__ import print_function

import sys
import unittest
import nacos
from nacos import files
from nacos.listener import SubscribeListener, SimpleListenerManager
from nacos.timer import NacosTimer, NacosTimerManager
import time
import shutil

SERVER_1 = "100.69.207.65"
SERVER_ADDRESSES = "%s:8848, 100.69.207.66:8848" % SERVER_1
SERVER_ADDRESSES = "127.0.0.1:8848"
NAMESPACE = "6cface1f-2f1b-4744-a59d-fd818b91a799"
NAMESPACE = ""

# Set the following values if authentication mode is enabled on the server
USERNAME = None
PASSWORD = None

client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username=USERNAME, password=PASSWORD)
# Set the following option if http requests need through by proxy
# client.set_options(proxies={"http":"192.168.56.1:809"})

class TestClient(unittest.TestCase):
    def test_get_server(self):
        self.assertEqual(client.get_server(), (SERVER_1, 8848))

    def test_set_get_remove_config(self):
        d = "test"
        g = "DEFAULT_GROUP"
        content = u"test中文"
        self.assertEqual(client.publish_config(d, g, content), True)
        time.sleep(0.5)
        self.assertEqual(client.get_config(d, g), content)
        self.assertEqual(client.remove_config(d, g), True)
        time.sleep(0.5)
        self.assertEqual(client.get_config(d, g), None)

    def test_server_failover(self):
        client2 = nacos.NacosClient("100.69.207.66:8848, %s:8848" % SERVER_1, namespace=NAMESPACE, username=USERNAME,
                                    password=PASSWORD)
        d = "test"
        g = "DEFAULT_GROUP"
        content = u"test中文"
        self.assertEqual(client2.publish_config(d, g, content), True)
        time.sleep(0.5)
        self.assertEqual(client2.get_config(d, g), content)
        self.assertEqual(client2.remove_config(d, g), True)
        time.sleep(0.5)
        self.assertEqual(client2.get_config(d, g), None)

    def test_fake_watcher(self):
        d = "test"
        g = "DEFAULT_GROUP"

        class Share:
            content = None
            count = 0

        cache_key = "+".join([d, g, NAMESPACE])

        def test_cb(args):
            print(args)
            Share.count += 1
            Share.content = args["content"]

        client.add_config_watcher(d, g, test_cb)
        client.add_config_watcher(d, g, test_cb)
        client.add_config_watcher(d, g, test_cb)
        time.sleep(1)
        client.notify_queue.put((cache_key, "xxx", "md51"))
        time.sleep(1)
        self.assertEqual(Share.content, "xxx")
        self.assertEqual(Share.count, 3)

        client.remove_config_watcher(d, g, test_cb)
        Share.count = 0
        client.notify_queue.put((cache_key, "yyy", "md52"))
        time.sleep(1)
        self.assertEqual(Share.content, "yyy")
        self.assertEqual(Share.count, 2)

        client.remove_config_watcher(d, g, test_cb, True)
        Share.count = 0
        client.notify_queue.put((cache_key, "not effective, no watchers", "md53"))
        time.sleep(1)
        self.assertEqual(Share.content, "yyy")
        self.assertEqual(Share.count, 0)

        Share.count = 0
        client.add_config_watcher(d, g, test_cb)
        time.sleep(1)
        client.notify_queue.put((cache_key, "zzz", "md54"))
        time.sleep(1)
        self.assertEqual(Share.content, "zzz")
        self.assertEqual(Share.count, 1)

        Share.count = 0
        client.notify_queue.put((cache_key, "not effective, md5 no changes", "md54"))
        time.sleep(1)
        self.assertEqual(Share.content, "zzz")
        self.assertEqual(Share.count, 0)

    def test_long_pulling(self):
        client2 = nacos.NacosClient(SERVER_ADDRESSES, username=USERNAME, password=PASSWORD)
        d = "test1_pulling"
        g = "Group1"
        g2 = "Group2"

        class Share:
            content = None

        def cb(x):
            Share.content = x["content"]
            print(Share.content)

        client2.publish_config(d, g, "test2")
        client2.publish_config(d, g2, "test2")
        time.sleep(0.5)
        # test common
        client2.add_config_watcher(d, g, cb)
        client2.add_config_watcher(d, g2, cb)
        time.sleep(0.5)
        client2.publish_config(d, g, "test")
        client2.publish_config(d, g2, "test")
        time.sleep(1)
        self.assertEqual(Share.content, "test")
        client2.publish_config(d, g2, u"test2中文")
        time.sleep(1)
        self.assertEqual(Share.content, u"test2中文")

    def test_get_from_failover(self):
        d = "test_fo"
        g = "group"
        key = "+".join([d, g, NAMESPACE])
        files.save_file(client.failover_base, key, u"xxx中文")
        print(client.get_config(d, g))
        self.assertEqual(client.get_config(d, g), u"xxx中文")
        shutil.rmtree(client.failover_base)

    def test_get_from_snapshot(self):
        client2 = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE, username=USERNAME, password=PASSWORD)
        client2.current_server = ("1.100.84.215", 8080)
        d = "test_snap"
        g = "group"
        key = "+".join([d, g, NAMESPACE])
        files.save_file(client2.snapshot_base, key, u"yyy中文")
        self.assertEqual(client2.get_config(d, g), u"yyy中文")
        shutil.rmtree(client2.snapshot_base)

    def test_add_naming_instance(self):
        self.assertEqual(
            client.add_naming_instance("test.service1", "1.0.0.7", 8080, "testCluster2", 0.2, "{}", False, True), True)

    def test_add_naming_instance_with_dict_metadata(self):
        self.assertEqual(
            client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, {"a": "c"}, False, True),
            True)

    def test_remove_naming_instance(self):
        print(client.remove_naming_instance("test.service", "1.0.0.1", 8080))

    def test_modify_naming_instance(self):
        self.assertEqual(
            client.modify_naming_instance("test.service", "1.0.0.1", 8080, cluster_name="testCluster", enable=False,
                                          metadata='{"a":"a"}'), True)

    def test_modify_naming_instance_with_dict_metadata(self):
        self.assertEqual(
            client.modify_naming_instance("test.service", "1.0.0.1", 8080, cluster_name="testCluster", enable=False,
                                          metadata={"a": "b"}), True)

    def test_list_naming_instance_offline(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True)
        self.assertEqual(len(client.list_naming_instance("test.service")["hosts"]), 0)

    def test_list_naming_instance_online(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", True, True)
        self.assertEqual(len(client.list_naming_instance("test.service")["hosts"]), 1)

    def test_get_naming_instance(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True)
        self.assertEqual(client.get_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2")['ip'], u'1.0.0.1')

    def test_send_heartbeat(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True)
        self.assertEqual(
            client.send_heartbeat("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}")["clientBeatInterval"] > 0,
            True)

    def test_send_heartbeat_with_dict_metadata(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, {"a": "c"}, False, True)
        self.assertEqual(
            client.send_heartbeat("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, {"a": "c"})[
                "clientBeatInterval"] > 0,
            True)

    # nacos timer test
    def print_hello(self, name):
        #  模拟调度方法中异常
        if name == 'exception':
            print("{name} enter exception".format(name=name))
            1 / 0
        tip = "{name} say Hello at {time}".format(name=name, time=time.time())
        print(tip)
        return tip

    def test_nacos_timer(self):
        # sample
        nt1 = NacosTimer("test_timer1", self.print_hello, 3, "nacos1")
        nt1.scheduler()
        nt2 = NacosTimer("test_timer2", self.print_hello, 3, "nacos2")
        nt2.scheduler()

        time.sleep(10)
        nt1.cancel()
        nt2.cancel()
        pass

    def timer_on_result_callback(self, res):
        print("timer_on_result_callback :" + res)

    def timer_on_exception_callback(self, ex):
        print("timer_on_exception_callback :{ex}".format(ex=ex))

    def test_nacos_timer_on_callback(self):
        # simple timer scheduler
        nt1 = NacosTimer("test_timer1", self.print_hello, 3, "nacos1")
        nt1.set_on_result(self.timer_on_result_callback)
        nt1.scheduler()

        # execute timer with exception ignored
        nt2 = NacosTimer("test_timer2", self.print_hello, 3, "exception")
        nt2.set_on_exception(self.timer_on_exception_callback).set_ignore_ex(True)
        nt2.scheduler()

        time.sleep(10)
        nt1.cancel()
        nt2.cancel()

    def test_nacos_timer_manager(self):
        nt1 = NacosTimer("test_timer1", self.print_hello, 3, "nacos1")
        nt2 = NacosTimer("test_timer2", self.print_hello, 3, "nacos2")

        ntm = NacosTimerManager()
        ntm.add_timer(nt1).add_timer(nt2)
        ntm.execute()

        # show all timers in manager
        for name, timer in ntm.all_timers().items():
            print("current timer in manager: {name}".format(name=name))

        # block
        time.sleep(5)
        # cancel timer in manager
        ntm.cancel_timer(nt1.name)
        for name, timer in ntm.all_timers().items():
            print("current timer in manager: {name} after canceled".format(name=name))

        # stop timer
        ntm.stop()

    def test_service_subscribe(self):
        def fn_listener1(event, instance):
            print("fn_listener1 is listening ==> ", event, instance.instance)
            pass

        def fn_listener2(event, instance):
            print("fn_listener2 is listening ==> ", event, instance.instance)
            pass

        def fn_listener3(event, instance):
            print("fn_listener3 is listening ==> ", event, instance.instance)
            pass

        fn1 = SubscribeListener(fn=fn_listener1, listener_name="fn_listener1")
        fn2 = SubscribeListener(fn=fn_listener2, listener_name="fn_listener2")
        fn3 = SubscribeListener(fn=fn_listener3, listener_name="fn_listener3")

        # tuple
        # client.subscribe((fn1, fn2), 3, "test.service", )
        # list
        # client.subscribe([fn1, fn2], 3, "test.service")
        # single function
        client.subscribe(fn1, 2, "test.service1", )
        client.subscribe(fn2, 2, "test.service")
        # client.subscribe(fn3, 2, "test.service")
        print("subscribe finished")

        # unsubscribe
        time.sleep(10)
        client.unsubscribe(service_name="test.service1", listener_name="fn_listener1")
        print("test.service1 has unsubscribed")

        #  stop subscribe
        time.sleep(5)
        client.stop_subscribe()
        print("subscribe has stopped")


if __name__ == '__main__':
    unittest.main()
