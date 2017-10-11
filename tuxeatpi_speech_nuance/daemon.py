"""Module defining Speech component based on Nuance Communications Services"""
import asyncio
import logging
import time

from pynuance import tts

from tuxeatpi_common.message import Message
from tuxeatpi_common.wamp import is_wamp_topic, is_wamp_rpc
from tuxeatpi_common.error import TuxEatPiError
from tuxeatpi_common.daemon import TepBaseDaemon


class Speech(TepBaseDaemon):
    """Speech Nuance Communications Services based component class

    This component waits for speech/say topic messageto read the text and say it
    """
    def __init__(self, name, workdir, intent_folder, dialog_folder, logging_level=logging.INFO):
        TepBaseDaemon.__init__(self, name, workdir, intent_folder, dialog_folder, logging_level)
        # get from settings
        self.app_id = None
        self.app_key = None
        self.codec = None
        self.voices = {}
        self.is_speaking = None
        # self.set_state(False)

    def main_loop(self):
        """Main loop.

        Do nothing
        """
        time.sleep(1)

    def set_config(self, config):
        """Save the configuration and reload the daemon"""
        # TODO improve this ? can be factorized ?
        for attr in ["app_id", "app_key", "codec", "voices"]:
            if attr not in config.keys():
                self.logger.error("Missing parameter {}".format(attr))
                return False
        # Set params
        self.app_id = config.get("app_id")
        self.app_key = config.get("app_key")
        self.codec = config.get("codec")
        if not config.get("voices", {}):
            # TODO improve this
            raise SpeechError("Bad language/voice combinaison")
        self.voices = config.get("voices")
        return True

    @property
    def voice(self):
        """Return current selected voice"""
        if hasattr(self, 'voices'):
            return self.voices.get(self.settings.language)

    def set_state(self, state):
        """State indicate if the Tux is currently speaking

        .. todo:: Set it as property
        """
        self.is_speaking = state
        topic = "global/is_speaking"
        data = {"arguments": {"state": state}}
        message = Message(topic=topic, data=data)
        self.logger.info("Publish %s with argument %s", message.topic, message.payload)
        self.publish(message)

    @is_wamp_rpc("say")
    @is_wamp_topic("say")
    def say(self, text):
        """Say a text using Nuance Communications Services"""
        self.logger.info("speech/say called with argument: text=%s", text)
        # Fix
        # RuntimeError: There is no current event loop in thread 'Thread-1'.
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        # Disabling hotword
        self.call("hotword.disable")
        # Set state
        self.set_state(True)
        # Say text
        tts.text_to_speech(self.app_id, self.app_key, self.settings.language,
                           self.voice, self.codec, text)
        # Set state
        self.set_state(False)
        # Enabling hotword
        self.call("hotword.enable")

    @is_wamp_rpc("test")
    @is_wamp_topic("test")
    def test(self):
        """Test this component sayng something"""
        self.logger.info("speech/test called")

    @is_wamp_rpc("help")
    @is_wamp_topic("help")
    def help_(self):
        pass


class SpeechError(TuxEatPiError):
    """Base class for hotword exceptions"""
    pass
