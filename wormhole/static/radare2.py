import r2pipe

from enum import Enum


class InfoCommand(Enum):
    segments = 'iSS'
    sections = 'iS',
    # signature     = 'iC',
    libraries = 'il',
    classes = 'ic'
    size = 'iZ'
    symbols = 'is'
    relocations = 'ir'
    codesign = 'iO c'
    entitlements = 'iO C'
    info = 'iI'
    imports = 'ii'
    headers = 'ih'
    exports = 'iE'
    strings = 'iz'


def modify_cmd(func):
    def wrapper(*args, **kwargs):
        command = InfoCommand.__getitem__(args[1]).value
        if kwargs.get('json', False):
            command += 'j'
            return func(args[0], command)
        else:
            filter_items = kwargs.get('filter', [])
            if filter_items:
                for item in filter_items:
                    command += f'~{item}'
        return func(args[0], command)

    return wrapper


class Radare2:

    def __init__(self, binary_path):
        self.r2 = r2pipe.open(binary_path)
        self.r2.cmd("aaaa")

    # GENERIC COMMANDS

    def run_custom_command(self, command: str):
        """
        Run generic r2 command
        :param command: generic command by user
        """
        return self.r2.cmd(command)

    @modify_cmd
    def exec_cmd(self, command: str, **kwargs):
        """

        """
        print(f"r2> {command}")
        return self.r2.cmd(command)



