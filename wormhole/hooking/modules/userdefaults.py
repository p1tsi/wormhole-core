from .base import BaseModule


class Userdefaults(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self.user_defaults: dict = dict()

    def _process(self):
        if "standardUserDefaults" in self.message.symbol:
            self.publish(self.message.ret)
        if "synchronize" in self.message.symbol:
            self.publish(self.message.ret)
