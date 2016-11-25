# -*- coding: utf-8-*-

'''
Main class
'''

import os
import sys
import shutil
import logging
import yaml

from jessy import tts
from jessy import stt
from jessy import jasperpath
from jessy import diagnose
from jessy.conversation import Conversation
from jessy.lazyload import LazyLoad


class Jessy(object):
    '''
    Main class.
    '''
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._stt = LazyLoad().scan('jessy.stt')
        self._tts = LazyLoad().scan('jessy.tts')

    def get_stt_modules(self):
        '''
        Return available STT modules.
        '''
        return self._stt.modules()

    def get_tts_modules(self):
        '''
        Return available TTS modules.
        '''
        return self._tts.modules()

    def initialize(self, mic):
        # Create config dir if it does not exist yet
        if not os.path.exists(jasperpath.CONFIG_PATH):
            try:
                os.makedirs(jasperpath.CONFIG_PATH)
            except OSError:
                self._logger.error("Could not create config dir: '%s'", jasperpath.CONFIG_PATH, exc_info=True)
                raise

        # Check if config dir is writable
        if not os.access(jasperpath.CONFIG_PATH, os.W_OK):
            self._logger.critical("Config dir %s is not writable. Jessy won't work correctly.",
                                  jasperpath.CONFIG_PATH)

        old_configfile = os.path.join(jasperpath.LIB_PATH, 'profile.yml')
        new_configfile = jasperpath.config('profile.yml')
        if os.path.exists(old_configfile):
            if os.path.exists(new_configfile):
                self._logger.warning("Deprecated profile file found: '%s'. Please remove it.",
                                     old_configfile)
            else:
                self._logger.warning("Deprecated profile file found: '%s'. Trying to copy it to new location '%s'.",
                                     old_configfile, new_configfile)
                try:
                    shutil.copy2(old_configfile, new_configfile)
                except shutil.Error:
                    self._logger.error("Unable to copy config file. Please copy it manually.", exc_info=True)
                    raise

        # Read config
        self._logger.debug("Trying to read config file: '%s'", new_configfile)
        try:
            with open(new_configfile, "r") as f:
                self.config = yaml.safe_load(f)
        except Exception as ex:
            self._logger.error("Error reading configuration file: '{0}'".format(new_configfile))
            raise ex

        stt_engine_class = self._stt[self.config['stt_engine_ng']].initiator()
        if 'stt_passive_engine' in self.config:
            stt_passive_engine_class = self._stt[self.config['stt_passive_engine']].initiator()
        else:
            stt_passive_engine_class = stt_engine_class

        tts_engine_class = self._tts[self.config['tts_engine_ng']].initiator()

        # Initialize Mic
        self.mic = mic(tts_engine_class.get_instance(),
                       stt_passive_engine_class.get_passive_instance(),
                       stt_engine_class.get_active_instance())
        return self

    def run(self):
        if 'first_name' in self.config:
            salutation = "Hey, {0}. Glad to see you. How can I help you?".format(self.config["first_name"])
        else:
            salutation = "How can I help you?"
        self.mic.say(salutation)

        Conversation(self.config.get('persona', 'jasper').upper(),
                     self.mic, self.config).handleForever()
