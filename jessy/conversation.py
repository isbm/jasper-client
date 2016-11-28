# -*- coding: utf-8-*-
import logging
from brain import Brain


class Conversation(object):
    '''
    Conversation loop class.
    '''

    def __init__(self, persona, mic, profile):
        self._logger = logging.getLogger(__name__)
        self.persona = persona
        self.mic = mic
        self.profile = profile
        self.brain = Brain(mic, profile)

    def handle_forever(self):
        """
        Delegates user input to the handling function when activated.
        """
        self._logger.info("Starting to handle conversation with keyword '%s'.",
                          self.persona)
        while True:
            self._logger.debug("Started listening for keyword '%s'", self.persona)
            threshold, transcribed = self.mic.passive_listen(self.persona)
            self._logger.debug("Stopped listening for keyword '%s'", self.persona)

            if not transcribed or not threshold:
                self._logger.info("Nothing has been said or transcribed.")
                continue

            self._logger.info("Keyword '%s' has been said!", self.persona)
            self._logger.debug("Started to listen actively with threshold: %r", threshold)
            input = self.mic.active_listen_to_all_options(threshold)
            self._logger.debug("Stopped to listen actively with threshold: %r", threshold)

            if input:
                self.brain.query(input)
            else:
                self.mic.say("Pardon?")
