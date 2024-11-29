from .base import BaseConnector


class Stdout(BaseConnector):

    def __init__(self):
        super(Stdout, self).__init__()

    def forward(self, message, **kwargs):
        print(f"{kwargs.get('timestamp')} [{kwargs.get('tid')}] "
              f"{kwargs.get('module')}({kwargs.get('function')}): {message}\n" + "-" * 60 + "\n")
