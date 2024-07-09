# epicmickeylib/formats/sequence_file.py
#
# cutscene format for both games
# WIP -- DO NOT USE

from epicmickeylib.internal.file_manipulator import FileManipulator

class Sequence:
    sequence_name:str
    character_name:str
    area_name:str
    unknown_short1:int
    unknown_short2:int
    entries:list

    def __init__(self, sequence_name:str = "", character_name:str = "", area_name:str = "", unknown_short1:int = 0, unknown_short2:int = 0, entries:list = []):
        self.sequence_name = sequence_name
        self.character_name = character_name
        self.area_name = area_name
        self.unknown_short1 = unknown_short1
        self.unknown_short2 = unknown_short2
        self.entries = entries

    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.sequence_name = fm.r_str_jps()
        self.character_name = fm.r_str_jps()
        self.area_name = fm.r_str_jps()
        self.unknown_short1 = fm.r_u16_jps()
        self.unknown_short2 = fm.r_u16_jps()
        self.entries = []
        for _ in range(fm.r_u32()):
            sequence_entry = SequenceEntry()
            fm = sequence_entry.unpack(fm)
            self.entries.append(sequence_entry)
        return fm

    def pack(self) -> bytes:
        fm = FileManipulator()
        fm.w_str_jps(self.sequence_name)
        fm.w_str_jps(self.character_name)
        fm.w_str_jps(self.area_name)
        fm.w_u16_jps(self.unknown_short1)
        fm.w_u16_jps(self.unknown_short2)
        fm.w_u32(len(self.entries))
        for entry in self.entries:
            fm.write(entry.pack())
        return fm.getbuffer()
    
    def __str__(self):
        return f"Sequence({self.sequence_name}, {self.character_name}, {self.area_name}, {self.unknown_short1}, {self.unknown_short2}, {self.entries})"

class Bark: # ID 0
    string1:str
    name1:str
    name2:str
    target_entity:str
    dialog_key:str
    string2:str
    string3:str
    sfx_name:str
    string4:str
    boolean1:bool

    def __init__(self, string1:str = "", name1:str = "", name2:str = "", target_entity:str = "", dialog_key:str = "", string2:str = "", string3:str = "", sfx_name:str = "", string4:str = "", boolean1:bool = False):
        self.string1 = string1
        self.name1 = name1
        self.name2 = name2
        self.target_entity = target_entity
        self.dialog_key = dialog_key
        self.string2 = string2
        self.string3 = string3
        self.sfx_name = sfx_name
        self.string4 = string4
        self.boolean1 = boolean1
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.string1 = fm.r_str_jps()
        self.name1 = fm.r_str_jps()
        self.name2 = fm.r_str_jps()
        self.target_entity = fm.r_str_jps()
        self.dialog_key = fm.r_str_jps()
        self.string2 = fm.r_str_jps()
        self.string3 = fm.r_str_jps()
        self.sfx_name = fm.r_str_jps()
        self.string4 = fm.r_str_jps()
        self.boolean1 = fm.r_bool()
        return fm
    
    def pack(self) -> bytes:
        fm = FileManipulator()
        fm.w_str_jps(self.string1)
        fm.w_str_jps(self.name1)
        fm.w_str_jps(self.name2)
        fm.w_str_jps(self.target_entity)
        fm.w_str_jps(self.dialog_key)
        fm.w_str_jps(self.string2)
        fm.w_str_jps(self.string3)
        fm.w_str_jps(self.sfx_name)
        fm.w_str_jps(self.string4)
        fm.w_bool(self.boolean1)
        return fm.getbuffer()
    
    def __str__(self):
        return f"Bark({self.string1}, {self.name1}, {self.name2}, {self.target_entity}, {self.dialog_key}, {self.string2}, {self.string3}, {self.sfx_name}, {self.string4}, {self.boolean1})"

class Unknown2: # ID 2
    string1:str
    short1:int # mode 1
    short2:int # mode 0
    short3:int # mode 0


class Subsequence: # ID 6
    string1:str
    short1:int

    def __init__(self, string1:str = "", short1:int = 0, sequence = Sequence()):
        self.string1 = string1
        self.short1 = short1
        self.sequence = sequence
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.string1 = fm.r_str_jps()
        self.short1 = fm.r_u16_jps()
        self.sequence = Sequence()
        fm = self.sequence.unpack(fm)
        return fm
    
    def pack(self) -> bytes:
        fm = FileManipulator()
        fm.w_str_jps(self.string1)
        fm.w_u16_jps(self.short1)
        fm.write(self.sequence.pack())
        return fm.getbuffer()
    
    def __str__(self):
        return f"Subsequence({self.string1}, {self.short1}, {self.sequence})"

class Unknown7: # ID 7
    string1:str
    string2:str
    string3:str
    boolean1:bool
    short1:int
    boolean2:bool

    def __init__(self, string1:str = "", string2:str = "", string3:str = "", boolean1:bool = False, short1:int = 0, boolean2:bool = False):
        self.string1 = string1
        self.string2 = string2
        self.string3 = string3
        self.boolean1 = boolean1
        self.short1 = short1
        self.boolean2 = boolean2
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.string1 = fm.r_str_jps()
        self.string2 = fm.r_str_jps()
        self.string3 = fm.r_str_jps()
        self.boolean1 = fm.r_bool()
        self.short1 = fm.r_u16_jps()
        self.boolean2 = fm.r_bool()
        return fm
    
    def pack(self) -> bytes:
        fm = FileManipulator()
        fm.w_str_jps(self.string1)
        fm.w_str_jps(self.string2)
        fm.w_str_jps(self.string3)
        fm.w_bool(self.boolean1)
        fm.w_u16_jps(self.short1)
        fm.w_bool(self.boolean2)
        return fm.getbuffer()
    
    def __str__(self):
        return f"Unknown7({self.string1}, {self.string2}, {self.string3}, {self.boolean1}, {self.short1}, {self.boolean2})"

class Script: # ID 9
    string1:str
    script:str

    def __init__(self, string1:str = "", script:str = ""):
        self.string1 = string1
        self.script = script
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.string1 = fm.r_str_jps()
        self.script = fm.r_str_jps()
        return fm
    
    def pack(self) -> bytes:
        fm = FileManipulator()
        fm.w_str_jps(self.string1)
        fm.w_str_jps(self.script)
        return fm.getbuffer()

    def __str__(self):
        return f"Script({self.string1}, {self.script})"

class SequenceEntry:
    id:int
    data:object

    def __init__(self, id:int = 0, data:object = None):
        self.id = id
        self.data = data
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.id = fm.r_u16_jps()
        data = None
        if self.id == 0:
            data = Bark()
        elif self.id == 6:
            data = Subsequence()
        elif self.id == 7:
            data = Unknown7()
        elif self.id == 9:
            data = Script()
        else:
            # stop the unpacking
            return fm
        fm = data.unpack(fm)
        self.data = data
        return fm
    
    def __str__(self) -> str:
        return f"SequenceEntry({self.id}, {self.data})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
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