import os
import json
import time
import threading

import pytest

from tuxeatpi_common.cli import main_cli, set_daemon_class
from tuxeatpi_speech_nuance.daemon import Speech
from tuxeatpi_common.message import Message, MqttClient
import paho.mqtt.client as paho


from click.testing import CliRunner

class TestDaemon(object):

    @classmethod
    def setup_class(self):
        workdir = "tests/workdir"
        intents = "intents"
        dialogs = "dialogs"
        self.speech_daemon = Speech('speech_test', workdir, intents, dialogs)
        self.speech_daemon.settings.language = "en_US"
        self.disable = False
        self.enable = False

        def get_message(mqttc, obj, msg):
            payload = json.loads(msg.payload.decode())
            self.message = payload.get("data", {}).get("arguments", {})
            if msg.topic == "hotword/disable":
                self.disable = True
            elif msg.topic == "hotword/enable":
                self.enable = True
            self.message_topic = msg.topic
        self.mqtt_client = paho.Client()
        self.mqtt_client.connect("127.0.0.1", 1883, 60)
        self.mqtt_client.on_message = get_message
        self.mqtt_client.subscribe("hotword/disable", 0)
        self.mqtt_client.subscribe("hotword/enable", 0)
        self.mqtt_client.loop_start()

    @classmethod
    def teardown_class(self):
        self.message = None
        self.speech_daemon.settings.delete("/config/global")
        self.speech_daemon.settings.delete("/config/speech_test")
        self.speech_daemon.settings.delete()
        self.speech_daemon.registry.clear()
        try:  # CircleCI specific
            self.speech_daemon.shutdown()
        except AttributeError:
            pass

    @pytest.mark.order1
    def test_time(self, capsys):
        t = threading.Thread(target=self.speech_daemon.start)
        t = t.start()

        time.sleep(1)
        global_config = {"language": "en_US",
                         "nlu_engine": "fake_nlu",
                         }
        self.speech_daemon.settings.save(global_config, "global")
        config = {"app_id": "FAKE_app_id",
                  "app_key": "FAKE_app_key",
                  "codec": "wav",
                  "voices": {"fr_FR": "Thomas",
                             "en_US": "Tom",
                             }}
        self.speech_daemon.settings.save(config)
        self.speech_daemon.set_config(config)
        time.sleep(2)
        assert self.speech_daemon.voices == {"fr_FR": "Thomas", 
                                             "en_US": "Tom",}

        voice = self.speech_daemon.voice
        assert voice == "Tom"
        time.sleep(1)

        # Mock tts
        from unittest.mock import MagicMock
        from pynuance import tts
        tts.text_to_speech = MagicMock()
        self.speech_daemon.say("Text sample")

        time.sleep(1)
        assert self.message == {}
        assert self.enable == True
        assert self.disable == True
