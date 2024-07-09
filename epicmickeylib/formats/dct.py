# epicmickeylib/formats/dct.py
#
# dialog container format used in both games

from epicmickeylib.internal.file_manipulator import EndianType, FileManipulator
from epicmickeylib.thirdparty.epic_mickey_hash import epic_mickey_hash
import xml.etree.ElementTree as ET
from xml.dom import minidom

class DCTLine:
    hashed_key:int
    text:str

    def __init__(self, hashed_key:int = 0, text:str = "") -> "DCTLine":
        self.hashed_key = hashed_key
        self.text = text

    def __str__(self) -> str:
        return self.text

class DCTFooterEntry:
    number:int
    text:str

    def __init__(self, number:int=0, text:str="") -> "DCTFooterEntry":
        self.number = number
        self.text = text
    
    def __str__(self) -> str:
        return self.text

class DCT:
    magic:str # = "DICT"
    version1:int
    hash_seed:int
    version2:int
    lines:list[DCTLine]
    footer_lines:list[DCTFooterEntry]

    def __init__(self, magic:str = "DICT", version1:int = 8192, hash_seed:int = 38400705, version2:int = 19, lines:list[DCTLine] = [], footer_lines:list[DCTFooterEntry]=[]):
        self.magic = magic
        self.version1 = version1
        self.hash_seed = hash_seed
        self.version2 = version2
        self.lines = lines
        self.footer_lines = footer_lines
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":

        self.magic = fm.r_str(4) # = "DICT"
        self.version1 = fm.r_u32() # = 8192
        self.hash_seed = fm.r_u32()
        self.version2 = fm.r_u32() # = 19
        
        line_count = fm.r_u32()

        # move forward 4 bytes
        fm.move(4)

        # read footer offset
        footer_offset = fm.tell() + fm.r_u32() + 9

        # read footer switch
        footer_switch = fm.r_u32()
        if footer_switch == 1:
            footer_switch = True
        else:
            footer_switch = False

        current_data_offset = fm.tell()

        self.lines = []
        # read lines
        for _ in range(line_count):
            # read line id (4 bytes)
            hashed_key = fm.r_u32()
            # if line id is 0, it is an empty line. add it to the lines and continue
            if hashed_key == 0:
                # move forward 8 bytes
                fm.move(8)
                self.lines.append(DCTLine())
                current_data_offset = fm.tell()
                continue
            line_offset = fm.tell() + fm.r_u32() + 1
            # read line zero
            line_zero = fm.r_u32()
            # set current data offset
            current_data_offset = fm.tell()
            # go to line offset
            fm.seek(line_offset)
            # read line - r_str_null(dct)
            line_text = fm.r_str_null()

            self.lines.append(DCTLine(hashed_key,line_text))

            # go to current data offset
            fm.seek(current_data_offset)
        
        if not footer_switch:
            return fm

        self.footer_lines = []
        while fm.tell() < footer_offset:
            footer_line_offset = fm.tell() + fm.r_u32() + 1
            footer_line_id = fm.r_u32()
            current_data_offset = fm.tell()

            fm.seek(footer_line_offset)

            footer_line_text = fm.r_str_null()

            # add footer line to footer
            self.footer_lines.append(DCTFooterEntry(footer_line_id, footer_line_text))
            # go to current data offset
            fm.seek(current_data_offset)

        return fm
    
    def pack(self) -> bytes:
        fm = FileManipulator(endian=EndianType.LITTLE)

        # get line count
        line_count = len(self.lines)
        # get footer line count
        footer_line_count = len(self.footer_lines)
        end_offset = (line_count * 12) + (footer_line_count * 8) - 1

        fm.w_str(self.magic)
        fm.w_u32(self.version1)
        fm.w_u32(self.hash_seed)
        fm.w_u32(self.version2)

        # write line count
        fm.w_u32(line_count)

        # write 1
        fm.w_u32(1)
        # write end offset
        fm.w_u32(end_offset)
        # if there are no footer lines, write 0 and continue
        if footer_line_count == 0:
            fm.w_u32(0)
        else:
            fm.w_u32(1)

        current_data_offset = fm.tell()
        current_line_offset = end_offset + 50
        # go to current line offset
        fm.seek(current_line_offset)
        # write null byte
        fm.write(b"\x00")
        # go to current data offset
        fm.seek(current_data_offset)
        # write lines
        for line in self.lines:
            # if line has no id, it is an empty line. write 0 and continue
            if line.hashed_key == 0:
                for _ in range(3):
                    fm.w_u32(0)
                current_data_offset = fm.tell()
                continue
            # parse unicode escape sequences

            # write line id
            fm.w_u32(line.hashed_key)
            # write line offset
            fm.w_u32(current_line_offset - fm.tell() - 1)
            # write line zero
            fm.w_u32(0)
            current_data_offset = fm.tell()
            fm.seek(current_line_offset)
            fm.w_str_null(line.text)
            current_line_offset = fm.tell()
            fm.seek(current_data_offset)
        
        if footer_line_count == 0:
            return fm.getbuffer()

        # write footer
        for footer_line in self.footer_lines:
            # write offset
            fm.w_u32(current_line_offset - fm.tell() - 1)
            # write id
            fm.w_u32(footer_line.number)
            current_data_offset = fm.tell()
            # go to current line offset
            fm.seek(current_line_offset)
            # write line
            fm.w_str_null(footer_line.text)
            # set current line offset
            current_line_offset = fm.tell()
            # go to current data offset
            fm.seek(current_data_offset)
        # write data end bytes
        # DF FF FF FF
        fm.write(b"\xdf\xff\xff\xff")
        fm.w_u32(11)
        fm.w_u32(12)
        fm.w_u32(0)

        return fm.getbuffer()
    
    def get_line_from_key(self, key:str=""):
        hashed_key = epic_mickey_hash(key.encode("utf-8"), self.hash_seed)
        for dct_line in self.lines:
            if dct_line.hashed_key == hashed_key:
                return dct_line
        return None
    
    def get_line_from_hash(self, hashed_key:int=0):
        for dct_line in self.lines:
            if dct_line.hashed_key == hashed_key:
                return dct_line
        return None
    
    def get_line_from_text(self, text:str=""):
        for dct_line in self.lines:
            if dct_line.text == text:
                return dct_line
        return None
    
    def remove_line_from_text(self, text:str=""):
        for dct_line in self.lines:
            if dct_line.text == text:
                self.lines.remove(dct_line)
                return True
        return False
    
    def to_xml(self, pretty:bool = True) -> str:
        root = ET.Element("DCT")
        root.set("version1", str(self.version1))
        root.set("hash_seed", str(self.hash_seed))
        root.set("version2", str(self.version2))
        lines = ET.SubElement(root, "Lines")
        for line in self.lines:
            dct_line = ET.SubElement(lines, "DCTLine")
            dct_line.set("hashed_key", str(line.hashed_key))
            dct_line.text = line.text
        footer = ET.SubElement(root, "Footer")
        for footer_line in self.footer_lines:
            dct_footer_line = ET.SubElement(footer, "DCTFooterLine")
            dct_footer_line.set("number", str(footer_line.number))
            dct_footer_line.text = footer_line.text
        string = ET.tostring(root, encoding="unicode")
        if pretty:
            string = minidom.parseString(string).toprettyxml(indent="    ")
        return string
    
    def to_xml_path(self, path:str, pretty:bool = True) -> None:
        with open(path, "w") as f:
            f.write(self.to_xml(pretty))
    
    def to_binary(self) -> bytes:
        return self.pack()
    
    def to_binary_path(self, path:str) -> None:
        with open(path, "wb") as f:
            f.write(self.to_binary())
    
    @staticmethod
    def from_binary(binary:bytes) -> "DCT":
        fm = FileManipulator(data=binary,endian=EndianType.LITTLE)
        dct = DCT()
        dct.lines = []
        dct.footer_lines = []
        dct.unpack(fm)
        return dct
    
    @staticmethod
    def from_binary_path(path:str) -> "DCT":
        with open(path, "rb") as f:
            return DCT.from_binary(f.read())
    
    @staticmethod
    def from_xml(xml:str) -> "DCT":
        root = ET.fromstring(xml)
        version1 = int(root.get("version1"))
        hash_seed = int(root.get("hash_seed"))
        version2 = int(root.get("version2"))
        lines = []
        footer_lines = []
        for line in root.find("Lines"):
            hashed_key = int(line.get("hashed_key"))
            text = line.text
            lines.append(DCTLine(hashed_key, text))
        for footer_line in root.find("Footer"):
            number = int(footer_line.get("number"))
            text = footer_line.text
            footer_lines.append(DCTFooterEntry(number, text))
        return DCT(version1=version1, hash_seed=hash_seed, version2=version2, lines=lines, footer_lines=footer_lines)
    
    @staticmethod
    def from_xml_path(path:str) -> "DCT":
        with open(path, "r") as f:
            xml = f.read()
        return DCT.from_xml(xml)