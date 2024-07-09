# epicmickeylib/formats/sdic.py
#
# format specific to the Japanese version of Epic Mickey 2 for Wii (why), similar to DCT but split up

from epicmickeylib.internal.file_manipulator import FileManipulator

class SDICLine:
    hashed_key:int
    text:str

    def __init__(self, hashed_key:int, text:str=""):
        self.hashed_key = hashed_key
        self.text = text

class SDICFile:
    lines:list[SDICLine]

    def __init__(self, lines:list[SDICLine]=[]):
        self.lines = lines
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        num_lines = fm.r_u32()
        for _ in range(num_lines):
            hashed_key = fm.r_u32()
            string_offset = fm.r_u32()
            pos = fm.tell()
            fm.seek(string_offset)
            string = fm.r_str_null(encoding="utf-8")
            self.lines.append(
                SDICLine(
                    hashed_key,
                    string
                )
            )
            fm.seek(pos)
        return fm
    
    @staticmethod
    def from_binary(binary:bytes) -> "SDICFile":
        sdic = SDICFile()
        fm = FileManipulator(binary)
        sdic.unpack(fm)
        return sdic
    
    @staticmethod
    def from_binary_path(path:str) -> "SDICFile":
        with open(path, "rb") as f:
            return SDICFile.from_binary(f.read())