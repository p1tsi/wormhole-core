# Thanks to https://github.com/seemoo-lab/plist17lib

import struct
from io import BytesIO


class InvalidFileException(Exception):
    pass


class BinaryPlist17Parser:

    def __init__(self, dict_type):
        self._dict_type = dict_type

    def parse(self, data: bytes, with_type_info=False):
        try:
            self._fp = BytesIO(data)
            # self._fp.seek(-32, os.SEEK_END)
            self._fp.seek(0)
            magic = self._fp.read(0x6)
            # print(magic)
            version = self._fp.read(0x2)
            # print(version)

            return self._read_object_at(0x8, with_type_info=with_type_info)

        except (OSError, IndexError, struct.error, OverflowError,
                ValueError):
            raise InvalidFileException()

    def _read_object_at(self, addr, with_type_info=False):
        """
        read the object by reference.

        May recursively read sub-objects (content of an array/dict/set)
        """
        # print("Entered _read_object_at: ", addr)
        totalReadBytes = []
        self._fp.seek(addr)
        token = self._fp.read(1)[0]
        totalReadBytes.append(token)
        tokenH, tokenL = token & 0xF0, token & 0x0F

        # elif token == 0x0f:
        #     result = b''

        if tokenH == 0x10:  # int
            # Integer (length tokenL)
            result_type = 'int'
            result_value = int.from_bytes(self._fp.read(tokenL), 'little', signed=True)

        elif token == 0x22:  # real
            result_type = 'float'
            result_value = struct.unpack('<f', self._fp.read(4))[0]

        elif token == 0x23:  # real
            result_type = 'double'
            result_value = struct.unpack('<d', self._fp.read(8))[0]

        elif tokenH == 0x40:  # data
            size = self._read_dynamic_size(totalReadBytes, tokenL)
            bytesData = self._fp.read(size)

            nestedData = BytesIO(bytesData)

            nestedData.seek(0)
            magic = nestedData.read(0x6)
            # print(magic)
            version = nestedData.read(0x2)
            # print(version)
            nestedData.seek(0)

            if len(bytesData) != size:
                raise InvalidFileException()

            result_type = 'data.hexstring'
            result_value = ''.join('{:02x}'.format(x) for x in bytesData)

            if magic == b'bplist':
                if version == b'00':
                    # parse bplist00
                    # TODO Fix BPlist00 parser
                    # type = 'data.bplist00'
                    # result = plistlibLoad(nestedData, fmt=PlistFormat.FMT_XML)
                    result_value = result_value
                elif version == b'17':
                    result_type = 'data.bplist17'
                    result_value = BinaryPlist17Parser(dict).parse(nestedData, with_type_info=with_type_info)

        elif tokenH == 0x60:  # unicode string
            size = self._read_dynamic_size(totalReadBytes, tokenL) * 2
            data = self._fp.read(size)
            if len(data) != size:
                raise InvalidFileException()
            result_type = 'string_utf16le'
            result_value = data.decode('utf-16le')

        elif tokenH == 0x70:  # ascii string
            size = self._read_dynamic_size(totalReadBytes, tokenL)
            data = self._fp.read(size)
            if len(data) != size:
                raise InvalidFileException()
            result_type = 'string_ascii'
            result_value = data.decode('ascii').rstrip('\x00')

        elif tokenH == 0x80:  # Referenced Object
            size = self._read_dynamic_size(totalReadBytes, tokenL)
            address = int.from_bytes(self._fp.read(size), 'little')
            currentAddr = self._fp.tell()
            result = self._read_object_at(address, with_type_info=with_type_info)
            self._fp.seek(currentAddr)
            return result  # return early, because the result of _read_object_at() is the final result
            # i.e. it already combines (type, value) if with_type_info == True

        elif tokenH == 0xA0:  # array
            endAddress = int.from_bytes(self._fp.read(0x8), 'little')
            result_type = 'array'
            result_value = []
            while (self._fp.tell() <= endAddress):
                result_value.append(self._read_object_at(self._fp.tell(), with_type_info=with_type_info))

            if self._fp.tell() != (endAddress + 1):
                raise InvalidFileException()  # TODO: Descriptive Exception

        elif token == 0xB0:
            result_type = 'bool'
            result_value = True

        elif token == 0xC0:
            result_type = 'bool'
            result_value = False

        elif tokenH == 0xD0:  # dict
            endAddress = int.from_bytes(self._fp.read(0x8), 'little')
            result_type = 'dict'
            result_value = self._dict_type()
            try:
                while (self._fp.tell() <= endAddress):
                    key = self._read_object_at(self._fp.tell(), with_type_info=False)
                    value = self._read_object_at(self._fp.tell(), with_type_info=with_type_info)
                    result_value[key] = value
            except TypeError:
                raise InvalidFileException()

            if self._fp.tell() != (endAddress + 1):
                raise InvalidFileException()  # TODO: Descriptive Exception

            result_value = self._transformDictionary(result_value, with_type_info=with_type_info)

        elif token == 0xE0:
            result_type = 'null'
            result_value = None

        elif tokenH == 0xF0:
            result_type = 'uint'
            result_value = int.from_bytes(self._fp.read(tokenL), 'big', signed=False)

        else:
            # raise InvalidFileException()
            raise TypeError("unsupported type: %s at: %s" % (''.join('{:02x}'.format(x) for x in totalReadBytes), addr))

        if with_type_info:
            result = self._dict_type()
            #result['type'] = result_type
            result['value'] = result_value
            return result
        else:
            return result_value

    def _read_dynamic_size(self, totalReadBytes, tokenL):
        if tokenL == 0xF:
            token2 = self._fp.read(1)[0]
            totalReadBytes.append(token2)
            length = token2 & 0xF  # extract last 4 bits from token2 as length
            if length != 0 and ((token2 & 0xF0) == 0x10):
                size = int.from_bytes(self._fp.read(length), 'little')
            else:
                raise TypeError("unsupported type: %s" % ''.join('{:02x}'.format(x) for x in totalReadBytes))
        else:
            size = tokenL
        return size

    def _transformDictionary(self, dictionary, with_type_info=False):
        transformed_dict = {}
        if with_type_info:
            return dictionary
        else:
            class_value = dictionary["$class"]
            if class_value == "NSDictionary" or class_value == "NSMutableDictionary":
                transformed_dict["$class"] = class_value
                keys = dictionary["NS.keys"]
                objects = dictionary["NS.objects"]
                for index in range(len(keys)):
                    transformed_dict[keys[index]] = objects[index]

                return transformed_dict
            else:
                return dictionary
