# epicmickeylib/formats/collectible_database.py
#
# container for collectible and extras data used in both games

from epicmickeylib.internal.file_manipulator import EndianType, FileManipulator
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import json

class Collectible:
    type:str
    dev_name:str
    icon_path:str

    def __init__(self, dev_name:str="", type:str="", icon_path:str=""):
        self.type = type
        self.dev_name = dev_name
        self.icon_path = icon_path
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.type = fm.r_str_jps()
        self.dev_name = fm.r_str_jps()
        self.icon_path = fm.r_str_jps()
        return fm
    
    def pack(self) -> bytes:
        fm:FileManipulator = FileManipulator()
        fm.w_str_jps(self.type)
        fm.w_str_jps(self.dev_name)
        fm.w_str_jps(self.icon_path)
        return fm.getbuffer()
    
    def __str__(self):
        string = ""
        string += "Collectible:\n"
        string += f"\ttype: {self.type}\n"
        string += f"\tdev_name: {self.dev_name}\n"
        string += f"\ticon_path: {self.icon_path}\n"
        return string

class Extra:
    global_state:str
    type:str
    thumbnail_path:str
    asset_path:str

    def __init__(self, global_state:str="", type:str="", thumbnail_path:str="", asset_path:str=""):
        self.global_state = global_state
        self.type = type
        self.thumbnail_path = thumbnail_path
        self.asset_path = asset_path
    
    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.global_state = fm.r_str_jps()
        self.type = fm.r_str_jps()
        self.thumbnail_path = fm.r_str_jps()
        self.asset_path = fm.r_str_jps()
        return fm
    
    def pack(self) -> bytes:
        fm:FileManipulator = FileManipulator()
        fm.w_str_jps(self.global_state)
        fm.w_str_jps(self.type)
        fm.w_str_jps(self.thumbnail_path)
        fm.w_str_jps(self.asset_path)
        return fm.getbuffer()
    
    def __str__(self):
        string = ""
        string += "Extra:\n"
        string += f"\tglobal_state: {self.global_state}\n"
        string += f"\ttype: {self.type}\n"
        string += f"\tthumbnail_path: {self.thumbnail_path}\n"
        string += f"\tasset_path: {self.asset_path}\n"
        return string

class CollectibleDatabase:
    version:int
    amount_of_collectibles:int
    collectibles:list[Collectible]
    extras:list[Extra]

    def __init__(self, version:int=3, collectibles:list[Collectible]=[], extras:list[Extra]=[]):
        self.version = version
        self.amount_of_collectibles = len(collectibles)
        self.collectibles = collectibles
        self.extras = extras

    def unpack(self, fm:FileManipulator) -> "FileManipulator":
        self.version = fm.r_u32()
        self.amount_of_collectibles = fm.r_u32()
        self.collectibles = []
        for _ in range(self.amount_of_collectibles):
            collectible = Collectible()
            fm = collectible.unpack(fm)
            self.collectibles.append(collectible)
        amount_of_extras = fm.r_u32()
        self.extras = []
        for _ in range(amount_of_extras):
            extra = Extra()
            fm = extra.unpack(fm)
            self.extras.append(extra)
    
    def pack(self, endian:EndianType=EndianType.BIG) -> bytes:
        fm:FileManipulator = FileManipulator(endian=endian)
        fm.w_u32(self.version)
        fm.w_u32(len(self.collectibles))
        for collectible in self.collectibles:
            fm.write(collectible.pack())
        fm.w_u32(len(self.extras))
        for extra in self.extras:
            fm.write(extra.pack())
        return fm.getbuffer()
    
    def __str__(self):
        string = ""
        string += "CollectibleDatabase:\n"
        string += f"\tversion: {self.version}\n"
        string += f"\tcollectibles ({len(self.collectibles)}):\n"
        for collectible in self.collectibles:
            collectible_string = str(collectible)
            lines = collectible_string.splitlines()
            for line in lines:
                string += f"\t\t{line}\n"
        string += f"\textras ({len(self.extras)}):\n"
        for extra in self.extras:
            extra_string = str(extra)
            lines = extra_string.splitlines()
            for line in lines:
                string += f"\t\t{line}\n"

        return string
    
    def to_xml(self, pretty:bool=True) -> str:
        root = Element("CollectibleDatabase")
        root.set("Version", str(self.version))
        collectibles = SubElement(root, "Collectibles")
        for collectible in self.collectibles:
            collectible_element = SubElement(collectibles, "Collectible")
            collectible_element.set("Type", str(collectible.type))
            collectible_element.set("DevName", str(collectible.dev_name))
            collectible_element.set("IconPath", str(collectible.icon_path))
        extras = SubElement(root, "Extras")
        for extra in self.extras:
            extra_element = SubElement(extras, "Extra")
            extra_element.set("GlobalState", str(extra.global_state))
            extra_element.set("Type", str(extra.type))
            extra_element.set("ThumbnailPath", str(extra.thumbnail_path))
            extra_element.set("AssetPath", str(extra.asset_path))
        string = tostring(root, encoding="unicode")
        if pretty:
            string = minidom.parseString(string).toprettyxml()
        return string
    
    def to_binary(self, endian:EndianType=EndianType.BIG) -> bytes:
        return self.pack(endian)
    
    def to_csv(self) -> tuple[str, str]:
        # COLLECTIBLES
        collectibles = "#DevName,Type,IconPath\n"

        quest_objects = []
        pins = []
        film_reels = []
        for collectible in self.collectibles:
            if collectible.type == "Quest_Object":
                quest_objects.append(collectible)
            elif collectible.type == "Pin":
                pins.append(collectible)
            elif collectible.type == "Film_Reel":
                film_reels.append(collectible)
        
        collectibles += "#QUEST_OBJECTS,,\n"
        for collectible in quest_objects:
            collectibles += f"{collectible.dev_name},{collectible.type},{collectible.icon_path}\n"
        collectibles += "#PIN,,\n"
        for collectible in pins:
            collectibles += f"{collectible.dev_name},{collectible.type},{collectible.icon_path}\n"
        collectibles += "#FILM_REELS,,\n"
        for collectible in film_reels:
            collectibles += f"{collectible.dev_name},{collectible.type},{collectible.icon_path}\n"

        # EXTRAS
        extras = "GlobalState,Type,ThumbnailPath,AssetPath\n"
        for extra in self.extras:
            extras += f"{extra.global_state},{extra.type},{extra.thumbnail_path},{extra.asset_path}\n"

        return collectibles, extras
    
    def to_json(self) -> str:
        # create a dictionary
        dictionary = {
            "version": self.version,
            "collectibles": [],
            "extras": []
        }
        for collectible in self.collectibles:
            dictionary["collectibles"].append({
                "type": collectible.type.text,
                "dev_name": collectible.dev_name.text,
                "icon_path": collectible.icon_path.text
            })
        for extra in self.extras:
            dictionary["extras"].append({
                "global_state": extra.global_state.text,
                "type": extra.type.text,
                "thumbnail_path": extra.thumbnail_path.text,
                "asset_path": extra.asset_path.text
            })
        # convert to json
        string = json.dumps(dictionary, indent=4)
        return string
    
    @staticmethod
    def from_binary(data:bytes, endian:EndianType=EndianType.BIG) -> "CollectibleDatabase":
        fm = FileManipulator(data, endian)
        collectible_database = CollectibleDatabase()
        collectible_database.unpack(fm)
        return collectible_database
    
    @staticmethod
    def from_binary_path(path:str, endian:EndianType=EndianType.BIG) -> "CollectibleDatabase":
        with open(path, "rb") as f:
            data = f.read()
        return CollectibleDatabase.from_binary(data, endian)
    
    @staticmethod
    def from_xml(xml:str) -> "CollectibleDatabase":
        root = Element.fromstring(xml)
        version = int(root.get("Version"))
        collectibles = []
        for collectible_element in root.find("Collectibles"):
            collectible = Collectible()
            collectible.set_type(collectible_element.get("Type"))
            collectible.set_dev_name(collectible_element.get("DevName"))
            collectible.set_icon_path(collectible_element.get("IconPath"))
            collectibles.append(collectible)
        extras = []
        for extra_element in root.find("Extras"):
            extra = Extra()
            extra.set_global_state(extra_element.get("GlobalState"))
            extra.set_type(extra_element.get("Type"))
            extra.set_thumbnail_path(extra_element.get("ThumbnailPath"))
            extra.set_asset_path(extra_element.get("AssetPath"))
            extras.append(extra)
        return CollectibleDatabase(version, collectibles, extras)
    
    @staticmethod
    def from_csv(collectibles_csv:str, extras_csv:str) -> "CollectibleDatabase":
        # collectibles
        collectibles = []
        for line in collectibles_csv.splitlines():
            if line.startswith("#"):
                continue
            split = line.split(",")
            collectible = Collectible()
            collectible.set_dev_name(split[0])
            collectible.set_type(split[1])
            collectible.set_icon_path(split[2])
            collectibles.append(collectible)
        # extras
        extras = []
        for line in extras_csv.splitlines():
            if line.startswith("#"):
                continue
            split = line.split(",")
            extra = Extra()
            extra.set_global_state(split[0])
            extra.set_type(split[1])
            extra.set_thumbnail_path(split[2])
            extra.set_asset_path(split[3])
            extras.append(extra)
        return CollectibleDatabase(3, collectibles, extras)
    
    @staticmethod
    def from_json(json_str:str) -> "CollectibleDatabase":
        # convert to dictionary
        dictionary = json.loads(json_str)
        # create collectibles
        collectibles = []
        for collectible in dictionary["collectibles"]:
            collectibles.append(Collectible(collectible["dev_name"], collectible["type"], collectible["icon_path"]))
        # create extras
        extras = []
        for extra in dictionary["extras"]:
            extras.append(Extra(extra["global_state"], extra["type"], extra["thumbnail_path"], extra["asset_path"]))
        # create collectible database
        return CollectibleDatabase(dictionary["version"], collectibles, extras)
    
    @staticmethod
    def from_xml_path(path:str) -> "CollectibleDatabase":
        with open(path, "r") as f:
            xml = f.read()
        return CollectibleDatabase.from_xml(xml)
    
    @staticmethod
    def from_csv_path(collectibles_path:str, extras_path:str) -> "CollectibleDatabase":
        with open(collectibles_path, "r") as f:
            collectibles_csv = f.read()
        with open(extras_path, "r") as f:
            extras_csv = f.read()
        return CollectibleDatabase.from_csv(collectibles_csv, extras_csv)
    
    @staticmethod
    def from_json_path(path:str) -> "CollectibleDatabase":
        with open(path, "r") as f:
            json_str = f.read()
        return CollectibleDatabase.from_json(json_str)