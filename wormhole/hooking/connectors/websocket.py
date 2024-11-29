from .base import BaseConnector


class Websocket(BaseConnector):

    def __init__(self, ws):
        super(Websocket, self).__init__()
        self.ws = ws
        self.count = 0

    def forward(self, message, *args, **kwargs):
        """
        final_message = ";~".join(list(metadata))
        final_message += f";~{message}"
        for _, v in content_metadata.items():
            final_message += f";~{v}"
        """
        message_dict = {"message": str(message)}
        message_dict.update(kwargs)
        #del message_dict['function']
        self.ws.emit("message", {"data": message_dict})
        self.count = self.count + 1
        print("WS:", self.count)
