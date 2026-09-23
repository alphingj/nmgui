import unittest

from nmgui.app import App
from nmgui.nmcli import Nmcli, _split_t_fields


class NmcliTests(unittest.TestCase):
    def test_split_t_fields_unescapes_colons_and_backslashes(self):
        self.assertEqual(_split_t_fields(r"Cafe\:WiFi:yes", 2), ["Cafe:WiFi", "yes"])
        self.assertEqual(_split_t_fields(r"path\\name:value", 2), [r"path\name", "value"])


    def test_split_t_fields_rejects_wrong_field_count(self):
        with self.assertRaises(ValueError):
            _split_t_fields("one:two", 3)


    def test_privileged_command_matching_uses_complete_prefix(self):
        nmcli = Nmcli()
        self.assertTrue(nmcli._needs_privileges(["device", "wifi", "connect", "Cafe WiFi"]))
        self.assertTrue(nmcli._needs_privileges(["radio", "wifi", "off"]))
        self.assertFalse(nmcli._needs_privileges(["device", "status"]))


    def test_display_command_redacts_password_values(self):
        command = ["nmcli", "device", "wifi", "connect", "Cafe", "password", "secret"]
        rendered = App._display_command(command)
        self.assertTrue(rendered.endswith("password <redacted>"))
        self.assertNotIn("secret", rendered)
