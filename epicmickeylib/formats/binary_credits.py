from enum import Enum
from epicmickeylib.internal.file_manipulator import FileManipulator, EndianType

class CreditType(Enum):
    NAME = 0
    JOB_TITLE = 1
    UNKNOWN_ID_2 = 2
    STUDIO_NAME = 3
    UNKNOWN_ID_4 = 4
    UNKNOWN_ID_5 = 5
    SPACE = 6
    GLYPH = 7
    EMPTY = 8

class CreditEntry:
    credit_type:CreditType
    text:str

    def __init__(self, credit_type:CreditType = CreditType(0), text:str = ""):
        self.credit_type = credit_type
        self.text = text

class CreditsFile:
    credit_entries:list[CreditEntry]

    def __init__(self, credit_entries:list[CreditEntry]=[]):
        self.credit_entries = credit_entries
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        number_of_entries = fm.r_u32()
        for i in range(number_of_entries):
            fm.seek(4 + (i * 8))
            number = fm.r_u32()
            text_offset = fm.r_u32()
            fm.seek(text_offset)
            text = fm.r_str_null()
            self.credit_entries.append(
                CreditEntry (   
                    credit_type=CreditType(number),
                    text=text
                )
            )
        return fm
    
    @staticmethod
    def from_binary(binary:bytes) -> "CreditsFile":
        credits = CreditsFile()
        fm = FileManipulator(binary)
        credits.unpack(fm)
        return credits
    
    @staticmethod
    def from_binary_path(path:str) -> "CreditsFile":
        with open(path, "rb") as f:
            return CreditsFile.from_binary(f.read())