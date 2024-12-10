from .base import BaseModule


class Userdefaults(BaseModule):
    """
    This module is used to collect, process and aggregate the results of UserDefaults functions hooking.
    Hooked functions:
        -[NSUserDefaults synchronize]
    """
    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self.user_defaults: dict = dict()

    def _process(self):
        if "standardUserDefaults" in self.message.symbol:
            self.publish(self.message.ret)
        if "synchronize" in self.message.symbol:
            self.publish(self.message.ret)
