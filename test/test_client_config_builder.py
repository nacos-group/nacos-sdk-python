import unittest

from v2.nacos.common.client_config_builder import ClientConfigBuilder


class ClientConfigBuilderTest(unittest.TestCase):
    def test_update_cache_when_empty_default_keeps_false(self):
        client_config = ClientConfigBuilder().build()

        self.assertFalse(client_config.update_cache_when_empty)

    def test_update_cache_when_empty_can_be_configured(self):
        client_config = ClientConfigBuilder().update_cache_when_empty(True).build()

        self.assertTrue(client_config.update_cache_when_empty)

    def test_update_cache_when_empty_keeps_builder_chainable(self):
        builder = ClientConfigBuilder()

        self.assertIs(builder.update_cache_when_empty(False), builder)
