import logging
import importlib

from typing import List
from flask_socketio import Namespace

BASE_MODULE = "wormhole.hooking.connectors"

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class ConnectorManager:
    """
    This is a singleton class that receives processed content from modules and forward it
    to all predefined output sources.
    """

    def __init__(self, connectors_list: List[str], ws: Namespace = None):
        self._connectors: list = list()
        for connector_name in connectors_list:
            try:
                connector = getattr(
                    importlib.import_module(f".{connector_name}", package=BASE_MODULE),
                    connector_name.capitalize()
                )
                if connector_name == "websocket" and ws:
                    self._connectors.append(connector(ws))
                else:
                    self._connectors.append(connector())
            except Exception as e:
                logger.error(f"Error on connector '{connector_name}': {e}")

    def clean_connectors(self):
        """
        Empty connectors list
        """
        self._connectors = list()

    def forward(self, content, *args, **kwars) -> None:
        """
        Take the content from processing modules and forward it to all initialized output sources
        :param content: processed message to forward
        """
        for connector in self._connectors:
            connector.forward(content, *args, **kwars)
