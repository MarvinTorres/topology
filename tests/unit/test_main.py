"""Module to test the main napp file."""
import time
import json
from io import BytesIO

from unittest import TestCase
from unittest.mock import MagicMock, create_autospec, patch

from kytos.core.switch import Switch
from kytos.core.interface import Interface
from kytos.core.link import Link
from kytos.lib.helpers import (get_switch_mock, get_interface_mock,
                               get_test_client)


from tests.unit.helpers import get_controller_mock, get_napp_urls


# pylint: disable=too-many-public-methods
class TestMain(TestCase):
    """Test the Main class."""
    # pylint: disable=too-many-public-methods

    def setUp(self):
        """Execute steps before each tests.

        Set the server_name_url_url from kytos/topology
        """
        self.server_name_url = 'http://localhost:8181/api/kytos/topology'

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        from napps.kytos.topology.main import Main
        self.addCleanup(patch.stopall)

        self.napp = Main(get_controller_mock())

    def test_get_event_listeners(self):
        """Verify all event listeners registered."""
        expected_events = ['kytos/core.shutdown',
                           'kytos/core.shutdown.kytos/topology',
                           'kytos/maintenance.start_link',
                           'kytos/maintenance.end_link',
                           'kytos/maintenance.start_switch',
                           'kytos/maintenance.end_switch',
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
        self.assertCountEqual(expected_events, actual_events)

    def test_verify_api_urls(self):
        """Verify all APIs registered."""
        expected_urls = [
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/interfaces'),
         ({}, {'POST', 'OPTIONS'}, '/api/kytos/topology/v3/metadata'),
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/switches'),
         ({}, {'GET', 'OPTIONS', 'HEAD'}, '/api/kytos/topology/v3/restore'),
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

        urls = get_napp_urls(self.napp)
        self.assertEqual(expected_urls, urls)

    @patch('napps.kytos.topology.main.StoreHouse.get_data')
    def test_restore_network_status(self, mock_storehouse):
        """Test restore_network_status."""
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_interface = get_interface_mock('s1-eth1', 1, mock_switch)
        mock_switch.interfaces = {1: mock_interface}
        self.napp.controller.switches = {dpid: mock_switch}
        status = {
            'network_status': {
                'id': 'network_status',
                'switches': {
                    '00:00:00:00:00:00:00:01': {
                        'dpid': '00:00:00:00:00:00:00:01',
                        'enabled': True,
                        'id': '00:00:00:00:00:00:00:01',
                        'interfaces': {
                            '00:00:00:00:00:00:00:01:1': {
                                'enabled': True,
                                'id': '00:00:00:00:00:00:00:01:1',
                            }
                        }
                    }
                }
            }
        }
        status_disable = {
            'network_status': {
                'id': 'network_status',
                'switches': {
                    '00:00:00:00:00:00:00:01': {
                        'dpid': '00:00:00:00:00:00:00:01',
                        'enabled': False,
                        'id': '00:00:00:00:00:00:00:01',
                        'interfaces': {
                            '00:00:00:00:00:00:00:01:1': {
                                'enabled': False,
                                'id': '00:00:00:00:00:00:00:01:1',
                            }
                        }
                    }
                }
            }
        }

        api = get_test_client(self.napp.controller, self.napp)
        mock_storehouse.side_effect = [{}, status, status_disable]

        # fail case
        url = f'{self.server_name_url}/v3/restore'
        response = api.get(url)
        self.assertEqual(response.status_code, 404, response.data)

        # enable
        url = f'{self.server_name_url}/v3/restore'
        response = api.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mock_switch.enable.call_count, 1)
        self.assertEqual(mock_interface.enable.call_count, 1)

        # disable
        url = f'{self.server_name_url}/v3/restore'
        response = api.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mock_switch.disable.call_count, 1)
        self.assertEqual(mock_interface.disable.call_count, 1)

    @patch('napps.kytos.topology.main.Main.save_status_on_storehouse')
    def test_enable_switch(self, mock_save_status):
        """Test enable_switch."""
        dpid = "00:00:00:00:00:00:00:01"
        mock_switch = get_switch_mock(dpid)
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        url = f'{self.server_name_url}/v3/switches/{dpid}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(mock_switch.enable.call_count, 1)
        mock_save_status.assert_called()

        # fail case
        mock_switch.enable.call_count = 0
        dpid = "00:00:00:00:00:00:00:02"
        url = f'{self.server_name_url}/v3/switches/{dpid}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(mock_switch.enable.call_count, 0)

    @patch('napps.kytos.topology.main.Main.save_status_on_storehouse')
    def test_disable_switch(self, mock_save_status):
        """Test disable_switch."""
        dpid = "00:00:00:00:00:00:00:01"
        mock_switch = get_switch_mock(dpid)
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        url = f'{self.server_name_url}/v3/switches/{dpid}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(mock_switch.disable.call_count, 1)
        mock_save_status.assert_called()

        # fail case
        mock_switch.disable.call_count = 0
        dpid = "00:00:00:00:00:00:00:02"
        url = f'{self.server_name_url}/v3/switches/{dpid}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(mock_switch.disable.call_count, 0)

    @patch('napps.kytos.topology.main.Main.notify_metadata_changes')
    def test_add_topology_metadata(self, mock_metadata_changes):
        """Test add_add_topology"""
        topology_init_state = {
            'switches':
            [
                {
                    'dpid':'00:00:00:00:00:00:00:01',
                    'interfaces':[
                        {'port':1,'name':'eth0'}
                    ]
                },
                {
                    'dpid':'00:00:00:00:00:00:00:02',
                    'interfaces':[
                        {'port':1,'name':'eth0'},
                        {'port':2,'name':'eth1'}
                    ]
                },
                {
                    'dpid':'00:00:00:00:00:00:00:03',
                    'interfaces':[
                        {'port':1,'name':'eth0'}
                    ]
                }
            ],
            'links':
            [
                {
                    'id': '00:00:00:00:00:00:00:01:1:00:00:00:00:00:00:00:02:2'
                }
            ]
        }
        mock_switches = {}
        for switch_data in topology_init_state['switches']:
            mock_switch = get_switch_mock(switch_data['dpid'])
            mock_switch.interfaces = {}
            for interface_data in switch_data['interfaces']:
                mock_interface = get_interface_mock(interface_data['name'], interface_data['port'], mock_switch)
                mock_switch.interfaces[interface_data['port']] = mock_interface
            mock_switches[switch_data['dpid']] = mock_switch

        # TODO: Add support for links in test_update_topology
        mock_links = {}
        for link_data in topology_init_state['links']:
            mock_link = MagicMock(Link)
            mock_link.id = link_data['id']
            mock_links[link_data['id']] = mock_link

        self.napp.controller.switches = mock_switches
        self.napp.links = mock_links
        api = get_test_client(self.napp.controller, self.napp)

        topology_update = {
            'switches':
            [
                {
                    'dpid':'00:00:00:00:00:00:00:01',
                    'metadata':{'color':'red','char':'A'},
                    'interfaces':[
                        {'port':1,'name':'eth0'}
                    ]
                },
                {
                    'dpid':'00:00:00:00:00:00:00:02',
                    'metadata':{'color':'green','char':'A'},
                    'interfaces':[
                        {'port':1,'name':'eth0'},
                        {'port':2,'name':'eth1','metadata':{'color':'blue'}}
                    ]
                },
                {
                    'dpid':'00:00:00:00:00:00:00:03',
                    'metadata':{'color':'blue','char':'A'},
                    'interfaces':[
                        {'port':1,'name':'eth0','metadata':{'color':'pink'}}
                    ]
                },
                {
                    'dpid':'00:00:00:00:00:00:00:03',
                    'metadata':{'color':'blue','char':'A'},
                    'interfaces':[
                        {'port':1,'name':'eth0','metadata':{'color':'green'}}
                    ]
                }
            ],
            'links':
            [
                {
                    'id': '00:00:00:00:00:00:00:01:1:00:00:00:00:00:00:00:02:2',
                    'metadata': {'color': 'purple'}
                }
            ]
        }
        url = f'{self.server_name_url}/v3/metadata'
        response = api.post(url, data = {'file': (BytesIO(json.dumps(topology_update).encode()), 'file.json')})
        self.assertEqual(response.status_code, 201, response.data)
        for switch_update in topology_update['switches']:
            mock_entity = mock_switches.get(switch_update['dpid'], None)
            if mock_entity is None:
                continue
            new_metadata = switch_update.get('metadata', None)
            if new_metadata is not None:
                mock_entity.extend_metadata.assert_any_call(new_metadata)
                mock_metadata_changes.assert_any_call(mock_entity, 'added')
            for interface in switch_update['interfaces']:
                mock_entity = mock_switches.get(switch_update['dpid'], None)
                if mock_entity is None:
                    continue
                new_metadata = switch_update.get('metadata', None)
                if new_metadata is not None:
                    mock_entity.extend_metadata.assert_any_call(new_metadata)
                    mock_metadata_changes.assert_any_call(mock_entity, 'added')
        for link_update in topology_update['links']:
            mock_entity = mock_links.get(link_update['id'], None)
            if mock_entity is None:
                continue
            new_metadata = link_update.get('metadata', None)
            if new_metadata is not None:
                mock_entity.extend_metadata.assert_any_call(new_metadata)
                mock_metadata_changes.assert_any_call(mock_entity, 'added')

        # Invalid json data type
        url = f'{self.server_name_url}/v3/metadata'
        response = api.post(url, data = {'file': (BytesIO(json.dumps("Hello!").encode()), 'file.json')})
        self.assertEqual(response.status_code, 400, response.data)

        # Not a json file
        url = f'{self.server_name_url}/v3/metadata'
        response = api.post(url, data = {'file': (BytesIO("Hello!".encode()), 'file.json')})
        self.assertEqual(response.status_code, 400, response.data)

        # Empty field
        url = f'{self.server_name_url}/v3/metadata'
        response = api.post(url)
        self.assertEqual(response.status_code, 400, response.data)

        # Empty field
        url = f'{self.server_name_url}/v3/metadata'
        response = api.post(url, data = {'file': (BytesIO("Hello!".encode()), '')})
        self.assertEqual(response.status_code, 400, response.data)

    def test_get_switch_metadata(self):
        """Test get_switch_metadata."""
        dpid = "00:00:00:00:00:00:00:01"
        mock_switch = get_switch_mock(dpid)
        mock_switch.metadata = "A"
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        url = f'{self.server_name_url}/v3/switches/{dpid}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 200, response.data)

        # fail case
        dpid = "00:00:00:00:00:00:00:02"
        url = f'{self.server_name_url}/v3/switches/{dpid}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.notify_metadata_changes')
    def test_add_switch_metadata(self, mock_metadata_changes):
        """Test add_switch_metadata."""
        dpid = "00:00:00:00:00:00:00:01"
        mock_switch = get_switch_mock(dpid)
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)
        payload = {"data": "A"}

        url = f'{self.server_name_url}/v3/switches/{dpid}/metadata'
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 201, response.data)
        mock_metadata_changes.assert_called()

        # fail case
        dpid = "00:00:00:00:00:00:00:02"
        url = f'{self.server_name_url}/v3/switches/{dpid}/metadata'
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.notify_metadata_changes')
    def test_delete_switch_metadata(self, mock_metadata_changes):
        """Test delete_switch_metadata."""
        dpid = "00:00:00:00:00:00:00:01"
        mock_switch = get_switch_mock(dpid)
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        key = "A"
        url = f'{self.server_name_url}/v3/switches/{dpid}/metadata/{key}'
        response = api.delete(url)
        mock_metadata_changes.assert_called()
        self.assertEqual(response.status_code, 200, response.data)

        # fail case
        key = "A"
        dpid = "00:00:00:00:00:00:00:02"
        url = f'{self.server_name_url}/v3/switches/{dpid}/metadata/{key}'
        response = api.delete(url)
        mock_metadata_changes.assert_called()
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.save_status_on_storehouse')
    def test_enable_interfaces(self, mock_save_status):
        """Test enable_interfaces."""
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_interface_1 = get_interface_mock('s1-eth1', 1, mock_switch)
        mock_interface_2 = get_interface_mock('s1-eth2', 2, mock_switch)
        mock_switch.interfaces = {1: mock_interface_1, 2: mock_interface_2}
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        interface_id = '00:00:00:00:00:00:00:01:1'
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mock_interface_1.enable.call_count, 1)
        self.assertEqual(mock_interface_2.enable.call_count, 0)
        mock_save_status.assert_called()

        mock_interface_1.enable.call_count = 0
        mock_interface_2.enable.call_count = 0
        url = f'{self.server_name_url}/v3/interfaces/switch/{dpid}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mock_interface_1.enable.call_count, 1)
        self.assertEqual(mock_interface_2.enable.call_count, 1)

        # test interface not found
        interface_id = '00:00:00:00:00:00:00:01:3'
        mock_interface_1.enable.call_count = 0
        mock_interface_2.enable.call_count = 0
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(mock_interface_1.enable.call_count, 0)
        self.assertEqual(mock_interface_2.enable.call_count, 0)

        # test switch not found
        dpid = '00:00:00:00:00:00:00:02'
        url = f'{self.server_name_url}/v3/interfaces/switch/{dpid}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(mock_interface_1.enable.call_count, 0)
        self.assertEqual(mock_interface_2.enable.call_count, 0)

    @patch('napps.kytos.topology.main.Main.save_status_on_storehouse')
    def test_disable_interfaces(self, mock_save_status):
        """Test disable_interfaces."""
        interface_id = '00:00:00:00:00:00:00:01:1'
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_interface_1 = get_interface_mock('s1-eth1', 1, mock_switch)
        mock_interface_2 = get_interface_mock('s1-eth2', 2, mock_switch)
        mock_switch.interfaces = {1: mock_interface_1, 2: mock_interface_2}
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mock_interface_1.disable.call_count, 1)
        self.assertEqual(mock_interface_2.disable.call_count, 0)
        mock_save_status.assert_called()

        mock_interface_1.disable.call_count = 0
        mock_interface_2.disable.call_count = 0
        url = f'{self.server_name_url}/v3/interfaces/switch/{dpid}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(mock_interface_1.disable.call_count, 1)
        self.assertEqual(mock_interface_2.disable.call_count, 1)

        # test interface not found
        interface_id = '00:00:00:00:00:00:00:01:3'
        mock_interface_1.disable.call_count = 0
        mock_interface_2.disable.call_count = 0
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 409, response.data)
        self.assertEqual(mock_interface_1.disable.call_count, 0)
        self.assertEqual(mock_interface_2.disable.call_count, 0)

        # test switch not found
        dpid = '00:00:00:00:00:00:00:02'
        url = f'{self.server_name_url}/v3/interfaces/switch/{dpid}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(mock_interface_1.disable.call_count, 0)
        self.assertEqual(mock_interface_2.disable.call_count, 0)

    def test_get_interface_metadata(self):
        """Test get_interface_metada."""
        interface_id = '00:00:00:00:00:00:00:01:1'
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_interface = get_interface_mock('s1-eth1', 1, mock_switch)
        mock_interface.metadata = {"metada": "A"}
        mock_switch.interfaces = {1: mock_interface}
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 200, response.data)

        # fail case switch not found
        interface_id = '00:00:00:00:00:00:00:02:1'
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 404, response.data)

        # fail case interface not found
        interface_id = '00:00:00:00:00:00:00:01:2'
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.notify_metadata_changes')
    def test_add_interface_metadata(self, mock_metadata_changes):
        """Test add_interface_metadata."""
        interface_id = '00:00:00:00:00:00:00:01:1'
        dpid = '00:00:00:00:00:00:00:01'
        mock_switch = get_switch_mock(dpid)
        mock_interface = get_interface_mock('s1-eth1', 1, mock_switch)
        mock_interface.metadata = {"metada": "A"}
        mock_switch.interfaces = {1: mock_interface}
        self.napp.controller.switches = {dpid: mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/metadata'
        payload = {"metada": "A"}
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 201, response.data)
        mock_metadata_changes.assert_called()

        # fail case switch not found
        interface_id = '00:00:00:00:00:00:00:02:1'
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/metadata'
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 404, response.data)

        # fail case interface not found
        interface_id = '00:00:00:00:00:00:00:01:2'
        url = f'{self.server_name_url}/v3/interfaces/{interface_id}/metadata'
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 404, response.data)

    def test_delete_interface_metadata(self):
        """Test delete_interface_metadata."""
        interface_id = '00:00:00:00:00:00:00:01:1'
        dpid = '00:00:00:00:00:00:00:01'
        iface_url = '/v3/interfaces/'
        mock_switch = get_switch_mock(dpid)
        mock_interface = get_interface_mock('s1-eth1', 1, mock_switch)
        mock_interface.remove_metadata.side_effect = [True, False]
        mock_interface.metadata = {"metada": "A"}
        mock_switch.interfaces = {1: mock_interface}
        self.napp.controller.switches = {'00:00:00:00:00:00:00:01':
                                         mock_switch}
        api = get_test_client(self.napp.controller, self.napp)

        key = 'A'
        url = f'{self.server_name_url}{iface_url}{interface_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 200, response.data)

        # fail case switch not found
        key = 'A'
        interface_id = '00:00:00:00:00:00:00:02:1'
        url = f'{self.server_name_url}{iface_url}{interface_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 404, response.data)

        # fail case interface not found
        key = 'A'
        interface_id = '00:00:00:00:00:00:00:01:2'
        url = f'{self.server_name_url}{iface_url}{interface_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 404, response.data)

        # fail case metadata not found
        key = 'A'
        interface_id = '00:00:00:00:00:00:00:01:1'
        url = f'{self.server_name_url}{iface_url}{interface_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 404, response.data)

    def test_enable_link(self):
        """Test enable_link."""
        mock_link = MagicMock(Link)
        self.napp.links = {'1': mock_link}
        api = get_test_client(self.napp.controller, self.napp)

        link_id = 1
        url = f'{self.server_name_url}/v3/links/{link_id}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(mock_link.enable.call_count, 1)

        # fail case
        link_id = 2
        url = f'{self.server_name_url}/v3/links/{link_id}/enable'
        response = api.post(url)
        self.assertEqual(response.status_code, 404, response.data)

    def test_disable_link(self):
        """Test disable_link."""
        mock_link = MagicMock(Link)
        self.napp.links = {'1': mock_link}
        api = get_test_client(self.napp.controller, self.napp)

        link_id = 1
        url = f'{self.server_name_url}/v3/links/{link_id}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(mock_link.disable.call_count, 1)

        # fail case
        link_id = 2
        url = f'{self.server_name_url}/v3/links/{link_id}/disable'
        response = api.post(url)
        self.assertEqual(response.status_code, 404, response.data)

    def test_get_link_metadata(self):
        """Test get_link_metadata."""
        mock_link = MagicMock(Link)
        mock_link.metadata = "A"
        self.napp.links = {'1': mock_link}
        msg_success = {"metadata": "A"}
        api = get_test_client(self.napp.controller, self.napp)

        link_id = 1
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(msg_success, json.loads(response.data))

        # fail case
        link_id = 2
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata'
        response = api.get(url)
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.notify_metadata_changes')
    def test_add_link_metadata(self, mock_metadata_changes):
        """Test add_link_metadata."""
        mock_link = MagicMock(Link)
        mock_link.metadata = "A"
        self.napp.links = {'1': mock_link}
        payload = {"metadata": "A"}
        api = get_test_client(self.napp.controller, self.napp)

        link_id = 1
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata'
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 201, response.data)
        mock_metadata_changes.assert_called()

        # fail case
        link_id = 2
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata'
        response = api.post(url, data=json.dumps(payload),
                            content_type='application/json')
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.notify_metadata_changes')
    def test_delete_link_metadata(self, mock_metadata_changes):
        """Test delete_link_metadata."""
        mock_link = MagicMock(Link)
        mock_link.metadata = "A"
        mock_link.remove_metadata.side_effect = [True, False]
        self.napp.links = {'1': mock_link}
        api = get_test_client(self.napp.controller, self.napp)

        link_id = 1
        key = 'A'
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 200, response.data)
        mock_metadata_changes.assert_called()

        # fail case link not found
        link_id = 2
        key = 'A'
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 404, response.data)

        # fail case metadata not found
        link_id = 1
        key = 'A'
        url = f'{self.server_name_url}/v3/links/{link_id}/metadata/{key}'
        response = api.delete(url)
        self.assertEqual(response.status_code, 404, response.data)

    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    @patch('napps.kytos.topology.main.Main.update_instance_metadata')
    def test_handle_new_switch(self, *args):
        """Test handle_new_switch."""
        (mock_instance_metadata, mock_notify_topology_update) = args
        mock_event = MagicMock()
        mock_switch = create_autospec(Switch)
        mock_event.content['switch'] = mock_switch
        self.napp.handle_new_switch(mock_event)
        mock_notify_topology_update.assert_called()
        mock_instance_metadata.assert_called()

    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    def test_handle_connection_lost(self, mock_notify_topology_update):
        """Test handle connection_lost."""
        mock_event = MagicMock()
        mock_switch = create_autospec(Switch)
        mock_switch.return_value = True
        mock_event.content['source'] = mock_switch
        self.napp.handle_connection_lost(mock_event)
        mock_notify_topology_update.assert_called()

    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    @patch('napps.kytos.topology.main.Main.update_instance_metadata')
    def test_handle_interface_up(self, *args):
        """Test handle_interface_up."""
        (mock_instance_metadata, mock_notify_topology_update) = args
        mock_event = MagicMock()
        mock_interface = create_autospec(Interface)
        mock_event.content['interface'] = mock_interface
        self.napp.handle_interface_up(mock_event)
        mock_notify_topology_update.assert_called()
        mock_instance_metadata.assert_called()

    @patch('napps.kytos.topology.main.Main.handle_interface_up')
    def test_handle_interface_created(self, mock_handle_interface_up):
        """Test handle interface created."""
        mock_event = MagicMock()
        self.napp.handle_interface_created(mock_event)
        mock_handle_interface_up.assert_called()

    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    @patch('napps.kytos.topology.main.Main.handle_interface_link_down')
    def test_handle_interface_down(self, *args):
        """Test handle interface down."""
        (mock_handle_interface_link_down, mock_notify_topology_update) = args
        mock_event = MagicMock()
        mock_interface = create_autospec(Interface)
        mock_event.content['interface'] = mock_interface
        self.napp.handle_interface_down(mock_event)
        mock_handle_interface_link_down.assert_called()
        mock_notify_topology_update.assert_called()

    @patch('napps.kytos.topology.main.Main.handle_interface_down')
    def test_interface_deleted(self, mock_handle_interface_link_down):
        """Test interface deleted."""
        mock_event = MagicMock()
        self.napp.handle_interface_deleted(mock_event)
        mock_handle_interface_link_down.assert_called()

    @patch('napps.kytos.topology.main.Main._get_link_from_interface')
    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    @patch('napps.kytos.topology.main.Main.update_instance_metadata')
    @patch('napps.kytos.topology.main.Main.notify_link_status_change')
    def test_interface_link_up(self, *args):
        """Test interface link_up."""
        (mock_status_change, mock_instance_metadata, mock_topology_update,
         mock_link_from_interface) = args

        now = time.time()
        mock_event = MagicMock()
        mock_interface_a = create_autospec(Interface)
        mock_interface_a.is_active.return_value = False
        mock_interface_b = create_autospec(Interface)
        mock_interface_b.is_active.return_value = True
        mock_link = create_autospec(Link)
        mock_link.get_metadata.return_value = now
        mock_link.is_active.side_effect = [False, True]
        mock_link.endpoint_a = mock_interface_a
        mock_link.endpoint_b = mock_interface_b
        mock_link_from_interface.return_value = mock_link
        content = {'interface': mock_interface_a}
        mock_event.content = content
        self.napp.link_up_timer = 1
        self.napp.handle_interface_link_up(mock_event)
        mock_topology_update.assert_called()
        mock_instance_metadata.assert_called()
        mock_status_change.assert_called()

    @patch('napps.kytos.topology.main.Main._get_link_from_interface')
    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    @patch('napps.kytos.topology.main.Main.notify_link_status_change')
    def test_interface_link_down(self, *args):
        """Test interface link down."""
        (mock_status_change, mock_topology_update,
         mock_link_from_interface) = args

        mock_event = MagicMock()
        mock_interface = create_autospec(Interface)
        mock_link = create_autospec(Link)
        mock_link.is_active.return_value = True
        mock_link_from_interface.return_value = mock_link
        mock_event.content['interface'] = mock_interface
        self.napp.handle_interface_link_down(mock_event)
        mock_topology_update.assert_called()
        mock_status_change.assert_called()

    @patch('napps.kytos.topology.main.Main._get_link_or_create')
    @patch('napps.kytos.topology.main.Main.notify_topology_update')
    def test_add_links(self, *args):
        """Test add_links."""
        (mock_notify_topology_update, mock_get_link_or_create) = args
        mock_event = MagicMock()
        self.napp.add_links(mock_event)
        mock_get_link_or_create.assert_called()
        mock_notify_topology_update.assert_called()

    @patch('napps.kytos.topology.main.Main._get_switches_dict')
    @patch('napps.kytos.topology.main.StoreHouse.save_status')
    def test_save_status_on_store(self, *args):
        """Test save_status_on_storehouse."""
        (mock_save_status, mock_get_switches_dict) = args
        self.napp.save_status_on_storehouse()
        mock_get_switches_dict.assert_called()
        mock_save_status.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_notify_topology_update(self, *args):
        """Test notify_topology_update."""
        (mock_buffers_put, mock_event) = args
        self.napp.notify_topology_update()
        mock_event.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_notify_link_status_change(self, *args):
        """Test notify link status change."""
        (mock_buffers_put, mock_event) = args
        mock_link = create_autospec(Link)
        self.napp.notify_link_status_change(mock_link)
        mock_event.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    @patch('napps.kytos.topology.main.isinstance')
    def test_notify_metadata_changes(self, *args):
        """Test notify metadata changes."""
        (mock_isinstance, mock_buffers_put, mock_event) = args
        mock_isinstance.return_value = True
        mock_obj = MagicMock()
        mock_action = create_autospec(Switch)
        self.napp.notify_metadata_changes(mock_obj, mock_action)
        mock_event.assert_called()
        mock_isinstance.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_notify_port_created(self, *args):
        """Test notify port created."""
        (mock_buffers_put, mock_kytos_event) = args
        mock_event = MagicMock()
        self.napp.notify_port_created(mock_event)
        mock_kytos_event.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_save_metadata_on_store(self, *args):
        """Test test_save_metadata_on_store."""
        (mock_buffers_put, mock_kytos_event) = args
        mock_event = MagicMock()
        mock_switch = MagicMock()
        mock_interface = MagicMock()
        mock_link = MagicMock()
        self.napp.store_items = {'switches': mock_switch,
                                 'interfaces': mock_interface,
                                 'links': mock_link}
        # test switches
        mock_event.content = {'switch': mock_switch}
        self.napp.save_metadata_on_store(mock_event)
        mock_kytos_event.assert_called()
        mock_buffers_put.assert_called()

        # test interfaces
        mock_event.content = {'interface': mock_interface}
        self.napp.save_metadata_on_store(mock_event)
        mock_kytos_event.assert_called()
        mock_buffers_put.assert_called()

        # test link
        mock_event.content = {'link': mock_link}
        self.napp.save_metadata_on_store(mock_event)
        mock_kytos_event.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_verify_storehouse(self, *args):
        """Test verify_storehouse."""
        (mock_buffers_put, mock_kytos_event) = args
        mock_entities = MagicMock()
        self.napp.verify_storehouse(mock_entities)
        mock_buffers_put.assert_called()
        mock_kytos_event.assert_called()

    @patch('napps.kytos.topology.main.KytosEvent')
    @patch('kytos.core.buffers.KytosEventBuffer.put')
    def test_request_retrieve_entities(self, *args):
        """Test retrive_entities."""
        (mock_buffers_put, mock_kytos_event) = args
        mock_event = MagicMock()
        mock_data = MagicMock()
        mock_error = MagicMock()
        mock_event.content = {"namespace": "test_box"}
        self.napp.request_retrieve_entities(mock_event, mock_data, mock_error)
        mock_kytos_event.assert_called()
        mock_buffers_put.assert_called()

        self.napp.request_retrieve_entities(mock_event, None, mock_error)
        mock_kytos_event.assert_called()
        mock_buffers_put.assert_called()

    @patch('napps.kytos.topology.main.Main.notify_link_status_change')
    def test_handle_link_maintenance_start(self, status_change_mock):
        """Test handle_link_maintenance_start."""
        link1 = MagicMock()
        link1.id = 2
        link2 = MagicMock()
        link2.id = 3
        link3 = MagicMock()
        link3.id = 4
        content = {'links': [link1, link2]}
        event = MagicMock()
        event.content = content
        self.napp.links = {2: link1, 4: link3}
        self.napp.handle_link_maintenance_start(event)
        status_change_mock.assert_called_once_with(link1)

    @patch('napps.kytos.topology.main.Main.notify_link_status_change')
    def test_handle_link_maintenance_end(self, status_change_mock):
        """Test handle_link_maintenance_end."""
        link1 = MagicMock()
        link1.id = 2
        link2 = MagicMock()
        link2.id = 3
        link3 = MagicMock()
        link3.id = 4
        content = {'links': [link1, link2]}
        event = MagicMock()
        event.content = content
        self.napp.links = {2: link1, 4: link3}
        self.napp.handle_link_maintenance_end(event)
        status_change_mock.assert_called_once_with(link1)

    @patch('napps.kytos.topology.main.Main.handle_link_down')
    def test_handle_switch_maintenance_start(self, handle_link_down_mock):
        """Test handle_switch_maintenance_start."""
        switch1 = MagicMock()
        interface1 = MagicMock()
        interface1.is_active.return_value = True
        interface2 = MagicMock()
        interface2.is_active.return_value = False
        interface3 = MagicMock()
        interface3.is_active.return_value = True
        switch1.interfaces = {1: interface1, 2: interface2, 3: interface3}
        switch2 = MagicMock()
        interface4 = MagicMock()
        interface4.is_active.return_value = False
        interface5 = MagicMock()
        interface5.is_active.return_value = True
        switch2.interfaces = {1: interface4, 2: interface5}
        content = {'switches': [switch1, switch2]}
        event = MagicMock()
        event.content = content
        self.napp.handle_switch_maintenance_start(event)
        self.assertEqual(handle_link_down_mock.call_count, 3)

    @patch('napps.kytos.topology.main.Main.handle_link_up')
    def test_handle_switch_maintenance_end(self, handle_link_up_mock):
        """Test handle_switch_maintenance_end."""
        switch1 = MagicMock()
        interface1 = MagicMock()
        interface1.is_active.return_value = True
        interface2 = MagicMock()
        interface2.is_active.return_value = False
        interface3 = MagicMock()
        interface3.is_active.return_value = True
        switch1.interfaces = {1: interface1, 2: interface2, 3: interface3}
        switch2 = MagicMock()
        interface4 = MagicMock()
        interface4.is_active.return_value = False
        interface5 = MagicMock()
        interface5.is_active.return_value = True
        switch2.interfaces = {1: interface4, 2: interface5}
        content = {'switches': [switch1, switch2]}
        event = MagicMock()
        event.content = content
        self.napp.handle_switch_maintenance_end(event)
        self.assertEqual(handle_link_up_mock.call_count, 5)
