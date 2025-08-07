from .base import BaseConnector


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def set_color(forward_function):
        def wrapper(*args, **kwargs):
            color = kwargs.get('color', None)
            if color:
                message = args[1]
                final_message = f'{getattr(BColors, color)}{message}{BColors.ENDC}'
                return forward_function(args[0], final_message, **kwargs)
            else:
                return forward_function(*args, **kwargs)

        return wrapper


class File(BaseConnector):

    def __init__(self):
        super(File, self).__init__()
        self.file = open("/tmp/bo.txt", "a")

    @BColors.set_color
    def forward(self, message, **kwargs):
        #with open("/tmp/bo.txt", "a") as file:
        self.file.write(
            f"{kwargs.get('timestamp')} [{kwargs.get('tid')}] {kwargs.get('module')}({kwargs.get('function')}): "
            f"{message}\n"
            + "-" * 60 + "\n")
