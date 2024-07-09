# epicmickeylib/formats/packfile.py
#
# asset container format used in both Epic Mickey games
# file order DOES matter...

import json
import xml.dom.minidom
from epicmickeylib.formats.collectible_database import CollectibleDatabase
from epicmickeylib.formats.dct import DCT
from epicmickeylib.formats.script import Script
from epicmickeylib.formats.subtitle_file import SubtitleFile
from epicmickeylib.internal.file_manipulator import FileManipulator, EndianType
from epicmickeylib.formats.scene import SceneFile
# element tree is used for xml parsing
import xml.etree.ElementTree as ET
import zlib
import os.path

class EndianDependentString:
    text:str

    def __init__(self, text:str=""):
        self.text = text
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.text = fm.r_str(4)
        if fm.endian == EndianType.LITTLE:
            self.text = self.text[::-1]
        self.text = self.text.replace("\x00", "")
        return fm
    
    def pack(self, endian:EndianType) -> bytes:
        fm:FileManipulator = FileManipulator(endian=endian)

        string_to_write = self.text

        while len(string_to_write) < 4:
            string_to_write += "\0"

        if fm.endian == EndianType.LITTLE:
            string_to_write = string_to_write[::-1]
        fm.w_str(string_to_write)
        return fm.getbuffer()

    def __str__(self) -> str:
        return self.text

class VirtualFile:
    type:EndianDependentString
    compress:bool
    compression_level:int
    path:str
    data:bytes

    def __init__(self, type:EndianDependentString = EndianDependentString(), compress:bool = False, compression_level:int = 6, path:str = "", data:bytes=[]) -> "VirtualFile":
        self.type = type
        self.compress = compress
        self.compression_level = compression_level
        self.path = path
        self.data = data
    
    def get_data_str(self) -> str:
        # return the data as a string, 16 bytes per line, ints
        data_str = ""
        for i in range(len(self.data)):
            if i % 16 == 0:
                data_str += "\n"
            data_str += str(self.data[i]) + " "
        return data_str
    
    def get_compressed_data(self) -> bytes:
        if self.compress == True:
            return zlib.compress(self.data, self.compression_level)
        return self.data
    
    def get_assembled_data(self) -> bytes:
        data = self.get_compressed_data()
        # if the data is of type memoryview, convert it to bytes
        if type(data) == memoryview:
            data = bytes(data)
        while (len(data) % 32) != 0:
            data += b"\x00"
        return data

    def get_split_path(self) -> tuple[str, str]:
        return os.path.split(self.path)
    
    def get_real_data_size(self) -> int:
        return len(self.data)
    
    def get_compressed_data_size(self) -> int:
        return len(self.get_compressed_data())
    
    def get_aligned_data_size(self) -> int:
        return len(self.get_assembled_data())
    
    def __str__(self):
        string = \
        f"""\
        VirtualFile:
            type: {str(self.type)}
            path: {self.path}
            compress: {self.compress}\
        """
        return string
    
    def to_dict(self) -> dict:
        return {
            "type": str(self.type),
            "compress": self.compress,
            "compression_level": self.compression_level,
            "path": self.path,
            "data": self.get_data_str()
        }
    
    def to_dict_stripped(self) -> dict:
        return {
            "type": str(self.type),
            "compress": self.compress,
            "compression_level": self.compression_level,
            "path": self.path
        }


class Packfile:

    magic:str
    version:int
    files:list[VirtualFile]

    def __init__(self, magic:str = "PAK ", version:int = 2, files:list[VirtualFile] = []):
        self.magic = magic
        self.version = version
        self.files = files

    def unpack(self, fm:FileManipulator):
        self.magic = fm.r_str(4)
        if fm.endian == EndianType.BIG:
            self.magic = self.magic[::-1]
        self.version = fm.r_u32()
        zero = fm.r_u32()
        header_size = fm.r_u32()
        data_pointer = fm.r_u32()
        data_pointer += header_size
        current_data_positon = data_pointer
        fm.seek(header_size)
        num_files = fm.r_u32()
        string_pointer = (num_files * 24) + header_size + 4
        current_header_position = header_size + 4

        # go to current header position
        fm.seek(current_header_position)

        # loop through all files
        for _ in range(num_files):
            # get the real file size as a 4 byte int
            real_file_size = fm.r_u32()
            # get the compressed file size as a 4 byte int
            compressed_file_size = fm.r_u32()
            # get the aligned file size as a 4 byte int
            aligned_file_size = fm.r_u32()
            
            # read the folder pointer as a 4 byte int
            folder_pointer = fm.r_u32()
            # read the file type as a 4 byte string
            file_type = EndianDependentString()
            fm = file_type.unpack(fm)
            # read the file pointer as a 4 byte int
            file_pointer = fm.r_u32()

            # add the string pointer to the folder name pointer and the file name pointer
            folder_pointer += string_pointer
            file_pointer += string_pointer

            # set the current header position to the current position
            current_header_position = fm.tell()

            # go to the folder name pointer
            fm.seek(folder_pointer)
            # read the folder name as a null terminated string
            folder_name = fm.r_str_null()

            # go to the file name pointer
            fm.seek(file_pointer)
            # read the file name as a null terminated string
            file_name = fm.r_str_null()

            # combine the folder name and the file name
            path = ""
            if folder_name == "" or folder_name == None:
                path = file_name
            else:
                path = folder_name + "/" + file_name

            # go to the current data position
            fm.seek(current_data_positon)

            # read the data
            data = fm.read(compressed_file_size)

            compress = False
            # if the file is compressed, decompress it
            if compressed_file_size != real_file_size:
                compress = True
                data = zlib.decompress(data)
            
            self.files.append(
                VirtualFile (
                    type=file_type,
                    compress=compress,
                    path=path,
                    data=data
                )
            )

            # add the aligned file size to the current data position
            current_data_positon += aligned_file_size

            # go to the current header position
            fm.seek(current_header_position)

        return fm

    def pack(self, endian:EndianType) -> bytes:
        fm = FileManipulator(endian=endian)

        if endian == EndianType.LITTLE:
            fm.w_str(self.magic)
        else:
            fm.w_str(self.magic[::-1])
        
        # version
        fm.w_u32(self.version)

        # header zero
        fm.w_u32(0)

        # header size
        header_size = 32
        fm.w_u32(header_size)

        path_partition = b""

        filename_pointers = {}
        folder_pointers = {}

        for file in self.files:
            foldername, filename  = file.get_split_path()
            # if foldername is not in folder pointers, add it to the path partition and the folder pointers
            if foldername not in folder_pointers:
                folder_pointers[foldername] = len(path_partition)
                path_partition += foldername.encode("utf-8")
                path_partition += b"\0"
            # if filename is not in filename pointers, add it to the path partition and the filename pointers
            if filename not in filename_pointers:
                filename_pointers[filename] = len(path_partition)
                path_partition += filename.encode("utf-8")
                path_partition += b"\0"
        # header data pointer
        data_pointer = header_size + len(path_partition) + (len(self.files) * 24) + 4
        while data_pointer % 32 != 0:
            data_pointer += 1
        fm.w_u32(data_pointer - header_size)
        
        # go to the header size
        fm.seek(header_size)

        # number of files
        fm.w_u32(len(self.files))

        # loop through all the files
        for file in self.files:
            # get the folder pointer
            foldername, filename = file.get_split_path()
            folder_pointer = folder_pointers[foldername]
            file_pointer = filename_pointers[filename]
            # write the header values
            fm.w_u32(file.get_real_data_size())
            fm.w_u32(file.get_compressed_data_size())
            fm.w_u32(file.get_aligned_data_size())
            fm.w_u32(folder_pointer)
            fm.write(file.type.pack(fm.endian))
            fm.w_u32(file_pointer)
        
        # write the path partition
        fm.write(path_partition)

        # go to the header data pointer
        fm.seek(data_pointer)

        for file in self.files:
            fm.write(file.get_assembled_data())
        
        # return the binary data
        return fm.getbuffer()
    
    def get_file_from_offset(self, offset:int) -> VirtualFile:
        fm = FileManipulator()

        if self.endian == EndianType.LITTLE:
            fm.w_str(self.magic)
        else:
            fm.w_str(self.magic[::-1])
        
        # version
        fm.w_u32(self.version)

        # header zero
        fm.w_u32(0)

        # header size
        header_size = 32
        fm.w_u32(header_size)

        path_partition = b""

        filename_pointers = {}
        folder_pointers = {}

        for file in self.files:
            foldername, filename  = file.get_split_path()
            # if foldername is not in folder pointers, add it to the path partition and the folder pointers
            if foldername not in folder_pointers:
                folder_pointers[foldername] = len(path_partition)
                path_partition += foldername.encode("utf-8")
                path_partition += b"\0"
            # if filename is not in filename pointers, add it to the path partition and the filename pointers
            if filename not in filename_pointers:
                filename_pointers[filename] = len(path_partition)
                path_partition += filename.encode("utf-8")
                path_partition += b"\0"
        # header data pointer
        data_pointer = header_size + len(path_partition) + (len(self.files) * 24)
        while data_pointer % 32 != 0:
            data_pointer += 1
        fm.w_u32(data_pointer - header_size)
        
        # go to the header size
        fm.seek(header_size)

        # number of files
        fm.w_u32(len(self.files))

        # loop through all the files
        for file in self.files:
            # get the folder pointer
            foldername, filename = file.get_split_path()
            folder_pointer = folder_pointers[foldername]
            file_pointer = filename_pointers[filename]
            # write the header values
            fm.w_u32(file.get_real_data_size())
            fm.w_u32(file.get_compressed_data_size())
            fm.w_u32(file.get_aligned_data_size())
            fm.w_u32(folder_pointer)
            fm.write(file.type.pack(fm.endian))
            fm.w_u32(file_pointer)

        # write the path partition
        fm.write(path_partition)

        # go to the header data pointer
        fm.seek(data_pointer)

        for file in self.files:
            start_offset = fm.tell()
            fm.write(file.get_assembled_data())
            end_offset = fm.tell()
            if start_offset <= offset and end_offset >= offset:
                return file
        return None
    
    @staticmethod
    def format_path_for_comparison(path:str) -> str:
        path = path.lower().replace("\\", "/")
        if path.startswith("/"):
            path = path[1:]
        return path
    
    def do_operation_on_file(self, path:str, operation:callable) -> None:
        path = Packfile.format_path_for_comparison(path)
        for file in self.files:
            path2 = Packfile.format_path_for_comparison(file.path)
            if path == path2:
                return operation(file)

    def remove_file_from_path(self, path:str) -> None:
        def operation(file:VirtualFile) -> None:
            self.files.remove(file)
        self.do_operation_on_file(path, operation)
    
    def get_file_from_path(self, path:str) -> VirtualFile:
        def operation(file:VirtualFile) -> VirtualFile:
            return file
        return self.do_operation_on_file(path, operation)

    def update_file(self, new_file:VirtualFile) -> None:
        def operation(file:VirtualFile) -> None:
            file.data = new_file.data
            file.compress = new_file.compress
            file.compression_level = new_file.compression_level
            file.type = new_file.type
        self.do_operation_on_file(new_file.path, operation)
    
    def rename_file(self, old_path:str, new_path:str) -> None:
        def operation(file:VirtualFile) -> None:
            file.path = new_path
        self.do_operation_on_file(old_path, operation)
    
    def add_file_from_path(self, real_path:str, virtual_path:str, index_to_insert:int=-1) -> None:
        file = VirtualFile()
        file.path = virtual_path
        file.data = open(real_path, "rb").read()
        file.type = Packfile.determine_type_from_path(virtual_path)
        compress = Packfile.determine_compress_from_path(virtual_path)
        if compress == True:
            file.compress = True
            file.compression_level = 6
        if index_to_insert == -1:
            self.files.append(file)
        else:
            self.files.insert(index_to_insert, file)
    
    def get_data_from_path(self, path:str) -> bytes:
        def operation(file:VirtualFile) -> None:
            return file.data
        return self.do_operation_on_file(path, operation)

    def set_data_from_path(self, path:str, data:bytes) -> None:
        def operation(file:VirtualFile) -> None:
            file.data = data
        self.do_operation_on_file(path, operation)
    
    def get_type_from_path(self, path:str) -> EndianDependentString:
        def operation(file:VirtualFile) -> None:
            return file.type
        return self.do_operation_on_file(path, operation)
    
    def get_file_paths(self) -> list[str]:
        paths = []
        for file in self.files:
            paths.append(file.path)
        return paths
    
    def get_data_from_end_path(self, end_path:str) -> bytes:
        end_path = Packfile.format_path_for_comparison(end_path)
        for file in self.files:
            path = Packfile.format_path_for_comparison(file.path)
            if path.endswith(end_path):
                return file.data
    
    def to_binary(self, endian:EndianType=EndianType.BIG) -> bytes:
        return self.pack(endian=endian)
    
    def to_binary_path(self, binary_path:str, endian:EndianType=EndianType.BIG):
        binary = self.to_binary(endian=endian)
        with open(binary_path, "wb") as f:
            f.write(binary)

    def to_xml(self, pretty:bool=True) -> str:
        root = ET.Element("Packfile")
        root.set("version", str(self.version))

        for file in self.files:
            file_element = ET.SubElement(root, "VirtualFile")
            file_element.set("path", file.path)
            file_element.set("type", str(file.type))
            file_element.set("compress", str(file.compress))
            file_element.set("compression_level", str(file.compression_level))
            
            # set the text to the data
            file_element.text = file.get_data_str()
        
        string = ET.tostring(root, encoding="unicode", method="xml")
        if pretty == True:
            string = xml.dom.minidom.parseString(string).toprettyxml()
        return string
    
    def to_xml_path(self, xml_path:str, pretty:bool=True):
        xml_string = self.to_xml(pretty=pretty)
        with open(xml_path, "w") as f:
            f.write(xml_string)

    def to_xml_stripped(self, pretty:bool=True) -> str:
        root = ET.Element("PackfileStripped")
        root.set("version", str(self.version))

        for file in self.files:
            file_element = ET.SubElement(root, "VirtualFile")
            file_element.set("path", file.path)
            if str(file.type) != "":
                file_element.set("type", str(file.type))
            if file.compress != False:
                file_element.set("compress", str(file.compress))
            if file.compression_level != 6:
                file_element.set("compression_level", str(file.compression_level))
            
            # since this is a stripped xml, we don't need the data

        string = ET.tostring(root, encoding="unicode", method="xml")
        if pretty == True:
            string = xml.dom.minidom.parseString(string).toprettyxml()
        return string
    
    def to_xml_stripped_path(self, xml_path:str, pretty:bool=True):
        xml_string = self.to_xml_stripped(pretty=pretty)
        with open(xml_path, "w") as f:
            f.write(xml_string)
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "files": [file.to_dict() for file in self.files]
        }
    
    def to_json(self, pretty:bool=True) -> str:
        if pretty == True:
            return json.dumps(self.to_dict(), indent=4)
        return json.dumps(self.to_dict())
    
    def to_json_path(self, path:str, pretty:bool=True) -> None:
        with open(path, "w") as f:
            f.write(self.to_json(pretty=pretty))
    
    def to_dict_stripped(self) -> dict:
        return {
            "version": self.version,
            "files": [file.to_dict_stripped() for file in self.files]
        }
    
    def to_json_stripped(self, pretty:bool=True) -> str:
        if pretty == True:
            return json.dumps(self.to_dict_stripped(), indent=4)
        return json.dumps(self.to_dict_stripped())
    
    def to_json_stripped_path(self, path:str, pretty:bool=True) -> None:
        with open(path, "w") as f:
            f.write(self.to_json_stripped(pretty=pretty))
    
    @staticmethod
    def from_xml(xml_string:str) -> "Packfile":
        root = ET.fromstring(xml_string)
        # make sure the name of the root is Packfile
        if root.tag != "Packfile":
            raise Exception("The root tag of the xml must be Packfile")
        packfile = Packfile()
        packfile.version = int(root.get("version"))
        packfile.magic = EndianDependentString("PAK ")
        for file_element in root:
            file = VirtualFile()
            file.path = file_element.get("path")
            file.type = EndianDependentString(file_element.get("type"))
            file.compress = bool(file_element.get("compress"))
            file.compression_level = int(file_element.get("compression_level"))
            data_str = file_element.text
            data_str = data_str.replace("\n", "")
            data_str_list = data_str.split(" ")
            data = []
            for byte in data_str_list:
                if byte == "":
                    continue
                data.append(int(byte))
            file.data = bytes(data)
            packfile.files.append(file)
        return packfile
    
    @staticmethod
    def from_xml_path(xml_path:str) -> "Packfile":
        xml_string = open(xml_path, "r").read()
        return Packfile.from_xml(xml_string)
    
    @staticmethod
    def from_xml_stripped(xml_string:str, base_directory:str) -> "Packfile":
        root = ET.fromstring(xml_string)
        if root.tag != "PackfileStripped":
            raise Exception("The root tag of the xml must be PackfileStripped")
        packfile = Packfile()
        packfile.version = int(root.get("version"))
        packfile.magic = EndianDependentString(" KAP")
        for file_element in root:
            file = VirtualFile()
            file.path = file_element.get("path")

            # check if type is in the file element
            if "type" in file_element.attrib:
                file.type = EndianDependentString(file_element.get("type"))
            else:
                file.type = EndianDependentString("")

            if "compress" in file_element.attrib:
                file.compress = bool(file_element.get("compress"))
            else:
                file.compress = False

            if "compression_level" in file_element.attrib:
                file.compression_level = int(file_element.get("compression_level"))
            else:
                file.compression_level = 6

            # check if the file exists
            absolute_path = os.path.join(base_directory, file.path)
            extension = os.path.splitext(absolute_path)[1]
            decomped_paths = [absolute_path + ".xml", absolute_path + ".json"]
            decomped_path = ""
            data = b""
            decomped = False
            for path in decomped_paths:
                if os.path.exists(path):
                    decomped_path = path
                    decomped = True
                    data = open(decomped_path, "r").read()
                    break
            if decomped == False:
                data = open(absolute_path, "rb").read()
            if decomped == True:
                if extension == ".lua":
                    script = Script.from_text(data)
                    data = script.to_binary()
                elif extension == ".bin":
                    scene = SceneFile.from_json(data)
                    data = scene.to_binary()
                elif extension == ".clb":
                    clb = CollectibleDatabase.from_xml(data)
                    data = clb.to_binary()
                elif extension == ".sub":
                    sub = SubtitleFile.from_xml(data)
                    data = sub.to_binary()
                elif extension == ".dct":
                    dct = DCT.from_xml(data)
                    data = dct.to_binary()
                else:
                    raise Exception(f"Unknown extension {extension}")
            file.data = data
            packfile.files.append(file)
        return packfile
    
    @staticmethod
    def from_xml_stripped_path(xml_path:str, base_directory:str) -> "Packfile":
        xml_string = open(xml_path, "r").read()
        return Packfile.from_xml_stripped(xml_string, base_directory)
    
    @staticmethod
    def from_binary(binary:bytes) -> "Packfile":

        # determine the endian type
        endian = EndianType.BIG
        if binary[0:4] == b"PAK ":
            endian = EndianType.LITTLE

        fm = FileManipulator(data=binary, endian=endian)
        packfile = Packfile()
        packfile.files = []
        packfile.unpack(fm)
        return packfile
    
    @staticmethod
    def from_dict_stripped(dictionary, base_directory:str) -> "Packfile":
        packfile = Packfile()
        packfile.version = dictionary["version"]
        packfile.magic = EndianDependentString(" KAP")
        packfile.files = []
        for file_dict in dictionary["files"]:
            file = VirtualFile()
            file.path = file_dict["path"]
            file.type = EndianDependentString(file_dict["type"])
            file.compress = file_dict["compress"]
            file.compression_level = file_dict["compression_level"]
            absolute_path = os.path.join(base_directory, file.path)
            extension = os.path.splitext(absolute_path)[1]
            decomped_paths = [absolute_path + ".xml", absolute_path + ".json"]
            decomped_path = ""
            data = b""
            decomped = False
            for path in decomped_paths:
                if os.path.exists(path):
                    decomped_path = path
                    decomped = True
                    data = open(decomped_path, "r").read()
                    break
            if decomped == False:
                data = open(absolute_path, "rb").read()
            if decomped == True:
                if extension == ".lua":
                    script = Script.from_text(data)
                    data = script.to_binary()
                elif extension == ".bin":
                    scene = SceneFile.from_json(data)
                    data = scene.to_binary()
                elif extension == ".clb":
                    clb = CollectibleDatabase.from_xml(data)
                    data = clb.to_binary()
                elif extension == ".sub":
                    sub = SubtitleFile.from_xml(data)
                    data = sub.to_binary()
                elif extension == ".dct":
                    dct = DCT.from_xml(data)
                    data = dct.to_binary()
                else:
                    raise Exception(f"Unknown extension {extension}")
            file.data = data
            packfile.files.append(file)
        return packfile
    
    @staticmethod
    def from_json_stripped(json_str:str, base_directory:str) -> "Packfile":
        dictionary = json.loads(json_str)
        return Packfile.from_dict_stripped(dictionary, base_directory)
    
    @staticmethod
    def from_binary_path(binary_path:str) -> "Packfile":
        binary = open(binary_path, "rb").read()
        return Packfile.from_binary(binary)
    
    @staticmethod
    def determine_compress_from_path(path:str) -> bool:
        path = path.lower()
        if path.endswith(".bin") or path.endswith(".lua"):
            return True
        return False

    @staticmethod
    def determine_type_from_path(path:str) -> EndianDependentString:
        path = path.lower()
        if path.endswith(".bsq"):
            return EndianDependentString("BSQ")
        elif path.endswith(".nif") or path.endswith(".nif_wii"):
            return EndianDependentString("NIF")
        elif path.endswith(".kf") or path.endswith(".kf_wii"):
            return EndianDependentString("KF")
        elif path.endswith(".kfm") or path.endswith(".kfm_wii"):
            return EndianDependentString("KFM")
        elif path.endswith(".hkx") or path.endswith(".hkx_wii"):
            # if the path begins with characters/ but not characters/shared, is it HKB
            if path.startswith("characters/") and not path.startswith("characters/shared/"):
                return EndianDependentString("HKB")
            else:
                return EndianDependentString("HKX")
        elif path.endswith(".hkw"):
            return EndianDependentString("HKW")
        elif path.endswith(".lit_cooked"):
            return EndianDependentString("LIT")
        else:
            return EndianDependentString()
    
    @staticmethod
    def from_file_list(file_list:list[str], base_directory:str) -> "Packfile":
        packfile = Packfile(magic=EndianDependentString(" KAP"))
        packfile.files = []
        for file in file_list:
            virtual_file = VirtualFile()
            virtual_file.path = file
            virtual_file.data = open(os.path.join(base_directory, file), "rb").read()
            virtual_file.type = Packfile.determine_type_from_path(file)
            compress = Packfile.determine_compress_from_path(file)
            if compress == True:
                virtual_file.compress = True
                virtual_file.compression_level = 6
            packfile.files.append(virtual_file)
        return packfile
    
    @staticmethod
    def build_from_scene_path(scene_path:str, base_directory:str) -> "Packfile":
        referenced_paths = Packfile.get_list_from_scene_path(scene_path, base_directory)
        return Packfile.from_file_list(referenced_paths, base_directory)
    
    @staticmethod
    def get_list_from_scene_path(scene_path:str, base_directory:str, palette:bool=False) -> list[str]:
        # NOTE: Does not currently work :(
        absolute_scene_path = os.path.join(base_directory, scene_path)
        scene = SceneFile.from_path_auto(absolute_scene_path)

        bin_paths = []
        lua_paths = []
        bsq_paths = []
        collision_paths = []
        misc_paths = []

        def add_tex_paths_for_nif(nif_path:str):
            absolute_nif_path = os.path.join(base_directory, nif_path)
            # if the nif path doesnt exist add nif_wii to the end of the path
            if not os.path.exists(absolute_nif_path):
                absolute_nif_path = absolute_nif_path + "_wii"
            texture_paths = []
            # search for every occurence of "_tex.nif_wii" in the nif file
            indexes = []
            with open(absolute_nif_path, "rb") as f:
                data = f.read()
                index = 0
                while True:
                    index = data.find(b"_tex.nif", index)
                    if index == -1:
                        break
                    indexes.append(index)
                    index += 1
            fm = FileManipulator.from_path(absolute_nif_path, endian=EndianType.BIG)
            for index in indexes:
                fm.seek(index)
                # go back until we hit a null byte
                while True:
                    fm.seek(-2, 1)
                    if fm.r_u8() == 0:
                        break
                # go back until we hit a non null byte
                while True:
                    fm.seek(-2, 1)
                    if fm.r_u8() != 0:
                        break
                # read the u32
                length = fm.r_u32()
                # read the string
                string = fm.r_str(length).lower()
                # replace the \ with /
                string = string.replace("\\", "/")
                # remove the beginning / if it exists
                if string[0] == "/":
                    string = string[1:]
                # add the string to the texture paths
                if string not in misc_paths:
                    texture_paths.append(string)
            
            misc_paths.extend(texture_paths)
            misc_paths.append(nif_path)
                

        def is_not_in_paths(path) -> bool:
            paths_to_check = [bin_paths, lua_paths, bsq_paths, collision_paths, misc_paths]
            for paths in paths_to_check:
                if path.lower() in paths:
                    return False
            return True
        
        def add_assets_for_behavior_project(path:str):
            # get the base name of the path with no extension
            name = os.path.splitext(os.path.basename(path))[0]
            # get everything before behaviorproject
            name = name.split("behaviorproject")[0]
            # get the folder the file is in
            folder = os.path.dirname(path)
            if folder.endswith("animations"):
                return
            behaviors_folder = os.path.join(folder, "behaviors")
            characters_folder = os.path.join(folder, "characters")
            animations_folder = os.path.join(folder, "animations")
            # add animations/{name}_tpose.hkx
            misc_paths.append(os.path.join(animations_folder, name + "_tpose.hkx"))
            # add behaviors/{name}behaviorgraph.hkx
            misc_paths.append(os.path.join(behaviors_folder, name + "behaviorgraph.hkx"))
            # add chacaters/{name}.hkx
            misc_paths.append(os.path.join(characters_folder, name + ".hkx"))
            # add characters/{name}_rig_skin.hkx
            misc_paths.append(os.path.join(characters_folder, name + "_rig_skin.hkx"))

            misc_paths.append(path)
        
        def add_assets_for_anim_list(path:str):
            absolute_path = os.path.join(base_directory, path)
            # read the list as a text file, seperated by new lines
            anims = []
            with open(absolute_path, "r") as f:
                anims = f.read().split("\n")
            # get the folder the file is in
            folder = os.path.dirname(path)
            animations_folder = os.path.join(folder, "animations")
            # loop through all the animations
            for anim in anims:
                if anim.strip() == "":
                    continue
                # add animations/{anim}
                add_path(os.path.join(animations_folder, anim))
            misc_paths.append(path)

        def add_path(path:str):
            path = path.lower()
            if is_not_in_paths(path):
                if os.path.splitext(os.path.basename(path))[0].endswith("_static_hull"):
                    collision_paths.append(path)
                elif path.endswith(".bin"):
                    bin_paths.append(path)
                elif path.endswith(".lua"):
                    lua_paths.append(path)
                elif path.endswith(".bsq"):
                    bsq_paths.append(path)
                elif path.endswith(".nif"):
                    add_tex_paths_for_nif(path)
                elif path.endswith(".kfm"):
                    path2 = path.replace(".kfm", ".kf")
                    add_path(path2)
                    misc_paths.append(path)
                elif path.endswith(".hkx"):
                    # remove the extension
                    path_no_extension = os.path.splitext(path)[0]
                    # if it ends with behaviorproject
                    if path_no_extension.endswith("behaviorproject"):
                        add_assets_for_behavior_project(path)
                    else:
                        misc_paths.append(path)
                elif path.endswith(".hkw"):
                    add_assets_for_anim_list(path)
                else:
                    misc_paths.append(path)
        
        def add_palette(palette_name:str):
            palettes_folder = os.path.join(base_directory, "palettes")
            # search for the palette name (regardless of extension) in the palettes folder and all subfolders
            for root, dirs, files in os.walk(palettes_folder):
                for file in files:
                    # remove file extension
                    file_no_extension = os.path.splitext(file)[0]
                    if file_no_extension.lower() == palette_name.lower():
                        path = os.path.relpath(os.path.join(root, file), base_directory)
                        # replace the extension with .bin
                        path = os.path.splitext(path)[0] + ".bin"
                        palette_paths = Packfile.get_list_from_scene_path(path, base_directory, palette=True)
                        for palette_path in palette_paths:
                            add_path(palette_path)
                        add_path(path)

        for e in scene.objects.entities:
            for c in e.components:
                for p in c.properties:
                    if p.asset == True:
                        if isinstance(p.value, list):
                            for v in p.value:
                                add_path(v)
                        else:
                            add_path(p.value)
                    elif p.palette == True:
                        if isinstance(p.value, list):
                            for v in p.value:
                                add_palette(v)
                        else:
                            add_palette(p.value)
                    elif p.template == True:
                        if isinstance(p.value, list):
                            for v in p.value:
                                add_palette(v)
                        else:
                            add_palette(p.value)
        
        # reverse lua paths
        lua_paths.reverse()

        paths = []
        paths.append(scene_path)
        paths.extend(bin_paths)
        paths.extend(lua_paths)
        # get the path to the scene with no extension
        scene_path_no_extension = os.path.splitext(scene_path)[0]
        if palette == False:
            paths.append(scene_path_no_extension + ".lit_cooked")
        paths.extend(bsq_paths)
        paths.extend(collision_paths)

        paths.append("environments/_test/textures/boxout_paint_tex.nif")

        # add all textures in effects/r3mt
        effects_folder = os.path.join(base_directory, "effects")
        r3mt_folder = os.path.join(effects_folder, "r3mt")
        for root, dirs, files in os.walk(r3mt_folder):
            for file in files:
                if file.endswith("_tex.nif") or file.endswith("_tex.nif_wii"):
                    path = os.path.relpath(os.path.join(root, file), base_directory)
                    paths.append(path.replace("_wii", "").lower())

        paths.extend(misc_paths)

        # remove empty paths
        paths = list(filter(lambda x: x != "", paths))
        
        # make sure / is used instead of \
        paths = list(map(lambda x: x.replace("\\", "/"), paths))

        # remove any beginning slashes
        paths = list(map(lambda x: x.lstrip("/"), paths))

        # remove duplicates (delete last occurernce first)
        paths = list(dict.fromkeys(paths))

        new_paths = []
        for path in paths:
            # get the absolute path
            absolute_path = os.path.join(base_directory, path)
            # if the path exists, add it to the new paths
            if os.path.exists(absolute_path):
                new_paths.append(path)
            elif os.path.exists(absolute_path + "_wii"):
                new_paths.append(path + "_wii")

        return new_paths