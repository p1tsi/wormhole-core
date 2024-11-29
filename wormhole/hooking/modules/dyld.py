from .base import BaseModule


class Dyld(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self._dylibs = dict()

    def _process(self):
        if self.message.symbol == "dlopen":
            if self.message.ret != "NULL":
                self._dylibs[self.message.ret] = self.message.args[0]
                self.publish(self.message.args[0])
            else:
                self.publish(f"ERROR OPENING {self.message.args[0]}")
        elif self.message.symbol == "dlopen_from":
            self.publish(f"{self.message.args[0]}")
        elif self.message.symbol == 'dlsym':
            self.publish(f"{self._dylibs.get(self.message.args[0])} - {self.message.args[1]}")
        else:
            self.publish(f"CLOSED {self._dylibs.get(self.message.args[0])}")
            del self._dylibs[self.message.args[0]]
