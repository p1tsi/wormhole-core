from .base import BaseModule


class Download(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        print(self.message)