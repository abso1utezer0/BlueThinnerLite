# epicmickeylib/formats/caf.py
# 
# audio container format for Epic Mickey 2: The Power of Two

import json
import os
from epicmickeylib.internal.file_manipulator import FileManipulator, EndianType

class VirtualAudioFile:
    hashed_name: int
    data: bytes

    def __init__(self, hashed_name: int, data: bytes):
        self.hashed_name = hashed_name
        self.data = data
    
    def get_aligned_data(self, alignment: int = 2048) -> bytes:
        return self.data + b"\x00" * (alignment - (len(self.data) % alignment))


class CafFile:
    unknown_1: int
    unknown_2: int
    unknown_3: int
    files: list[VirtualAudioFile]

    def __init__(self, unknown_1: int = 0, unknown_2: int = 2, unknown_3: int = 2048, files: list[VirtualAudioFile] = []):
        self.unknown_1 = unknown_1
        self.unknown_2 = unknown_2
        self.unknown_3 = unknown_3
        self.files = files
    
    def unpack(self, fm:FileManipulator):
        self.unknown_1 = fm.r_u32()
        amount_of_files = fm.r_u32()
        self.unknown_2 = fm.r_u32()
        self.unknown_3 = fm.r_u32()
        fm.move(0x10)
        self.files = []
        current_header_pos = fm.tell()
        for i in range(amount_of_files):
            hashed_name = fm.r_u32()
            data_offset = fm.r_u32()
            data_size = fm.r_u32()
            current_header_pos = fm.tell()
            fm.seek(data_offset)
            data = fm.read(data_size)
            fm.seek(current_header_pos)
            self.files.append(VirtualAudioFile(hashed_name, data))
        return fm

    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_u32(self.unknown_1)
        fm.w_u32(len(self.files))
        fm.w_u32(self.unknown_2)
        fm.w_u32(self.unknown_3)
        fm.write(b"\x00" * 0x10)
        current_header_pos = fm.tell()
        current_data_pos = current_header_pos + (12 * len(self.files))
        # align data position to 2048
        current_data_pos = (current_data_pos + 2047) & ~2047
        for file in self.files:
            fm.w_u32(file.hashed_name)
            fm.w_u32(current_data_pos)
            fm.w_u32(len(file.data))
            current_header_pos = fm.tell()
            fm.seek(current_data_pos)
            fm.write(file.get_aligned_data())
            current_data_pos = fm.tell()
            fm.seek(current_header_pos)
        return fm.getbuffer().tobytes()
    
    def to_dict_stripped(self):
        return {
            "unknown_1": self.unknown_1,
            "unknown_2": self.unknown_2,
            "unknown_3": self.unknown_3
        }
    
    def to_json_stripped(self, pretty: bool = True):
        return json.dumps(self.to_dict_stripped(), indent=4 if pretty else None)

    def to_json_stripped_path(self, path: str, pretty: bool = True):
        with open(path, "w") as f:
            f.write(self.to_json_stripped(pretty))
    
    def to_binary(self, endian: EndianType = EndianType.BIG) -> bytes:
        return self.pack(endian)
    
    def to_binary_path(self, path: str, endian: EndianType = EndianType.BIG):
        with open(path, "wb") as f:
            f.write(self.to_binary(endian))
    
    def extract(self, directory: str, overwrite: bool = False):
        if not os.path.exists(directory):
            os.makedirs(directory)
        for file in self.files:
            file_path = os.path.join(directory, f"{file.hashed_name}.wem")
            if not os.path.exists(file_path) or overwrite:
                with open(file_path, "wb") as f:
                    f.write(file.data)
        # write metadata
        self.to_json_stripped_path(os.path.join(directory, "caf_stripped.json"))
    
    @staticmethod
    def compress(directory: str, path: str, endian: EndianType = EndianType.BIG):
        # read metadata
        caf = CafFile.from_json_stripped_path(os.path.join(directory, "caf_stripped.json"))
        caf.files = []
        # get a list of wem files with numbers as names
        wem_files = [f for f in os.listdir(directory) if f.endswith(".wem") and f[:-4].isnumeric()]
        # sort the list by the number
        wem_files.sort(key=lambda x: int(x[:-4]))
        # read wem files
        for wem_file in wem_files:
            with open(os.path.join(directory, wem_file), "rb") as f:
                data = f.read()
            caf.files.append(VirtualAudioFile(int(wem_file[:-4]), data))
        # write caf
        caf.to_binary_path(path, endian)
    
    @staticmethod
    def from_binary(data: bytes, endian: EndianType):
        fm = FileManipulator(data=data, endian=endian)
        caf = CafFile()
        caf.files = []
        caf.unpack(fm)
        return caf
    
    @staticmethod
    def from_binary_path(path: str, endian: EndianType):
        with open(path, "rb") as f:
            data = f.read()
        return CafFile.from_binary(data, endian)
    
    @staticmethod
    def from_dict_stripped(data: dict):
        return CafFile(data["unknown_1"], data["unknown_2"], data["unknown_3"])
    
    @staticmethod
    def from_json_stripped(data: str):
        return CafFile.from_dict_stripped(json.loads(data))
    
    @staticmethod
    def from_json_stripped_path(path: str):
        with open(path, "r") as f:
            data = f.read()
        return CafFile.from_json_stripped(data)