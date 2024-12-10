import os.path
import time
import base64
from enum import Enum

from .base import BaseModule


class Mode(Enum):
    ECB = 1
    CBC = 2
    CFB = 3
    CTR = 4
    OFB = 7
    RC4 = 9
    CFB8 = 10


class Algorithm(Enum):
    AES = 0
    DES = 1
    DES3 = 2
    CAST = 3
    RC4 = 4
    RC2 = 5
    Blowfish = 6


class EncryptSession:

    def __init__(self,
                 operation=None,
                 mode=None,
                 algorithm=None,
                 padding=None,
                 iv_present=False,
                 key_length=32,
                 data=bytes()):
        self.decrypt_op: bool = bool(int(operation, 16))
        self.mode: Mode = Mode(int(mode, 16))
        self.algorithm: Algorithm = Algorithm(int(algorithm, 16))
        self.padding = padding
        if iv_present:
            self.key = base64.b64encode(data[:key_length]).decode()
            self.iv = base64.b64encode(data[key_length:]).decode()
        else:
            self.key = base64.b64encode(data).decode()
            self.iv = None
        self.plaintext = bytes()
        self.cipehertext = bytes()

    def populate_data(self, data, input_len):
        input_data, output_data = data[:input_len], data[input_len:]
        if self.decrypt_op:
            self.cipehertext += input_data
            self.plaintext += output_data
        else:
            self.cipehertext += output_data
            self.plaintext += input_data

    def final_data(self, data):
        if self.decrypt_op:
            self.plaintext += data
        else:
            self.cipehertext += data

    def __repr__(self):
        final = "\n"
        final += "DECRYPT" if self.decrypt_op else "ENCRYPT"
        final += " "
        final += str(self.algorithm)
        final += " "
        final += f"({self.mode})"
        final += "\n"
        final += f"KEY: {self.key}"
        final += "\n"
        if self.iv:
            final += f"IV: {self.iv}"
            final += "\n"
        if self.decrypt_op:
            final += f"CIPHERTEXT ({len(self.cipehertext)}): {self.cipehertext[:16]}[...]"
            final += "\n"
            final += f"PLAINTEXT ({len(self.plaintext)}): {self.plaintext}"
        else:
            final += f"PLAINTEXT ({len(self.plaintext)}): {self.plaintext}"
            final += "\n"
            final += f"CIPHERTEXT ({len(self.cipehertext)}): {self.cipehertext[:16]}[...]"
            final += "\n"
            final += f"C-B64: {base64.b64encode(self.cipehertext)}"

        final += "\n" + "=" * 45 + "\n"
        return final


class Encryption(BaseModule):
    """
    This module is used to collect, process and aggregate the results of cryptography functions hooking.
    Hooked functions:
        - CCCryptorCreateWithMode
        - CCCryptorUpdate
        - CCCryptorGetOutputLength
        - CCCryptorFinal
        - CCCryptorRelease
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self.encryption_sessions: dict = dict()

    def _process(self):
        session = self.encryption_sessions.get(self.message.tid, None)
        if not session:
            if self.message.symbol == "CCCryptorCreateWithMode":
                session = EncryptSession(
                    self.message.args[0],   # OPERATION
                    self.message.args[1],   # MODE
                    self.message.args[2],   # ALGORITHM
                    self.message.args[3],   # PADDING
                    self.message.args[4],
                    self.message.args[5],
                    self.message.data       # KEY
                )
                self.encryption_sessions[self.message.tid] = session

            elif self.message.symbol == "CCCryptorGetOutputLength":
                session = EncryptSession()
                self.encryption_sessions[self.message.tid] = session
        else:
            if self.message.symbol == "CCCryptorUpdate":
                if self.message.data:
                    session.populate_data(self.message.data, self.message.args[0])
            elif self.message.symbol == "CCCryptorFinal":
                if self.message.data:
                    session.final_data(self.message.data)
            elif self.message.symbol == "CCCryptorRelease":
                with open(os.path.join(self._module_dir, f"{time.time()}"), "wb") as outfile:
                    outfile.write(session.plaintext)

                self.publish(str(session))
                del self.encryption_sessions[self.message.tid]
