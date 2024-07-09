# epicmickeylib/formats/subtitle_file.py
#
# format contains subtitle dialog keys and their start/end times

from epicmickeylib.internal.file_manipulator import EndianType, FileManipulator
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json

class SubtitleString:
    text:str

    def __init__(self, text:str=""):
        self.text = text
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.text = fm.r_str(0x44).replace("\0", "")
        return fm
    
    def pack(self) -> bytes:
        fm:FileManipulator = FileManipulator()
        fm.w_str(self.text)
        fm.pad(0x44)
        return fm.getbuffer()

    def __str__(self):
        return self.text

class Subtitle:
    version:int
    translation_key:SubtitleString
    # start time and end time are either an int for version 1 or a float for version 2
    start_time:int | float
    end_time:int | float

    def __init__(self, version:int=1, translation_key:str="", start_time:int | float=0, end_time:int | float=0):
        self.version = version
        self.translation_key = SubtitleString(translation_key)
        self.start_time = start_time
        self.end_time = end_time
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        fm = self.translation_key.unpack(fm)
        if self.version == 1:
            self.start_time = fm.r_u32()
            self.end_time = fm.r_u32()
        elif self.version == 2:
            self.start_time = fm.r_float()
            self.end_time = fm.r_float()
        return fm

    def pack(self, endian:EndianType=EndianType.BIG) -> bytes:
        fm:FileManipulator = FileManipulator(endian=endian)
        fm.write(self.translation_key.pack())
        if self.version == 1:
            fm.w_u32(self.start_time)
            fm.w_u32(self.end_time)
        elif self.version == 2:
            fm.w_float(self.start_time)
            fm.w_float(self.end_time)
        return fm.getbuffer()
    
    def to_dict(self) -> dict:
        return {
            "translation_key": self.translation_key.text,
            "start_time": self.start_time,
            "end_time": self.end_time
        }
    
    def __str__(self):
        string = ""

        string += "Subtitle:\n"
        string += f"\ttranslation_key: {self.translation_key}\n"
        string += f"\tstart_time: {self.start_time}\n"
        string += f"\tend_time: {self.end_time}\n"

        return string

class SubtitleFile:
    version:int
    subtitles:list[Subtitle]

    def __init__(self, version:int=1, subtitles:list[Subtitle]=[]):
        self.version = version
        self.subtitles = subtitles
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        amount_to_read = int(fm.size() / 76)
        for _ in range(amount_to_read):
            subtitle:Subtitle = Subtitle(version=self.version)
            fm = subtitle.unpack(fm)
            self.subtitles.append(subtitle)
        return fm
    
    def pack(self, endian:EndianType=EndianType.BIG) -> bytes:
        fm:FileManipulator = FileManipulator(endian=endian)
        for subtitle in self.subtitles:
            fm.write(subtitle.pack(endian=endian))
        return fm.getbuffer()
    
    def __str__(self) -> str:
        string = ""
        string += "SubtitleFile:\n"
        string += f"\tsubtitles ({len(self.subtitles)}):\n"
        for subtitle in self.subtitles:
            subtitle_string = str(subtitle)
            lines = subtitle_string.splitlines()
            for line in lines:
                string += f"\t\t{line}\n"
        return string
    
    def get_sorted_subtitles(self) -> list[Subtitle]:
        return sorted(self.subtitles, key=lambda subtitle: subtitle.start_time)
    
    def to_xml(self, pretty:bool=False) -> str:
        root = ET.Element("SubtitleFile")
        root.set("version", str(self.version))
        for subtitle in self.subtitles:
            subtitle_element = ET.SubElement(root, "Subtitle")
            subtitle_element.set("translation_key", subtitle.translation_key.text)
            subtitle_element.set("start_time", str(subtitle.start_time))
            subtitle_element.set("end_time", str(subtitle.end_time))
        
        string = ET.tostring(root, encoding="unicode")
        if pretty:
            string = minidom.parseString(string).toprettyxml(indent="    ")
        return string
    
    def to_xml_path(self, path:str, pretty:bool=False) -> None:
        with open(path, "w") as f:
            f.write(self.to_xml(pretty=pretty))
    
    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "subtitles": [subtitle.to_dict() for subtitle in self.subtitles]
        }
    
    def to_json(self, pretty:bool=False) -> str:
        if pretty:
            return json.dumps(self.to_dict(), indent=4)
        return json.dumps(self.to_dict())
    
    def to_json_path(self, path:str, pretty:bool=False) -> None:
        with open(path, "w") as f:
            f.write(self.to_json(pretty=pretty))
    
    def to_binary(self, endian:EndianType=EndianType.BIG) -> bytes:
        fm:FileManipulator = FileManipulator(endian=endian)
        fm.write(self.pack(endian=endian))
        return fm.getbuffer()
    
    def to_binary_path(self, path:str, endian:EndianType=EndianType.BIG) -> None:
        with open(path, "wb") as f:
            f.write(self.to_binary(endian=endian))
    
    @staticmethod
    def from_xml(xml:str) -> "SubtitleFile":
        root = ET.fromstring(xml)
        version = int(root.get("version"))
        subtitles = []
        for subtitle_element in root:
            translation_key = subtitle_element.get("translation_key")
            start_time = subtitle_element.get("start_time")
            end_time = subtitle_element.get("end_time")
            if version == 1:
                start_time = int(start_time)
                end_time = int(end_time)
            elif version == 2:
                start_time = float(start_time)
                end_time = float(end_time)
            subtitle = Subtitle(version=version, translation_key=translation_key, start_time=start_time, end_time=end_time)
            subtitles.append(subtitle)
        return SubtitleFile(version=version, subtitles=subtitles)
    
    @staticmethod
    def from_xml_path(path:str) -> "SubtitleFile":
        with open(path, "r") as f:
            xml = f.read()
        return SubtitleFile.from_xml(xml=xml)
    
    @staticmethod
    def from_dict(dictionary:dict) -> "SubtitleFile":
        version = dictionary["version"]
        subtitles = []
        for subtitle_dict in dictionary["subtitles"]:
            translation_key = subtitle_dict["translation_key"]
            start_time = subtitle_dict["start_time"]
            end_time = subtitle_dict["end_time"]
            subtitle = Subtitle(version=version, translation_key=translation_key, start_time=start_time, end_time=end_time)
            subtitles.append(subtitle)
        return SubtitleFile(version=version, subtitles=subtitles)
    
    @staticmethod
    def from_json(json_str:str) -> "SubtitleFile":
        dictionary = json.loads(json_str)
        return SubtitleFile.from_dict(dictionary=dictionary)
    
    @staticmethod
    def from_json_path(path:str) -> "SubtitleFile":
        with open(path, "r") as f:
            json_str = f.read()
        return SubtitleFile.from_json(json_str=json_str)
    
    @staticmethod
    def from_binary(binary:bytes, endian:EndianType=EndianType.BIG, version:int=1) -> "SubtitleFile":
        fm = FileManipulator(data=binary, endian=endian)
        subtitle_file = SubtitleFile(version=version)
        subtitle_file.subtitles = []
        fm = subtitle_file.unpack(fm)
        return subtitle_file
    
    @staticmethod
    def from_binary_path(path:str, endian:EndianType=EndianType.BIG, version:int=1) -> "SubtitleFile":
        with open(path, "rb") as f:
            binary = f.read()
        return SubtitleFile.from_binary(binary=binary, endian=endian, version=version)