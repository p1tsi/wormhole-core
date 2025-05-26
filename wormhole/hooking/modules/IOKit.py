import base64

from .base import BaseModule


class KextConnection:

    def __init__(self):
        self.kext_name = ''
        self.service_id = ''
        self.connection_id = ''


class Iokit(BaseModule):
    """
    This module is used to collect, process and aggregate the results of IOKit functions hooking.
    Hooked functions:
        - IOServiceMatching,
        - IOServiceNameMatching,
        - IOServiceGetMatchingService,
        - IOServiceGetMatchingServices,
        - IOServiceOpen,
        - IOConnectCallMethod,
        - IOConnectCallScalarMethod
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self.kexts = dict()

    def _process(self):
        if self.message.symbol == 'IOServiceMatching' or self.message.symbol == 'IOServiceNameMatching':
            self.publish(f"Driver Name:\t{self.message.args[0]} -> {self.message.ret}")

        elif self.message.symbol == 'IOServiceGetMatchingService':
            self.publish(f"{self.message.args[0]} -> {self.message.ret}")
        elif self.message.symbol == 'IOServiceGetMatchingServices':
            self.publish(f"{self.message.args[0]} -> {self.message.ret}")
        elif self.message.symbol == 'IOServiceOpen':
            self.publish(
                f"Service: {self.message.args[0]} -> Connection: {self.message.args[1]}\tRET:{self.message.ret}")
        # elif self.message.symbol == 'IOIteratorNext':
        #    self.publish(f"{self.message.ret}")
        elif self.message.symbol == 'IOConnectCallScalarMethod':
            self.publish(f"Port:{self.message.args[0]} -> "
                         f"{self.message.args[1]}({self.message.args[2]}) = {self.message.args[3]}\tRET:{self.message.ret}")
        elif self.message.symbol == 'IOConnectCallMethod':
            if self.message.data:
                message = f"Port:{self.message.args[0]} -> "
                message += f"{self.message.args[1]}({self.message.args[2]}, {self.message.args[3]}, "

                if self.message.args[5] > 0:
                    message += f"{base64.b64encode(self.message.data[:self.message.args[5]]).decode()}, {self.message.args[5]})"
                else:
                    message += "0, 0)"

                message += f" = ({self.message.args[6]}, {self.message.args[7]}, "

                if self.message.args[9] > 0:
                    message += f"{base64.b64encode(self.message.data[self.message.args[5]:]).decode()}, {self.message.args[9]})"
                else:
                    message += "0, 0)"
                message += f"\tRET:{self.message.ret}"

                self.publish(message)
            else:
                self.publish(f"Port:{self.message.args[0]} -> "
                             f"{self.message.args[1]}({self.message.args[2]}, {self.message.args[3]}, "
                             f"{self.message.args[4]}, {self.message.args[5]})"
                             f" = ({self.message.args[6]}, {self.message.args[7]}, "
                             f"{self.message.args[8]}, {self.message.args[9]})"
                             f"\tRET:{self.message.ret}")
        else:
            self.publish(f"{self.message.args}")
