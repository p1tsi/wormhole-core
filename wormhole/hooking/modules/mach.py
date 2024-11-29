from .base import BaseModule

KERN_RETURN_T = (
    "KERN_SUCCESS",
    "KERN_INVALID_ADDRESS",
    "KERN_PROTECTION_FAILURE",
    "KERN_NO_SPACE",
    "KERN_INVALID_ARGUMENT",
    "KERN_FAILURE",
    "KERN_RESOURCE_SHORTAGE",
    "KERN_NOT_RECEIVER",
    "KERN_NO_ACCESS",
    "KERN_MEMORY_FAILURE",
    "KERN_MEMORY_ERROR",
    "KERN_ALREADY_IN_SET",
    "KERN_NOT_IN_SET",
    "KERN_NAME_EXISTS",
    "KERN_ABORTED",
    "KERN_INVALID_NAME",
    "KERN_INVALID_TASK",
    "KERN_INVALID_RIGHT",
    "KERN_INVALID_VALUE",
    "KERN_UREFS_OVERFLOW",
    "KERN_INVALID_CAPABILITY",
    "KERN_RIGHT_EXISTS",
    "KERN_INVALID_HOST",
    "KERN_MEMORY_PRESENT",
    "KERN_MEMORY_DATA_MOVED",
    "KERN_MEMORY_RESTART_COPY",
    "KERN_INVALID_PROCESSOR_SET",
    "KERN_POLICY_LIMIT",
    "KERN_INVALID_POLICY",
    "KERN_INVALID_OBJECT",
    "KERN_ALREADY_WAITING",
    "KERN_DEFAULT_SET",
)

MSG_OPTIONS = {
    0x0: "MACH_MSG_OPTION_NONE",
    0x1: "MACH_SEND_MSG",
    0x2: "MACH_RCV_MSG",
    0x4: "MACH_RCV_LARGE",
    0x10: "MACH_SEND_TIMEOUT",
    0x40: "MACH_SEND_INTERRUPT",
    0x80: "MACH_SEND_CANCEL",
    0x100: "MACH_RCV_TIMEOUT",
    0x200: "MACH_RCV_NOTIFY",
    0x400: "MACH_RCV_INTERRUPT",
    0x1000: "MACH_RCV_OVERWRITE",
    0x20000: "MACH_SEND_TRAILER",
    0x10000: "MACH_SEND_ALWAYS"
}


RECV_MACH_PORTS = set()


class Mach(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        # self._files = dict()

    def get_string_BK(self, data):
        key = ""
        i = 0
        c = data[i]
        while c != 0:
            key = key + chr(c)
            i = i + 1
            c = data[i]
        if i % 4 != 0:
            return key, (int(i / 4) + 1) * 4
        return key, i

    def get_string(self, data):
        key = ""
        i = 0
        c = data[i]
        while c != 0:
            key = key + chr(c)
            i = i + 1
            c = data[i]
        return key, i + 1

    def get_mach_msg_params(self):
        msg_opt = " | "
        flags = []
        """for i in range(32):
            res = self.message.args[0] & (1 << i)
            if res:
                flags.append(MSG_OPTIONS.get(res, ''))"""
        if self.message.args[1] == 0:
            RECV_MACH_PORTS.add(hex(int(self.message.args[3])))
            #print("=" * 40, "MESSAGE", "=" * 40)
            #print(f"OPTION:\t{msg_opt.join(flags)}")
            #print(f"SEND SIZE:\t{self.message.args[1]}")
            #print(f"RECV SIZE:\t{self.message.args[2]}")
            #print(f"RECV NAME:\t{self.message.args[3]}")
            #print(f"TIMEOUT:\t{self.message.args[4]}")
            #print(f"NOTIFY:\t\t{self.message.args[5]}")
        print(RECV_MACH_PORTS)

    def _process(self):
        # self.get_mach_msg_params()
        # try:
        # print(self.message.data[44:])

        if self.message.data[24:28].decode('UTF-8') != "CPX@":

            self.get_mach_msg_params()
            """print(f"\t\tRAW HEADER: {self.message.data[:44]}")
            msgh_bits = self.message.data[:4]
            print(f"\t\tBITS: {msgh_bits}")
            msgh_size = int.from_bytes(self.message.data[4:8], byteorder='little')
            print(f"\t\tSIZE: {msgh_size}")
            msgh_remote_port = int.from_bytes(self.message.data[8:12], byteorder='little')
            msgh_local_port = int.from_bytes(self.message.data[12:16], byteorder='little')
            print(f"\t\tREMOTE PORT: {msgh_remote_port}")
            print(f"\t\tLOCAL PORT: {msgh_local_port}")
            msgh_reserved = int.from_bytes(self.message.data[16:20], byteorder='little')
            print(f"\t\tRESERVED: {msgh_reserved}")
            msgh_id = int.from_bytes(self.message.data[20:24], byteorder='little')
            print(f"\t\tMSG ID: {msgh_id}")
            # print(data[24:])
            print(f"\t\tVERSION: {int.from_bytes(self.message.data[28:32], 'little')}")
            print(f"\t\tTYPE: {self.message.data[32:36]}")
            content_length = int.from_bytes(self.message.data[36:40], 'little')
            print(f"\t\tBYTE LENGTH: {content_length}")
            dict_entries = int.from_bytes(self.message.data[40:44], 'little')
            print(f"\t\tDICT ENTRIES: {dict_entries}")
            print(f"\t\tACTUAL LENGTH: {len(self.message.data[44:])}")
            """

            """if self.message.data[24:28].decode('UTF-8') == "CPX@":
                self.get_mach_msg_params()
                print("\t\t", "=" * 15, f"{datetime.fromtimestamp((self.message.timestamp / 1000))} SENT XPC ",
                      "=" * 15)
                # print(f"\t\tRAW HEADER: {self.message.data[:44]}")
                msgh_bits = self.message.data[:4]
                print(f"\t\tBITS: {msgh_bits}")
                msgh_size = int.from_bytes(self.message.data[4:8], byteorder='little')
                print(f"\t\tSIZE: {msgh_size}")
                msgh_remote_port = int.from_bytes(self.message.data[8:12], byteorder='little')
                msgh_local_port = int.from_bytes(self.message.data[12:16], byteorder='little')
                print(f"\t\tREMOTE PORT: {msgh_remote_port}")
                print(f"\t\tLOCAL PORT: {msgh_local_port}")
                msgh_reserved = int.from_bytes(self.message.data[16:20], byteorder='little')
                print(f"\t\tRESERVED: {msgh_reserved}")
                msgh_id = int.from_bytes(self.message.data[20:24], byteorder='little')
                print(f"\t\tMSG ID: {msgh_id}")
                # print(data[24:])
                print(f"\t\tTYPE: @XPC")
                print(f"\t\tVERSION: {int.from_bytes(self.message.data[28:32], 'little')}")
                print(f"\t\tTYPE: {self.message.data[32:36]}")
                content_length = int.from_bytes(self.message.data[36:40], 'little')
                print(f"\t\tBYTE LENGTH: {content_length}")
                dict_entries = int.from_bytes(self.message.data[40:44], 'little')
                print(f"\t\tDICT ENTRIES: {dict_entries}")
                print(f"\t\tACTUAL LENGTH: {len(self.message.data[44:])}")

                if b"bplist" in self.message.data[44:44 + 32 + 100]:
                    print("\t\tBPLIST")
                else:
                    print(f"\t\tCONTENT: {self.message.data[44:]}")
                    # for i in range(0, content_length, 4):
                    #    print(f"> {data[44 + i:44 + i + 4]}")

                    xpc_dict = dict()
                    i = 44
                    c = 0
                    while c < dict_entries:
                        key, key_len = self.get_string(self.message.data[i:])
                        print("KEY LEN:", key_len)
                        i = i + key_len
                        while self.message.data[i] == 0:
                            i = i + 1
                        t = int(self.message.data[i])
                        if t == 144:
                            # STRING
                            i = i + 1
                            while self.message.data[i] == 0:
                                i = i + 1
                            str_len = int(self.message.data[i])
                            while self.message.data[i] == 0:
                                i = i + 1
                            value = self.get_string(self.message.data[i])
                        elif t == 64:
                            value = "TODO"
            """

        """except Exception:
            print("NOT XPC")

            # else:
            #    print("=" * 30 + f"{datetime.fromtimestamp((timestamp / 1000))} RECV " + "=" * 30)

            print(f"{KERN_RETURN_T[self.message.ret] if self.message.ret <= len(KERN_RETURN_T) else self.message.ret}")"""
