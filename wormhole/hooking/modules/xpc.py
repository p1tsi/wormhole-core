import os
import json
import time
import base64

import binascii

from .base import BaseModule
from wormhole.utils.bplist17parser import BinaryPlist17Parser


def try_parse_root_field(message: str) -> str:
    msg_dict = json.loads(message)
    if msg_dict.get('root', None):

        try:
            root_data = base64.b64decode(msg_dict.get('root'))
        except binascii.Error:
            return message

        if root_data[:8].decode() == "bplist17":
            p = BinaryPlist17Parser(dict_type=dict)
            
            try:
                result = p.parse(root_data)
            except:
                result = p.parse(root_data, with_type_info=True)
            
            if result:
                result_str = json.dumps(result)
                msg_dict['root'] = result_str

                message = json.dumps(msg_dict)

    return message


class XpcMessage:

    def __init__(self, message="", service="", is_input_message=False):
        self.message: str = try_parse_root_field(message)
        self.xpc_service: str = service
        self.is_input_message: bool = is_input_message
        self.response: dict = dict()

    def set_response(self, response=""):
        self.response = try_parse_root_field(response)

    def __repr__(self):
        msg = f"{self.message} " \
              f"{'<--' if self.is_input_message else '-->'} " \
              f"{self.xpc_service}"

        if self.response:
            msg += "\n\nRESPONSE\n\n"
            msg += f"{self.response}"

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
        - _xpc_connection_call_event_handler
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self._async_messages = {}

    def _process(self):
        if "-callback" in self.message.symbol:
            xpc_message = self._async_messages.get(self.message.tid, None)
            
            if not xpc_message:
                self.publish(try_parse_root_field(self.message.args[0]))
                return

            xpc_message.set_response(try_parse_root_field(self.message.args[0]))
            self.publish(xpc_message, color='WARNING')
            del self._async_messages[self.message.tid]
        else:

            if "com.apple.cfprefsd.daemon" in self.message.args[0] or "com.apple.runningboard" in self.message.args[0] \
                    or "com.apple.UIKit.KeyboardManagement.hosted" in self.message.args[0]:
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

            if self.message.symbol == "xpc_connection_send_message":
                self.publish(xpc_message, color='WARNING')
            elif self.message.symbol == "xpc_connection_call_event_handler":
                self.publish(xpc_message, color='OKCYAN')
            elif "_sync" in self.message.symbol:
                """if len(self.message.ret) > 100000:
                    filename = f"Response_{time.time()}"
                    with open(os.path.join(self._module_dir, filename), "w") as outfile:
                        outfile.write(try_parse_root_field(self.message.ret))
                    xpc_message.set_response(filename)
                else:"""
                xpc_message.set_response(self.message.ret)

                self.publish(xpc_message, color='WARNING')
                
            else:
                self._async_messages[self.message.tid] = xpc_message
                