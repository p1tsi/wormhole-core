from .base import BaseModule


class Gestalt(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        self.publish(f"{self.message.args[0]} -> {self.message.ret}")