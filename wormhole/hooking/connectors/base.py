class BaseConnector:

    def __init__(self):
        pass

    def forward(self, message, *metadata, **content_metadata):
        raise NotImplementedError()
