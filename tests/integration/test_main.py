"""Module to test the main napp file."""
from unittest import TestCase
from unittest.mock import Mock, patch

from kytos.core.events import KytosEvent
from tests.integration.helpers import (get_controller_mock, get_interface_mock,
                                       get_switch_mock)

LINK_DATA = {
    "active": False,
    "enabled": True,
    "endpoint_a": {
        "id": "00:00:00:00:00:00:00:01:1",
        "link": "26927949-df3c-4c25-874b-3da30d8ae983",
        "mac": "26:fb:42:20:b8:b1",
        "name": "s1-eth1",
        "nni": False,
        "port_number": 1,
        "speed": "10 Gbps",
        "switch": "00:00:00:00:00:00:00:01",
        "type": "interface",
        "uni": True
    },
    "endpoint_b": {
        "id": "00:00:00:00:00:00:00:01:1",
        "link": "26927949-df3c-4c25-874b-3da30d8ae983",
        "mac": "26:fb:42:20:b8:b1",
        "name": "s1-eth1",
        "nni": False,
        "port_number": 1,
        "speed": "10 Gbps",
        "switch": "00:00:00:00:00:00:00:01",
        "type": "interface",
        "uni": True
    }
}

SWITCH_DATA = {
    "id": "00:00:00:00:00:00:00:01",
    "name": "my-beautiful-switch",
    "serial": "string",
    "software": "Version 2.3.4",
    "ofp_version": "0x01",
    "connection": "127.0.0.1:49330",
    "data_path": "string",
    "manufacturer": "Unkown Manufactor",
    "hardware": "Hardware version 2.0",
    "type": "switch",
    "active": True,
    "enabled": False,
    "dpid": "00:00:00:00:00:00:00:01",
    "metadata": {},
    "interfaces": {
        "additionalProp1": {
            "id": "00:00:00:00:00:00:00:01:1",
            "link": "26927949-df3c-4c25-874b-3da30d8ae983",
            "mac": "26:fb:42:20:b8:b1",
            "name": "s1-eth1",
            "nni": False,
            "port_number": 1,
            "speed": "10 Gbps",
            "switch": "00:00:00:00:00:00:00:01",
            "type": "interface",
            "uni": True
        },
        "additionalProp2": {
            "id": "00:00:00:00:00:00:00:01:1",
            "link": "26927949-df3c-4c25-874b-3da30d8ae983",
            "mac": "26:fb:42:20:b8:b1",
            "name": "s1-eth1",
            "nni": False,
            "port_number": 1,
            "speed": "10 Gbps",
            "switch": "00:00:00:00:00:00:00:01",
            "type": "interface",
            "uni": True
        },
        "additionalProp3": {
            "id": "00:00:00:00:00:00:00:01:1",
            "link": "26927949-df3c-4c25-874b-3da30d8ae983",
            "mac": "26:fb:42:20:b8:b1",
            "name": "s1-eth1",
            "nni": False,
            "port_number": 1,
            "speed": "10 Gbps",
            "switch": "00:00:00:00:00:00:00:01",
            "type": "interface",
            "uni": True
        }
    }
}


class FakeBox:
    """Simulate a Storehouse Box."""

    def __init__(self, data):
        """Initizalize default values to FakeBox."""
        self.data = data
        self.namespace = None
        self.name = None
        self.box_id = None
        self.created_at = None
        self.owner = None


# pylint: disable=bad-option-value
class TestMain(TestCase):
    """Test the Main class."""

    def setUp(self):
        """Execute steps before each tests.

        Set the server_name_url from kytos/topology
        """
        self.server_name_url = 'http://localhost:8181/api/kytos/topology'

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        from napps.kytos.topology.main import Main
        self.addCleanup(patch.stopall)
        self.napp = Main(get_controller_mock())
        self.init_napp()

    @patch('napps.kytos.topology.main.Main.verify_storehouse')
    def init_napp(self, mock_verify_storehouse=None):
        """Initialize a Topology NApp instance."""
        mock_verify_storehouse.return_value = None
        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        from napps.kytos.topology.main import Main
        self.addCleanup(patch.stopall)
        self.napp = Main(get_controller_mock())
        self.napp.store_items = {
            "links": FakeBox(LINK_DATA),
            "switches": FakeBox(SWITCH_DATA)
        }

    def test_get_switches_dict(self):
        """Basic test for switch listing."""
        # pylint: disable=protected-access
        switches = self.napp._get_switches_dict()
        assert isinstance(switches['switches'], dict)
        assert switches['switches'] == {}

    def test_get_event_listeners(self):
        """Verify all event listeners registered."""
        expected_events = ['kytos/core.shutdown',
                           'kytos/core.shutdown.kytos/topology',
                           '.*.interface.is.nni',
                           '.*.connection.lost',
                           '.*.switch.interface.created',
                           '.*.switch.interface.deleted',
                           '.*.switch.interface.link_down',
                           '.*.switch.interface.link_up',
                           '.*.switch.(new|reconnected)',
                           '.*.switch.port.created',
                           'kytos/topology.*.metadata.*']
        actual_events = self.napp.listeners()
        self.assertEqual(expected_events, actual_events)

    def test_verify_api_urls(self):
        """Verify all APIs registered."""
        expected_urls = [
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/interfaces'),
         ({}, {'POST', 'OPTIONS'}, '/api/kytos/topology/v3/metadata'),
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/switches'),
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/links'),
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/'),
         ({'dpid': '[dpid]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/interfaces/switch/<dpid>/disable'),
         ({'dpid': '[dpid]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/interfaces/switch/<dpid>/enable'),
         ({'key': '[key]', 'interface_id': '[interface_id]'},
          {'OPTIONS', 'DELETE'},
          '/api/kytos/topology/v3/interfaces/<interface_id>/metadata/<key>'),
         ({'interface_id': '[interface_id]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/interfaces/<interface_id>/metadata'),
         ({'interface_id': '[interface_id]'}, {'GET', 'OPTIONS', 'HEAD'},
          '/api/kytos/topology/v3/interfaces/<interface_id>/metadata'),
         ({'interface_disable_id': '[interface_disable_id]'},
          {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/interfaces/<interface_disable_id>/disable'),
         ({'interface_enable_id': '[interface_enable_id]'},
          {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/interfaces/<interface_enable_id>/enable'),
         ({'dpid': '[dpid]', 'key': '[key]'}, {'OPTIONS', 'DELETE'},
          '/api/kytos/topology/v3/switches/<dpid>/metadata/<key>'),
         ({'dpid': '[dpid]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/switches/<dpid>/metadata'),
         ({'dpid': '[dpid]'}, {'GET', 'OPTIONS', 'HEAD'},
          '/api/kytos/topology/v3/switches/<dpid>/metadata'),
         ({'dpid': '[dpid]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/switches/<dpid>/disable'),
         ({'dpid': '[dpid]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/switches/<dpid>/enable'),
         ({'link_id': '[link_id]', 'key': '[key]'}, {'OPTIONS', 'DELETE'},
          '/api/kytos/topology/v3/links/<link_id>/metadata/<key>'),
         ({'link_id': '[link_id]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/links/<link_id>/metadata'),
         ({'link_id': '[link_id]'}, {'GET', 'OPTIONS', 'HEAD'},
          '/api/kytos/topology/v3/links/<link_id>/metadata'),
         ({'link_id': '[link_id]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/links/<link_id>/disable'),
         ({'link_id': '[link_id]'}, {'POST', 'OPTIONS'},
          '/api/kytos/topology/v3/links/<link_id>/enable')]

        urls = self.get_napp_urls(self.napp)
        self.assertEqual(expected_urls, urls)

    @staticmethod
    def get_napp_urls(napp):
        """Return the kytos/topology urls.

        The urls will be like:

        urls = [
            (options, methods, url)
        ]

        """
        controller = napp.controller
        controller.api_server.register_napp_endpoints(napp)

        urls = []
        for rule in controller.api_server.app.url_map.iter_rules():
            options = {}
            for arg in rule.arguments:
                options[arg] = "[{0}]".format(arg)

            if f'{napp.username}/{napp.name}' in str(rule):
                urls.append((options, rule.methods, f'{str(rule)}'))

        return urls

    @staticmethod
    def get_app_test_client(napp):
        """Return a flask api test client."""
        napp.controller.api_server.register_napp_endpoints(napp)
        return napp.controller.api_server.app.test_client()

    def test_save_metadata_on_store(self):
        """Test save metadata on store."""
        event_name = 'kytos.storehouse.update'
        switch = get_switch_mock(0x04)
        event = KytosEvent(name=event_name,
                           content={'switch': switch})
        self.napp.save_metadata_on_store(event)
        event_response = self.napp.controller.buffers.app.get()
        self.assertEqual(event_response.name,
                         'kytos.storehouse.update')

    def test_handle_new_switch(self):
        """Test handle new switch."""
        event_name = '.*.switch.(new|reconnected)'
        switch = get_switch_mock(0x04)
        event = KytosEvent(name=event_name,
                           content={'switch': switch})
        self.napp.handle_new_switch(event)
        event_response = self.napp.controller.buffers.app.get()
        self.assertEqual(event_response.name,
                         'kytos/topology.updated')

    def test_handle_interface_created(self):
        """Test handle interface created."""
        event_name = '.*.switch.interface.created'
        interface = get_interface_mock("interface1", 7)
        stats_event = KytosEvent(name=event_name,
                                 content={'interface': interface})
        self.napp.handle_interface_created(stats_event)
        event_response = self.napp.controller.buffers.app.get()
        self.assertEqual(event_response.name,
                         'kytos/topology.updated')

    def test_handle_interface_deleted(self):
        """Test handle interface deleted."""
        event_name = '.*.switch.interface.deleted'
        interface = get_interface_mock("interface1", 7)
        stats_event = KytosEvent(name=event_name,
                                 content={'interface': interface})
        self.napp.handle_interface_deleted(stats_event)
        event_response = self.napp.controller.buffers.app.get()
        self.assertEqual(event_response.name,
                         'kytos/topology.updated')

    def test_handle_connection_lost(self):
        """Test handle connection lost."""
        event_name = '.*.connection.lost'
        source = Mock()
        stats_event = KytosEvent(name=event_name,
                                 content={'source': source})
        self.napp.handle_connection_lost(stats_event)
        event_response = self.napp.controller.buffers.app.get()
        self.assertEqual(event_response.name,
                         'kytos/topology.updated')
