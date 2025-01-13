import os
import time

from .base import BaseModule

MODE = {
    "0x0": "O_RDONLY",
    "0x1": "O_WRONLY",
    "0x2": "O_RDWR",
    "0x3": "O_ACCMODE",
    "0x10": "O_SHLOCK",
    "0x20": "O_EXLOCK",
    "0x40": "O_ASYNC",
    "0x100": "O_NOFOLLOW",
    "0x200": "O_CREAT",
    "0x400": "O_TRUNC",
    "0x800": "O_EXCL",
    "0x1000": "TRUNC",
    "0x2000": "APPEND",
    "0x4000": "NONBLOCK",
    "0x8000": "O_EVTONLY",
    "0x10000": "SYNC",
    "0x20000": "O_NOCTTY",
    "0x40000": "DIRECT",
    "0x100000": "O_DIRECTORY",
    "0x200000": "O_SYMLINK",
    "0x400000": "O_DSYNC",
    "0x1000000": "O_CLOEXEC",
    "0x2000000": "CLOEXEC",
    "0x20000000": "O_NOFOLLOW_ANY",
}

FILE_NOT_OPENED = '0xffffffffffffffff'
STREAM_NOT_OPENED = '0x0'


class Io(BaseModule):
    """
    This module is used to collect, process and aggregate the results of IO functions hooking.
    Hooked functions:
        - open
        - read
        - write
        - close
        - fopen
        - fclose
        - fwrite
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        read_dir = os.path.join(self._module_dir, "read")
        write_dir = os.path.join(self._module_dir, "write")
        os.mkdir(read_dir) if not os.path.exists(read_dir) else None
        os.mkdir(write_dir) if not os.path.exists(write_dir) else None

        # Keep track of opened files. Key: file descriptor, value: file path
        self._files = dict()

    @staticmethod
    def parse_mode_flags(flags):
        flags_list = list()
        for i in range(32):
            res = int(flags, 16) & (1 << i)
            if res:
                flags_list.append(MODE.get(str(hex(res)), ''))
        return " | ".join(flags_list) if flags_list else MODE.get(flags)

    def _process(self):
        if 'open' in self.message.symbol:
            res = 'KO'

            if self.message.ret != FILE_NOT_OPENED and self.message.ret != STREAM_NOT_OPENED:
                res = 'OK'
                self._files[self.message.ret] = self.message.args[0]

            mode = self.parse_mode_flags(self.message.args[1]) if not self.message.symbol.startswith(
                "f") else self.message.args[1]
            self.publish(f"{self.message.args[0]} -> {mode} ({res})")
        elif 'read' in self.message.symbol:
            file_path = self._files.get(self.message.args[0], None)
            if file_path:
                if not file_path.startswith("/System/Library/") or not file_path.endswith('Info.plist'):
                    try:
                        with open(os.path.join(self._module_dir,
                                               "read",
                                               "_".join(file_path.split("/")[-2:]) + f"_{time.time()}"),
                                  "ab") as f:
                            f.write(self.message.data)
                    except Exception:
                        pass
            else:
                with open(os.path.join(self._module_dir,
                                       "read",
                                       "NOTFOUND" + f"_{time.time()}"),
                          "ab") as io_file:
                    io_file.write(self.message.data)
        elif "write" in self.message.symbol:
            file_path = self._files.get(self.message.args[0], None)
            if file_path:
                if not file_path.endswith('.log'):
                    with open(os.path.join(self._module_dir,
                                           "write",
                                           "_".join(file_path.split("/")[-2:]) + f"_{time.time()}"),
                              "ab") as io_file:
                        io_file.write(self.message.data)
            else:
                with open(os.path.join(self._module_dir,
                                       "write",
                                       "NOTFOUND" + f"_{time.time()}"),
                          "ab") as io_file:
                    io_file.write(self.message.data)
        elif "close" in self.message.symbol:
            try:
                del self._files[self.message.args[0]]
            except KeyError:
                pass
