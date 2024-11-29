import frida

from core import Core
from static.radare2 import Radare2

device = frida.get_usb_device()

target = ""
wormhole = Core(device, target, None)
wormhole.run()

cmd = None
subcmd = None
try:
    while cmd != '10':
        cmd = input(">")
        if cmd == "1":
            wormhole.resume_target()
        if cmd == "2":
            print(wormhole.execute_method("checksec"))
        if cmd == "3":
            subcmd = input(">>")
            if subcmd == "1":
                print(wormhole.execute_method("info/icon"))
            if subcmd == "2":
                print(wormhole.execute_method("info/info"))
            if subcmd == "3":
                print(wormhole.execute_method("info/userDefaults"))
        if cmd == "4":
            print(wormhole.execute_method("certpinning"))
        if cmd == "5":
            print(wormhole.operations(["io"], [], ["file"]))
        if cmd == "6":
            print(wormhole.unhook())
        if cmd == "7":
            print(wormhole.execute_method("dumpipa"))
        if cmd == '10':
            wormhole.kill_session()

except KeyboardInterrupt:
    if isinstance(target, str):
        wormhole.kill_session()

print("See U soon!")
