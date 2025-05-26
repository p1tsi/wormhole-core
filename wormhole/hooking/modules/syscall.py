import base64

from .base import BaseModule


class Syscall(BaseModule):
    """
    This module is used to collect, process and aggregate the results of syscalls hooking.
    Hooked functions:
        - __mac_syscall
        - sysctl
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        if self.message.symbol == "__mac_syscall" or self.message.symbol == "sysctlbyname":
            self.publish(f"{self.message.symbol}({self.message.args[0]}, "
                         f"{self.message.args[1]}, "
                         f"{self.message.args[2]}) "
                         f"-> {self.message.ret}")
        elif self.message.symbol == "sysctl":
            self.publish(f"{self.message.symbol}({self.message.args[0]}, "
                         f"{self.message.args[1]}, "
                         f"{self.message.args[2]}, "
                         f"{self.message.args[3]}) "
                         f"-> {self.message.ret}")
        elif self.message.symbol == "renameat":
            self.publish(f"{self.message.symbol}({self.message.args[0]}, "
                         f"{self.message.args[1]}) "
                         f"-> {self.message.ret}")
        elif "execve" in self.message.symbol:
            self.publish(f"{self.message.symbol}({self.message.args[0]}) -> {self.message.ret}")
