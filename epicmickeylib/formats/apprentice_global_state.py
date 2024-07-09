from epicmickeylib.internal.file_manipulator import FileManipulator

class ApprenticeGlobalStateEntry:
    text:str
    id:int
    number:int
    boolean:bool

    def __init__(self, text:str="", id:int=0, number:int=0, boolean:bool=False):
        self.text = text
        self.id = id
        self.number = number
        self.boolean = boolean
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.text = fm.r_str_jps()
        self.id = fm.r_u16()
        fm.move(2) # skip the CD CD filler bytes
        self.number = fm.r_u16()
        fm.move(2) # skip the FF FF filler bytes
        self.boolean = fm.r_bool()
        return fm
    
    def pack(self) -> bytes:
        fm:FileManipulator = FileManipulator()
        fm.w_str_jps(self.text)
        fm.w_u16(self.id)
        fm.write(b"\xCD\xCD")
        fm.w_u16(self.number)
        fm.write(b"\xFF\xFF")
        fm.w_bool(self.boolean)
        return fm.getbuffer()
    
    def __str__(self):
        string = ""
        string += "ApprenticeGlobalStateEntry:\n"
        string += f"\ttext: {self.text}\n"
        string += f"\tid: {self.id}\n"
        string += f"\tnumber: {self.number}\n"
        string += f"\tboolean: {self.boolean}\n"
        return string

class ApprenticeGlobalState:
    magic:int
    highest_id:int
    entries:list[ApprenticeGlobalStateEntry]

    def update_highest_id(self):
        self.highest_id = 0
        for entry in self.entries:
            if entry.id > self.highest_id:
                self.highest_id = entry.id

    def __init__(self, magic:int=30, entries:list[ApprenticeGlobalStateEntry]=[]):
        self.magic = magic  
        self.entries = entries
        self.update_highest_id()

    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.magic = fm.r_u32()
        self.highest_id = fm.r_u16()
        fm.move(2) # skip the CD CD filler bytes
        while fm.tell() != fm.size():
            entry = ApprenticeGlobalStateEntry()
            fm = entry.unpack(fm)
            self.entries.append(entry)
        return fm
    
    def pack(self) -> bytes:
        self.update_highest_id()
        fm:FileManipulator = FileManipulator()
        fm.w_u32(self.magic)
        fm.w_u16(self.highest_id)
        fm.write(b"\xCD\xCD")
        for entry in self.entries:
            fm.write(entry.pack())
        return fm.getbuffer()
    
    def __str__(self) -> str:
        string = ""
        string += "ApprenticeGlobalState:\n"
        string += f"\tentries ({len(self.entries)}):\n"
        for entry in self.entries:
            entry_string = str(entry)
            lines = entry_string.splitlines()
            for line in lines:
                string += f"\t\t{line}\n"
        return string