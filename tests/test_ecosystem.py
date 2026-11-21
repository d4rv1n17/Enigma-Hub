import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, Mock
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener

from hub_ecosystem import LaunchBroker, running_product


class BrokerTests(unittest.TestCase):
    def setUp(self):
        self.broker = LaunchBroker()

    def tearDown(self):
        self.broker.close()

    def claim_http(self, ticket, product):
        request = Request(self.broker.endpoint, data=json.dumps(dict(ticket=ticket, product=product)).encode(), method='POST')
        with build_opener(ProxyHandler({})).open(request, timeout=3) as response:
            return response.status

    def test_ticket_is_product_bound_and_consumed_once(self):
        ticket = self.broker.issue('cube')
        with self.assertRaises(HTTPError):
            self.claim_http(ticket, 'disk')
        self.assertEqual(self.claim_http(ticket, 'cube'), 200)
        with self.assertRaises(HTTPError):
            self.claim_http(ticket, 'cube')

    def test_expired_and_forged_tickets_are_rejected(self):
        ticket = self.broker.issue('disk')
        self.broker._tickets[ticket] = ('disk', time.monotonic() - 1)
        self.assertFalse(self.broker.claim(ticket, 'disk'))
        self.assertFalse(self.broker.claim('forged', 'disk'))
        self.assertFalse(self.broker.claim({}, 'disk'))

    def test_no_launch_command_is_exposed_over_http(self):
        request = Request(self.broker.endpoint.replace('/claim', '/launch'), data=b'{}', method='POST')
        with self.assertRaises(HTTPError):
            build_opener(ProxyHandler({})).open(request, timeout=3)

    def test_cube_client_claims_real_ticket_and_scrubs_environment(self):
        path = Path(__file__).resolve().parents[2] / 'EnigmaCube/Enigma-Cube/enigma_timer/hub_link.py'
        if not path.is_file():
            self.skipTest('Sibling Cube repository is not present')
        spec = importlib.util.spec_from_file_location('cube_hub_link', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        environment = self.broker.environment('cube')
        with patch.dict(os.environ, environment, clear=True):
            self.assertTrue(module.claim_launch())
            self.assertNotIn('ENIGMA_HUB_TICKET', os.environ)
            self.assertNotIn('ENIGMA_HUB_ENDPOINT', os.environ)
            self.assertFalse(module.claim_launch())

    def test_cube_rejects_remote_ticket_endpoints_without_network(self):
        path = Path(__file__).resolve().parents[2] / 'EnigmaCube/Enigma-Cube/enigma_timer/hub_link.py'
        if not path.is_file():
            self.skipTest('Sibling Cube repository is not present')
        spec = importlib.util.spec_from_file_location('cube_hub_link', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for endpoint in ('https://example.com/claim', 'http://127.0.0.1:80/claim?secret=1', 'http://user@127.0.0.1/claim'):
            with patch.dict(os.environ, ENIGMA_HUB_ENDPOINT=endpoint, ENIGMA_HUB_TICKET='secret'), patch.object(module, 'build_opener') as opener:
                self.assertFalse(module.claim_launch())
                opener.assert_not_called()

    @unittest.skipUnless(sys.platform == 'win32', 'Windows process enumeration')
    def test_process_check_matches_exact_path(self):
        self.assertTrue(running_product(sys.executable))
        self.assertFalse(running_product(Path(tempfile.gettempdir()) / 'not-an-enigma-exe.exe'))


class HubRoutingTests(unittest.TestCase):
    def setUp(self):
        import enigma_hub as hub
        from test_experience import APP
        self.hub, self.app = hub, APP
        self.temp = tempfile.TemporaryDirectory()
        self.patches = [patch.object(hub, 'APPDATA', Path(self.temp.name)),
                        patch.object(hub, 'STATE_FILE', Path(self.temp.name) / 'settings.json'),
                        patch.object(hub.Hub, 'load_news'), patch.object(hub.Hub, 'check_updates'),
                        patch.object(hub.Hub, 'check_hub_update')]
        for item in self.patches:
            item.start()
        self.window = hub.Hub()

    def tearDown(self):
        self.window.ecosystem_quit = True
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_custom_product_path_is_adopted_and_routed(self):
        executable = Path(self.temp.name) / 'EnigmaDisk.exe'
        executable.write_bytes(b'test')
        with patch.object(self.window, 'launch_product') as launch:
            self.window.ecosystem_request(dict(product='disk', action='launch', exe=str(executable)))
            launch.assert_called_once_with(self.hub.PRODUCTS[1])
        self.assertEqual(self.window.state['paths']['disk'], self.temp.name)

    def test_wrong_executable_never_launches(self):
        executable = Path(self.temp.name) / 'other.exe'
        executable.write_bytes(b'test')
        with patch.object(self.window, 'launch_product') as launch:
            self.window.ecosystem_request(dict(product='disk', action='launch', exe=str(executable)))
            launch.assert_not_called()

    def test_running_product_cannot_be_updated_or_removed(self):
        with patch.object(self.hub, 'running_product', return_value=True), patch.object(self.window, 'notify') as notify, patch.object(self.hub, 'ProductWorker') as worker:
            for action in ('install', 'update', 'remove'):
                self.window.start_task(self.hub.PRODUCTS[1], action)
            self.assertEqual(notify.call_count, 3)
            worker.assert_not_called()

    def test_quit_does_not_terminate_running_products(self):
        process = Mock()
        process.poll.return_value = None
        self.window.ecosystem_processes = [process]
        self.window.quit_ecosystem()
        process.kill.assert_not_called()
        process.terminate.assert_not_called()

    def test_tray_actions_launch_correct_products_and_can_be_shown_again(self):
        with patch.object(self.window, 'launch_product') as launch:
            self.window.ensure_ecosystem_tray()
            actions = self.window.ecosystem_tray.contextMenu().actions()
            actions[1].trigger()
            launch.assert_called_once_with(self.hub.PRODUCTS[0])
            self.window.ecosystem_tray.hide()
            self.window.ensure_ecosystem_tray()
            self.assertTrue(self.window.ecosystem_tray.isVisible())
            self.window.ecosystem_tray.hide()
