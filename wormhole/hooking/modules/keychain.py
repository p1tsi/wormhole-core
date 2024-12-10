import os
import time

from .base import BaseModule


class Keychain(BaseModule):
    """
    This module is used to collect, process and aggregate the results of Keychain functions hooking.
    Hooked functions:
        - SecItemCopyMatching
        - SecItemAdd
        - SecItemDelete
        - SecItemUpdate
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        if self.message.data:
            filename = os.path.join(self._module_dir, f"{time.time()}")
            self.publish(f'{self.message.args[0]} -> {filename}')
            with open(filename, "wb") as binary_file:
                binary_file.write(self.message.data)
        else:
            if len(self.message.args) == 2:
                self.publish(f'{self.message.args[0]} -> {self.message.args[1]}')
            else:
                self.publish(f'{self.message.args[0]}')
