import json

from .base import BaseModule


class XpcMessage:

    def __init__(self, message="", service="", is_input_message=False):
        self.message: str = message
        self.xpc_service: str = service
        self.is_input_message: bool = is_input_message
        self.response: dict = dict()

    def __repr__(self):
        msg = f"{self.message} " \
              f"{'<--' if self.is_input_message else '-->'} " \
              f"{self.xpc_service}" \

        if self.response:
            msg += "\n\nRESPONSE\n\n" \
                   f"{self.response if self.response else ''}"

        return msg

    """
    TODO: if you want a message as dict, you should implement this __iter__ method
    def __iter__(self):
        for key in self.__dict__:
            if key == 'from_service':
                yield key, getattr(self, key)
            if key == 'message':
                yield 'content', json.loads(getattr(self, key))
            if key == 'xpc_service'
        #message_as_dict['content'] = json.loads(self.message)
        #message_as_dict['service'] = json.loads(self.xpc_service)
        #message_as_dict['service']['process'] = PROCESSES.get(message_as_dict['service']['pid'], 'N/A')
        #message_as_dict['from_service'] = self.from_service
        #return message_as_dict
    """


class Xpc(BaseModule):
    """
    This module is used to collect, process and aggregate the results of XPC functions hooking.
    Hooked functions:
        - xpc_connection_send_message
        - xpc_connection_send_message_with_reply
        - xpc_connection_send_message_with_reply_sync
        - xpc_connection_send_notification
        - _xpc_connection_call_event_handler
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        if "-callback" in self.message.symbol:
            self.publish(json.loads(self.message.args[0]))
        else:
            """if 'com.apple.xpc.anonymous' in connection_string:
                try:
                    connection = json.loads(self.message.args[0])
                    connection['name'] = list(
                        filter(
                            lambda p: p.pid == connection.get('pid'),
                            list(
                                filter(
                                    lambda d: d.type == 'usb',
                                    frida.enumerate_devices()
                                )
                            )[0].enumerate_processes()
                        )
                    )[0].name
                    print(connection['name'])
                    connection_string = json.dumps(connection)
                except Exception:
                    pass  # print("Pid not found")"""

            if "com.apple.cfprefsd.daemon" in self.message.args[0] or "com.apple.runningboard" in self.message.args[0] \
                    or "com.apple.UIKit.KeyboardManagement.hosted" in self.message.args[0] or "com.apple.windowmanager.server" in self.message.args[0]:
                return

            try:
                xpc_message = XpcMessage(
                    self.message.args[1],
                    self.message.args[0],
                    "call_event_handler" in self.message.symbol
                )
            except Exception:
                print("Error creating XpcMessage object")
                return

            if "_sync" in self.message.symbol:
                xpc_message.response = self.message.ret

            self.publish(xpc_message, color='OKCYAN' if xpc_message.is_input_message else 'WARNING')
