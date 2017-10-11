import os
import json
import time
import threading

import pytest
from wampy.peers import Client

from tuxeatpi_common.cli import main_cli, set_daemon_class
from tuxeatpi_speech_nuance.daemon import Speech
from tuxeatpi_common.message import Message


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

        def get_message(message, meta):
            payload = json.loads(message)
            self.message = payload.get("data", {}).get("arguments", {})
            if meta['topic'] == "hotword.disable":
                self.disable = True
            elif meta['topic'] == "hotword.enable":
                self.enable = True
            self.message_topic = meta['topic']

        def hotword_disable():
            self.message = {}
            self.disable = True

        def hotword_enable():
            self.message = {}
            self.enable = True

        self.wamp_client = Client(realm="tuxeatpi")
        self.wamp_client.start()

        self.wamp_client.session._register_procedure("hotword.disable")
        setattr(self.wamp_client, "hotword.disable", hotword_disable)
        self.wamp_client.session._register_procedure("hotword.enable")
        setattr(self.wamp_client, "hotword.enable", hotword_enable)

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

        assert "speech_test.say" in dir(self.speech_daemon._wamp_client)


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
