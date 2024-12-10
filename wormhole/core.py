import os
import frida
import shutil
import logging
import paramiko
import subprocess

from paramiko import SSHClient
from scp import SCPClient
from typing import List, Union, Tuple
from flask_socketio import Namespace
from enum import Enum

from .hooking.connector_manager import ConnectorManager
from .hooking.modules_manager import ModulesManager

AGENT_PROJECT_DIR = os.path.join(os.getcwd(), 'wormhole-agent')
AGENT_DIR = os.path.join(os.getcwd(), 'agents')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


class TargetOs(Enum):
    IOS = "ios"
    MACOS = "macos"


class Core(object):

    def __init__(self, device: frida.core.Device, target: Union[str, int], ws: Union[Namespace, None]):
        """
        Initialize Core
        :param device: device to attach
        :param target: bundle ID of the app/pid of the process to analyze
        :param ws: websocket connection with GUI
        """
        self._ws = ws
        self._device: frida.core.Device = device
        self._os: TargetOs = TargetOs.MACOS if device.query_system_parameters().get('os').get(
            'id') == 'macos' else TargetOs.IOS

        # Setup callbacks on device
        if self._device:
            self._device.on('output', lambda: logger.info("DEVICE OUTPUT"))
            if self._ws:
                self._device.on('lost', lambda: ws.emit('detached'))

        # Passing pid => already running app || system daemon
        if isinstance(target, int):
            self._target_pid: int = target
            self._target_name: str = list(
                filter(lambda x: x.pid == target, self._device.enumerate_processes(scope="metadata"))
            )[0].name
        # If target is a string then spawn the app
        else:
            self._target_name: str = target
            self._target_pid: Union[int, None] = None

        self._data_dir: str = self._create_data_dir()
        self._session: Union[frida.core.Session, None] = None
        self._script = None
        self._resumed = False if not self._target_pid else True
        self._modules_manager: ModulesManager = ModulesManager(self._target_name, self._data_dir)
        self._connector_manager: Union[ConnectorManager, None] = None
        self._hooking_ops: bool = False
        self._dumped_ipa: bool = False

    def is_target_resumed(self) -> bool:
        """
        Check if target app/process is resumed
        """
        return self._resumed

    def resume_target(self) -> bool:
        """
        If the app/process is not resumed, resume it.
        """
        if not self._resumed:
            try:
                logger.info("Resume target")
                self._device.resume(self._target_pid)
                self._resumed = True
                return True
            except Exception as e:
                logger.error(f"Error resuming tagret: {e}")
                return False

        logger.info("Target already resumed")
        return True

    def _create_data_dir(self) -> str:
        """
        Create home app directory
        """
        base_dir = os.path.join(os.getcwd(), 'appData')
        dir_path = os.path.join(base_dir,
                                f"{self._target_name + '_' + str(self._target_pid) if self._target_pid else self._target_name}")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        else:
            shutil.rmtree(dir_path)
            os.makedirs(dir_path)

        logger.info(f"Create data directory at: {dir_path}")
        return dir_path

    def _on_session_detached(self) -> None:
        logger.info("Session detached")
        if self._ws:
            self._ws.emit('destroyed')

    def _on_destroyed(self):
        logger.info('Script destroyed')
        if self._ws:
            self._ws.emit('destroyed')

    def custom_modules(self) -> List[str]:
        """
        Retrieve a list of custom hooking modules for currently analyzed application.
        """
        custom_modules = self._modules_manager.get_available_custom_modules()
        logger.info(f"Getting custom hooking modules: {custom_modules}")
        return custom_modules

    def _dynamic_compile(self, final_agent_script_path: str, custom_modules: List) -> str:
        """
        Modify the file 'hooking.template.ts' adding rows of code that let hook custom functions
        :param final_agent_script_path: the path for the new agent to be compiled
        :param custom_modules: list of modules specific for current analyzed application
        :return: path for the compiled custom agent
        """
        hooking_template_file_path = os.path.join(
            AGENT_PROJECT_DIR,
            'src',
            self._os.value,
            'hooking',
            'hooking.template.ts'
        )
        final_hooking_file_path = os.path.join(
            AGENT_PROJECT_DIR,
            'src',
            self._os.value,
            'hooking',
            'hooking.ts'
        )
        app_name = self._target_name.replace(".", "/")
        with open(hooking_template_file_path, "r") as read_hooking_file:
            hooking_file_content = read_hooking_file.readlines()

        out_hooking_file = []
        for line in hooking_file_content:
            out_hooking_file.append(line)
            if '//#IMPORT#//' in line:
                for module in custom_modules:
                    out_hooking_file.append("\nimport { %s_functions } from './modules/custom/%s/%s';\n" %
                                            (module, app_name, module))
            if '//#FOREACH#//' in line:
                out_hooking_file.append("\n\tcustomModules.forEach(module => {\n")
                for i, module in enumerate(custom_modules):
                    if i == 0:
                        out_hooking_file.append("\t\tif (module === '%s')"
                                                "{ %s_functions.forEach(func => attach_interceptor_to_func(func))}\n"
                                                % (module, module))
                    else:
                        out_hooking_file.append("\t\telse if (module === '%s')"
                                                "{ %s_functions.forEach(func => attach_interceptor_to_func(func))}\n"
                                                % (module, module))

                out_hooking_file.append("\t});\n")

        with open(final_hooking_file_path, "w") as write_hooking_file:
            write_hooking_file.writelines(out_hooking_file)

        # ...and then compile the agent
        logger.info("Compiling custom agent")
        p = subprocess.Popen(["npm", "run", "build", final_agent_script_path], cwd=AGENT_PROJECT_DIR)
        p.communicate()
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            logger.error("COMPILATION TIMEOUT EXPIRED")
            exit(1)
        logger.info("Compilation done")
        os.remove(final_hooking_file_path)

        return final_agent_script_path

    def _get_agent_path(self, force: bool = False) -> str:
        """
        As it is possible to add custom modules to hook app-specific classes' methods and functions,
            it is necessary to compile the agent dynamically in order to use custom modules.
        :param force: Force recompile
        :return: path for compiled agent or default agent
        """

        # TODO: It seems that exists some frida compilation method. Check it out.

        custom_modules = self._modules_manager.get_available_custom_modules()
        if not custom_modules:
            agent_name = f'_{self._os.value}_base_agent.js'
            logger.info(f"No custom modules. Using base agent {agent_name}")
            # Default agent script (precompiled)
            return os.path.join(AGENT_DIR, agent_name)

        final_agent_script_path = os.path.join(AGENT_DIR, f"_{self._os.value}_{self._target_name}_agent.js")
        if os.path.exists(final_agent_script_path) and not force:
            logger.info(f"Using already compiled custom agent: {final_agent_script_path}...")
            return final_agent_script_path

        logger.info(f"Custom modules: {custom_modules}. Compiling custom agent...")
        # Dynamically modify 'hooking.template.ts' file to include stuff related to custom modules
        self._dynamic_compile(final_agent_script_path, custom_modules)

        return final_agent_script_path

    def _on_message(self, message: dict, data: bytes) -> None:
        """
        Callback method on receiving message
        :param message: dictionary containing message info
        :param data: raw bytes from "send" function
        """
        self._modules_manager.process_message(message, data)

    def run(self) -> bool:
        """
        Spawn target app, load the agent script and resume the app
        :return: true if everything goes well
        """

        # Prepare agent script to inject
        script_path = self._get_agent_path()
        with open(script_path, "r") as js_file:
            js_source = js_file.read()

        # Spawn target if needed
        if not self._target_pid:
            try:
                logger.info(f"Spawning {self._target_name}...")
                self._target_pid = self._device.spawn(self._target_name)
            except Exception as e:
                logger.error(f"Impossible to spawn target app: {e}")
                return False
        else:
            logger.info(f"{self._target_name} already running")
            self._resumed = True

        # Inject script and attach to the session
        try:
            timeout = 180 if self._device.type == 'remote' else 60
            self._session = self._device.attach(self._target_pid, persist_timeout=timeout)
        except frida.TransportError as e:
            logger.error(f'{e}')
            return False

        self._script = self._session.create_script(js_source)
        self._session.on('detached', self._on_session_detached)
        self._script.on('message', self._on_message)
        self._script.on('destroyed', self._on_destroyed)
        # self._script.on('exited', )
        # self._script.on('stopped', )
        # self._script.on('crashed', )
        # self._script.on('unload', )
        self._script.load()

        return True

    def operations(self, modules: List[str], custom_modules: List[str], connectors: List[str]) -> bool:
        """
        Start hooking app's functions related to modules and custom modules. Publish intercepted calls to connectors
        :param modules: list of modules to hook
        :param custom_modules: list of custom modules created for single applications/processes
        :param connectors: list of connectors that publish intercepted data to their specific container
        :retval: true if everything goes well
        """
        if self._hooking_ops:
            logging.warning("Already hooking functions")
            return False

        try:
            self._connector_manager = ConnectorManager(connectors, self._ws)
            modules, custom_modules = self._modules_manager.init_modules(
                modules,
                custom_modules,
                self._connector_manager
            )
        except Exception as e:
            logger.error(e)
            return False

        if not modules and not custom_modules:
            logger.error("No hooking modules")
            return False

        logger.info(f"Hooking functions from {modules} and {custom_modules}")
        logger.info(f"Sending output to {connectors}")
        res = self._script.exports.hook(modules, custom_modules)
        if res:
            self._hooking_ops = True
            if not self._resumed:
                return self.resume_target()
            else:
                return True
        else:
            logger.error("Error hooking functions!")
            return False

    def unhook(self):
        """
        Remove all previously added hooks
        """
        if not self._hooking_ops:
            return False

        logger.info("Remove hooks")
        self._script.exports.unhook()
        self._hooking_ops = False
        self._modules_manager.clear_modules()
        self._connector_manager.clean_connectors()
        return True

    def execute_method(self, method: str, *args):
        """
        Execute a one-shot function from agent script
        :param method: the name of the function to call
        :return: the output from called function from
                    injected script inside app's process
        """

        logger.info(f"Call {method} {args}")
        if method == 'dumpipa':
            return self._dump_ipa(method, args)
        else:
            try:
                data = self._script.exports.invoke(method, args)
                err = None
            except Exception as e:
                logger.error(e)
                data, err = None, str(e)

        return data, err

    def detach_session(self):
        self.unhook()
        self._session.detach()

    def kill_session(self):
        self.detach_session()
        self._device.kill(self._target_pid)

    def _dump_ipa(self, method: str, args: tuple) -> Tuple[Union[str, None], Union[str, None]]:
        """
        Dump unencrypted IPA from the device.
        NB: in oreder to use this function, it is foundamental to have previously run an "iproxy" command
            or to have ssh access to jailbroken device.
        :param method: string representing the agent's method to dump ipa
        :param args: tuple of args to pass to method
        :return: a tuple of (Return_message, Error_message). Only one of them is populated.
        """
        if self._dumped_ipa:
            logger.warning("IPA already dumped")
            return None, 'IPA already dumped'

        try:
            items = self._script.exports.invoke(method, args)

            if not items:
                return None, "No files to download"

            payload_dir = os.path.join(self._data_dir, "Payload")
            if not os.path.exists(payload_dir):
                os.makedirs(payload_dir)

            with SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    "127.0.0.1",
                    port=2222,
                    username="root",
                    password="alpine"
                )

                with SCPClient(ssh.get_transport(), socket_timeout=60) as scp:
                    bundle_dir = ""
                    for item in items:
                        logger.info(f"Getting {item.get('path')}")
                        if item.get("is_dir"):
                            bundle_dir = os.path.basename(item.get('path'))
                            scp.get(
                                item.get('path'),
                                os.path.join(self._data_dir, "Payload"),
                                recursive=True
                            )
                        else:
                            filename = os.path.basename(item.get('path'))
                            scp.get(
                                item.get('path'),
                                os.path.join(self._data_dir, "Payload", bundle_dir, filename),
                                recursive=True
                            )
                    logger.info("IPA correctly dumped!")
                data, err = "IPA correctly dumped!", None

        except Exception as e:
            logger.error(e)
            data, err = None, str(e)

        return data, err
