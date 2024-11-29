from .base import BaseModule


class Icloud(BaseModule):

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)

    def _process(self):
        if "startDownloading" in self.message.symbol:
            self.publish(f"Downloading {self.message.args[0]}...")
        elif 'ubiquityIdentityToken' in self.message.symbol:
            self.publish(f"Token: {self.message.args[0]}")
        elif 'ContainerIdentifier' in self.message.symbol:
            self.publish(f"Container ID: {self.message.args[0]}")
        else:
            self.publish(self.message.args)