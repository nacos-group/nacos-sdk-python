# -*- coding: utf8 -*-

from __future__ import print_function
import unittest
import nacos
from nacos import files
import time
import shutil

SERVER_ADDRESSES = "100.69.207.65:8848, 100.69.207.66:8848"
NAMESPACE = "6cface1f-2f1b-4744-a59d-fd818b91a799"
# NAMESPACE = ""

client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)


class TestClient(unittest.TestCase):
    def test_get_server(self):
        self.assertEqual(client.get_server(), ("100.69.207.65", 8848))

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
        client2 = nacos.NacosClient("100.69.207.66:8848, 100.69.207.65:8848", namespace=NAMESPACE)
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
        client2 = nacos.NacosClient(SERVER_ADDRESSES)
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
        client2 = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)
        client2.current_server = ("1.100.84.215", 8080)
        d = "test_snap"
        g = "group"
        key = "+".join([d, g, NAMESPACE])
        files.save_file(client2.snapshot_base, key, u"yyy中文")
        self.assertEqual(client2.get_config(d, g), u"yyy中文")
        shutil.rmtree(client2.snapshot_base)

    def test_add_naming_instance(self):
        self.assertEqual(
            client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True), True)

    def test_remove_naming_instance(self):
        print(client.remove_naming_instance("test.service", "1.0.0.1", 8080))

    def test_modify_naming_instance(self):
        self.assertEqual(
            client.modify_naming_instance("test.service", "1.0.0.1", 8080, cluster_name="testCluster", enable=False,
                                          metadata="{a:'a'}"), True)

    def test_list_naming_instance(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True)
        self.assertEqual(len(client.list_naming_instance("test.service")["hosts"]), 1)

    def test_get_naming_instance(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True)
        self.assertEqual(client.get_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2")['ip'], u'1.0.0.1')

    def test_send_heartbeat(self):
        client.add_naming_instance("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}", False, True)
        self.assertEqual(
            client.send_heartbeat("test.service", "1.0.0.1", 8080, "testCluster2", 0.1, "{}")["clientBeatInterval"] > 0,
            True)


if __name__ == '__main__':
    unittest.main()
