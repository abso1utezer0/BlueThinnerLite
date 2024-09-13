# epicmickeylib/formats/sequence_file.py
#
# cutscene format for both games
# WIP -- DO NOT USE

from epicmickeylib.internal.file_manipulator import FileManipulator

class Sequence:
    character:str
    area:str
    unknown_short1:int
    unknown_short2:int

    def __init__(self, character:str = "", area:str = "", unknown_short1:int = 0, unknown_short2:int = 0):
        self.character = character
        self.area = area
        self.unknown_short1 = unknown_short1
        self.unknown_short2 = unknown_short2
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.character = fm.r_str_j
    
class SequenceFile:
    magic:int
    sequence:Sequence

    def __init__(self, magic:int = 30, sequence:Sequence = Sequence()):
        self.magic = magic
        self.sequence = sequence
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.magic = fm.r_u32()
        self.sequence = Sequence()
        fm = self.sequence.unpack(fm)
        return fm
    
    def pack(self) -> bytes:
        fm = FileManipulator()
        fm.w_u32(self.magic)
        fm.write(self.sequence.pack())
        return fm.getbuffer()
    
    def __str__(self) -> str:
        return f"SequenceFile({self.magic}, {self.sequence})"
    
    @staticmethod
    def from_binary(data:bytes) -> "SequenceFile":
        fm = FileManipulator(data)
        sequence_file = SequenceFile()
        fm = sequence_file.unpack(fm)
        return sequence_file
    
    @staticmethod
    def from_binary_path(path:str) -> "SequenceFile":
        with open(path, "rb") as f:
            return SequenceFile.from_binary(f.read())