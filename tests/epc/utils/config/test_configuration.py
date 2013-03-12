import unittest

from epc.utils.config import Configuration


class TestConfiguration(unittest.TestCase):
    
    def setUp(self):
        self.cfg = Configuration({
            "rrm": {
                "t3212": 64,
                "csEnabled": True,
                "psEnabled": False
            },
            "son": {
                "enabled": True,
                "utrafdd": {
                    "enabled": True,
                    "scanOnBoot": True,
                    "freqs": [10787, 9137],
                },
                "gsm": {
                    "enabled": True,
                    "scanOnBoot": True,
                    "freqs": [514, 516]
                }
            },
            "oam": {
                "cliEnabled": True,
                "username": "fap123",
                "password": "fap123"
            }
        })

    def test_setValue(self):
        self.cfg.setValue(("oam", "cliEnabled"), False)
        self.assertFalse(self.cfg.content["oam"]["cliEnabled"])

    def test_setValueWithDotFormat(self):
        self.cfg.setValue("oam.cliEnabled", False)
        self.assertFalse(self.cfg.content["oam"]["cliEnabled"])

    def test_getValue(self):
        self.assertEqual(self.cfg.getValue(("oam", "username")), "fap123")

    def test_getValueWithDotFormat(self):
        self.assertEqual(self.cfg.getValue("oam.username"), "fap123")
    
    def test_listenerCalledOnValueChanged(self):
        def onValueChanged(path, value):
            self.result = (path, value)
        self.cfg.addListener("oam", onValueChanged)
        self.cfg.setValue("oam.cliEnabled", False)
        self.assertListEqual(self.result[0], list(("oam", "cliEnabled")))
        self.assertEqual(self.result[1], False)

    def test_listenerNotCalledOnValueChanged(self):
        self.listenerCalled = False
        def onValueChanged(path, value):
            self.listenerCalled = True
        self.cfg.addListener("oam.cliEnabled", onValueChanged)
        self.cfg.setValue("rrm.t3212", 10)
        self.assertFalse(self.listenerCalled)