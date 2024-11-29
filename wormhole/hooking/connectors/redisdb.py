from redis import Redis

from .base import BaseConnector


class Redisdb(BaseConnector):

    def __init__(self):
        super(Redisdb, self).__init__()
        self.redis = Redis(host="127.0.0.1",
                           port=6379,
                           db=0,
                           decode_responses=True)

    def forward(self, message, *metadata, **content_metadata):
        final_message = ";~".join(list(metadata))
        final_message += f";~{message}"
        for _, v in content_metadata.items():
            final_message += f";~{v}"
        self.redis.publish("prova", final_message)
