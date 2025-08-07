from .base import BaseModule



class Spwan(BaseModule):
    """
    This module is used to collect, process and aggregate the results of functions
    related to the creation and execution of new threads or subprocesses.
    Hooked functions:
        - pthread_create
        - popen
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        if self.message.symbol == "popen":
            self.publish(f"> {self.message.args[0]} -> {self.message.ret}")