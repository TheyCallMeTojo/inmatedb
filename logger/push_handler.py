import logging
import time

from pushbullet import Pushbullet
from typing import NamedTuple

class PushCredentials(NamedTuple):
    api_key: str
    channel_tag: str

class PushHandler(logging.Handler):

    def __init__(self, credentials:PushCredentials):
        '''
        If you set up a pushbullet account, create a Channel, then you can get live notifications from the server.
        Here's how: https://blog.pushbullet.com/2014/09/30/introducing-pushbullet-channels/
        Get your access token here: https://www.pushbullet.com/#settings/account
        '''
        super(PushHandler, self).__init__()
        
        self.bullet = Pushbullet(credentials.api_key)
        self.channel = self.bullet.get_channel(credentials.channel_tag)

    def emit(self, record):
        title = f"{record.levelname}: an error occurred"
        message = self.format(record).strip()
        self.log(message, title)

    def log(self, message, title=None):
        title = "Server Message" if (title is None) else title
        push = self.bullet.push_note(title, message, channel=self.channel)
        return push

    def push_image(self, image_file, body=None, title=None, filename="*.png"):
        filedata = self.bullet.upload_file(image_file, filename)
        push = self.bullet.push_file(**filedata, body=body, title=title, channel=self.channel)
        return push

    def get_pushes(self):
        pushes = self.bullet.get_pushes()

        match_name = lambda p: p['sender_name'] == self.channel.name
        channel_pushes = list(filter(match_name, pushes))
        return channel_pushes

    def delete_everything(self):
        for push in self.get_pushes():
            push_id = push['iden']
            self.bullet.delete_push(push_id)

    def delete_pushes_older_than(self, max_age_in_seconds):
        for push in self.get_pushes():
            created_at = push['created']
            push_age = time.time() - created_at

            if push_age > max_age_in_seconds:
                push_id = push['iden']
                self.bullet.delete_push(push_id)
