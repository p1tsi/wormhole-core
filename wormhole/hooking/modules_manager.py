import importlib
import logging

from typing import List, Tuple

from .connector_manager import ConnectorManager

BASE_MODULE = "wormhole.hooking.modules"

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class ModulesManager:
    """
    Singleton object handling all incoming messages from the agent running inside the app
    """

    def __init__(self, target_app: str, data_dir: str):
        self._app_name = target_app
        self._data_dir: str = data_dir
        self._available_custom_modules: List[str] = self._discover_custom_modules()
        self._modules: dict = dict()

    def get_available_standard_modules(self) -> List[str]:
        """
        Look for standard modules
        :return: list of standard modules found
        """
        try:
            return importlib.import_module(f".", package=BASE_MODULE).__all__
        except Exception as e:
            logger.error(f"Error getting custom modules for {self._app_name}: {e}")
            return [] 

    def _discover_custom_modules(self) -> List[str]:
        """
        Look for custom modules for current app/process
        :return: list of custom modules found
        """
        try:
            return importlib.import_module(f".custom.{self._app_name}", package=BASE_MODULE).__all__
        except Exception as e:
            logger.error(f"Error getting custom modules for {self._app_name}: {e}")
            return []

    def get_available_custom_modules(self) -> List[str]:
        """
        Returns the list of user-defined modules for current app/process
        :return: list of custom modules names
        """
        return self._available_custom_modules

    def _import_modules(self, modules: List[str], connector_manager: ConnectorManager) -> List[str]:
        """
        Import and initialize modules
        :param modules: list of modules to initialize
        :param connector_manager: ConnectionManager object passed to each module in order to let them publish the result of
                                their processing
        :return: list of correctly imported and initialized modules
        """
        initialized_modules = list()
        for module in modules:
            if module not in self._modules:
                try:
                    self._modules[module] = getattr(
                        importlib.import_module(f".{module}", package=BASE_MODULE),
                        module.capitalize())(self._data_dir, connector_manager)
                    initialized_modules.append(module)
                except Exception as e:
                    logger.error(f"Error setting '{module}' module: {e}")

        return initialized_modules

    def _import_custom_modules(self, custom_modules: List[str], connector_manager: ConnectorManager) -> List[str]:
        """
        Import and initialize custom modules
        :param custom_modules: list of custom modules
        :param connector_manager: ConnectionManager object passed to each module in order to let them publish the result of
                                their processing
        :return: list of correctly imported and initialized custom modules
        """
        initialized_custom_modules = list()
        for custom_module in custom_modules:
            if custom_module not in self._modules and custom_module in self._available_custom_modules:
                try:
                    self._modules[custom_module] = getattr(
                        importlib.import_module(f".custom.{self._app_name}", package=BASE_MODULE),
                        custom_module)(self._data_dir, connector_manager)
                    initialized_custom_modules.append(custom_module)
                except Exception as e:
                    logger.error(f"Plugin {custom_module} is not an available custom module or already added: {e}")

        return initialized_custom_modules

    def init_modules(self,
                     modules: List[str],
                     custom_modules: List[str],
                     connector_manager: ConnectorManager) -> Tuple[list, list]:
        """
        Initialize and set modules to use to inspect target app
        :param modules: list of modules names (strings)
        :param custom_modules: list of modules names available for target app (strings)
        :param connector_manager: manager of output connectors
        :return: list of correctly initialized modules, list of correctly initialized custom modules
        """

        return self._import_modules(modules, connector_manager), self._import_custom_modules(custom_modules,
                                                                                             connector_manager)

    def clear_modules(self) -> None:
        """
        Empty modules dict
        """

        self._modules = dict()

    def add_modules(self, modules: List[str], connector_manager: ConnectorManager) -> List[str]:
        """
        Add a module to module dict at runtime
        :param modules: list of new modules
        :param connector_manager: manager of output connectors
        :return: list of correct initialized modules
        """
        initialized_modules = list()
        for module in modules:
            if module not in self._modules:
                try:
                    self._modules[module] = getattr(
                        importlib.import_module(f".{module}", package="hooking.modules"),
                        module.capitalize())(self._data_dir, connector_manager)
                    initialized_modules.append(module)
                except Exception as e:
                    logger.error(f"Error setting '{module}' module: {e}")

        return initialized_modules

    def process_message(self, message: dict, data: bytes) -> None:
        """
        Process message coming from "send" function of agent running inside the target app/process
        :param message: dictionary containing message info
        :param data: raw bytes from "send" function
        """

        if message.get('type', '') == 'error':
            logger.error(f"Error: {message.get('fileName', '')}:"
                          f"{message.get('lineNumber', '')} - {message.get('description', '')}")
        else:
            module_name = message.get('payload', {}).get('type', '')
            try:
                self._modules[module_name].process(message, data)
            except Exception as e:
                logger.error(f"Error processing message: {e}.\n{message}")
