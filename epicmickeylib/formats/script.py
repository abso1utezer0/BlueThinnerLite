# epicmickeylib/formats/script.py
#
# (de)compiles EM1 lua scripts

import os
from epicmickeylib.internal.file_manipulator import FileManipulator
import random

class Script:
    text = None
    unluac_path = None
    luac_path = None

    def __init__(self, text: str = "", unluac_path: str = "unluac.jar", luac_path: str = "luac"):
        self.text = text
        self.unluac_path = unluac_path
        self.luac_path = luac_path
    
    def unpack(self, fm: FileManipulator) -> FileManipulator:
        data = fm.getbuffer().tobytes()
        # write the file
        with open(".temp.luac", "wb") as f:
            f.write(data)
        # decompile the file
        os.system(f"java -jar {self.unluac_path} .temp.luac > .temp.lua")
        # read the decompiled file
        with open(".temp.lua", "r") as f:
            self.text = f.read()
        
        # remove the temp files
        try:
            os.remove(".temp.luac")
            os.remove(".temp.lua")
        except PermissionError:
            pass
        return fm
    
    def pack(self, strip_debug_info: bool = True) -> bytes:
        # compile the text using the installed lua compiler
        with open(".temp.lua", "w") as f:
            f.write(self.text)
        # strip the debug info
        os.system(self.luac_path + f" -o .temp.luac {'-s' if strip_debug_info else ''} .temp.lua")
        with open(".temp.luac", "rb") as f:
            data = f.read()
        os.remove(".temp.lua")
        os.remove(".temp.luac")
        return data
    
    def to_text(self):
        return self.text
    
    def to_text_path(self, path):
        with open(path, "w") as f:
            f.write(self.text)
    
    def to_binary(self, strip_debug_info: bool = True):
        return self.pack(strip_debug_info)
    
    def to_binary_path(self, path, strip_debug_info: bool = True):
        with open(path, "wb") as f:
            f.write(self.to_binary(strip_debug_info))
    
    @staticmethod
    def from_text(text, unluac_path: str = "unluac.jar", luac_path: str = "luac"):
        return Script(text, unluac_path, luac_path)
    
    @staticmethod
    def from_text_path(path, unluac_path: str = "unluac.jar", luac_path: str = "luac"):
        with open(path, "r") as f:
            return Script(f.read(), unluac_path, luac_path)
    
    @staticmethod
    def from_binary(data, unluac_path: str = "unluac.jar", luac_path: str = "luac"):
        fm = FileManipulator(data)
        script = Script(unluac_path=unluac_path, luac_path=luac_path)
        fm = script.unpack(fm)
        return script
    
    @staticmethod
    def from_binary_path(path, unluac_path: str = "unluac.jar", luac_path: str = "luac"):
        with open(path, "rb") as f:
            return Script.from_binary(f.read(), unluac_path, luac_path)