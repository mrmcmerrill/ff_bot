import requests
import json
import logging

logger = logging.getLogger(__name__)

class GroupMeException(Exception):
    pass

class GroupMeBot(object):
    """Posts messages to a GroupMe group via a bot id."""

    def __init__(self, bot_id):
        self.bot_id = bot_id

    def __repr__(self):
        return "GroupMeBot(%s)" % self.bot_id

    def send_message(self, text):
        """Post text to the GroupMe group; no-op if no real bot id is configured."""
        template = {
            "bot_id": self.bot_id,
            "text": text, #limit 1000 chars
            "attachments": []
        }

        headers = {'content-type': 'application/json'}

        if self.bot_id not in (1, "1", ''):
            r = requests.post("https://api.groupme.com/v3/bots/post",
                              data=json.dumps(template), headers=headers)
            if r.status_code != 202:
                logger.error(r.content)
                raise GroupMeException(r.content)

            return r
