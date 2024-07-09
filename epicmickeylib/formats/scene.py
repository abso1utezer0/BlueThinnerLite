# epicmickeylib/formats/scene.py
#
# Scene/palette format used in both games, contains game objects and their properties

import json
import math
from xml.etree import ElementTree
from epicmickeylib.internal.file_manipulator import FileManipulator, EndianType
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def stringify_float(f:float) -> str:
    string = f"{f:.16f}"

    return string

# version enum
class SceneFileVersion:
    VERSION_1 = 1 # EM1 and early EM2 prototypes
    VERSION_2_PROTOTYPE = 2 # some EM2 prototypes
    VERSION_2 = 3 # later EM2 prototypes and EM2

class Point2:
    x:float
    y:float

    def __init__(self, x:float = 0.0, y:float = 0.0):
        self.x = x
        self.y = y
    
    def unpack(self, fm:FileManipulator):
        self.x = fm.r_float()
        self.y = fm.r_float()
        return fm
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_float(self.x)
        fm.w_float(self.y)
        return fm.getbuffer()
    
    def __str__(self):
        return f"({self.x}, {self.y})"
    
    def __repr__(self):
        return f"Point2({self.x}, {self.y})"
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def to_tuple(self):
        return (self.x, self.y)
    
    def to_list(self):
        return [self.x, self.y]
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}
    
    def to_xml(self) -> str:
        return f"{self.x}, {self.y}"
    
    @staticmethod
    def from_xml(xml:str):
        # remove whitespace and split the values
        data = xml.replace(" ", "").split(",")
        x = float(data[0])
        y = float(data[1])
        return Point2(x, y)
    
    @staticmethod
    def from_dict(d:dict):
        return Point2(d["x"], d["y"])

class Point3:
    x:float
    y:float
    z:float

    def __init__(self, x:float = 0.0, y:float = 0.0, z:float = 0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def unpack(self, fm:FileManipulator):
        self.x = fm.r_float()
        self.y = fm.r_float()
        self.z = fm.r_float()
        return fm
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_float(self.x)
        fm.w_float(self.y)
        fm.w_float(self.z)
        return fm.getbuffer()
    
    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"
    
    def __repr__(self):
        return f"Point3({self.x}, {self.y}, {self.z})"
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash((self.x, self.y, self.z))
    
    def to_tuple(self):
        return (self.x, self.y, self.z)
    
    def to_list(self):
        return [self.x, self.y, self.z]
    
    def to_dict(self):
        return {"x": self.x, "y": self.y, "z": self.z}
    
    def to_xml(self):
        return f"{self.x}, {self.y}, {self.z}"
    
    @staticmethod
    def from_xml(xml:str):
        # remove whitespace and split the values
        data = xml.replace(" ", "").split(",")
        x = float(data[0])
        y = float(data[1])
        z = float(data[2])
        return Point3(x, y, z)
    
    @staticmethod
    def from_dict(d:dict):
        return Point3(d["x"], d["y"], d["z"])

class Matrix3:
    m00:float
    m01:float
    m02:float
    m10:float
    m11:float
    m12:float
    m20:float
    m21:float
    m22:float

    def __init__(self, m00:float = 1.0, m01:float = 0.0, m02:float = 0.0, m10:float = 0.0, m11:float = 1.0, m12:float = 0.0, m20:float = 0.0, m21:float = 0.0, m22:float = 1.0):
        self.m00 = m00
        self.m01 = m01
        self.m02 = m02
        self.m10 = m10
        self.m11 = m11
        self.m12 = m12
        self.m20 = m20
        self.m21 = m21
        self.m22 = m22
    
    def unpack(self, fm:FileManipulator):
        self.m00 = fm.r_float()
        self.m01 = fm.r_float()
        self.m02 = fm.r_float()
        self.m10 = fm.r_float()
        self.m11 = fm.r_float()
        self.m12 = fm.r_float()
        self.m20 = fm.r_float()
        self.m21 = fm.r_float()
        self.m22 = fm.r_float()
        return fm
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_float(self.m00)
        fm.w_float(self.m01)
        fm.w_float(self.m02)
        fm.w_float(self.m10)
        fm.w_float(self.m11)
        fm.w_float(self.m12)
        fm.w_float(self.m20)
        fm.w_float(self.m21)
        fm.w_float(self.m22)
        return fm.getbuffer()
    
    def __str__(self):
        return f"({self.m00}, {self.m01}, {self.m02}, {self.m10}, {self.m11}, {self.m12}, {self.m20}, {self.m21}, {self.m22})"
    
    def __repr__(self):
        return f"Matrix3({self.m00}, {self.m01}, {self.m02}, {self.m10}, {self.m11}, {self.m12}, {self.m20}, {self.m21}, {self.m22})"
    
    def to_tuple(self):
        return (self.m00, self.m01, self.m02, self.m10, self.m11, self.m12, self.m20, self.m21, self.m22)
    
    def to_list(self):
        return [self.m00, self.m01, self.m02, self.m10, self.m11, self.m12, self.m20, self.m21, self.m22]
    
    def to_dict(self):
        return {
            "m" : [
                [self.m00, self.m01, self.m02],
                [self.m10, self.m11, self.m12],
                [self.m20, self.m21, self.m22]
            ]
        }
    
    def to_degrees(self) -> list:
        # convert the matrix to degrees
        x = math.degrees(math.atan2(self.m21, self.m22))
        y = math.degrees(math.atan2(-self.m20, math.sqrt(self.m21**2 + self.m22**2)))
        z = math.degrees(math.atan2(self.m10, self.m00))
        return [x, y, z]
    
    def to_xml(self):
        # 3 ROWs

        # ROW 1 <ROW> m00, m01, m02 </ROW>
        row1 = Element("ROW")
        row1.text = f"{stringify_float(self.m00)}, {stringify_float(self.m01)}, {stringify_float(self.m02)}"
        # ROW 2 <ROW> m10, m11, m12 </ROW>
        row2 = Element("ROW")
        row2.text = f"{stringify_float(self.m10)}, {stringify_float(self.m11)}, {stringify_float(self.m12)}"
        # ROW 3 <ROW> m20, m21, m22 </ROW>
        row3 = Element("ROW")
        row3.text = f"{stringify_float(self.m20)}, {stringify_float(self.m21)}, {stringify_float(self.m22)}"
        

        string = tostring(row1) + tostring(row2) + tostring(row3)
        return string

    @staticmethod
    def from_degrees(x:float, y:float, z:float):
        # convert the degrees to matrix
        x = -math.radians(x)
        y = -math.radians(y)
        z = math.radians(z)
        # create the matrix
        m00 = math.cos(y) * math.cos(z)
        m01 = math.cos(x) * math.sin(z) + math.sin(x) * math.sin(y) * math.cos(z)
        m02 = math.sin(x) * math.sin(z) - math.cos(x) * math.sin(y) * math.cos(z)
        m10 = -math.cos(y) * math.sin(z)
        m11 = math.cos(x) * math.cos(z) - math.sin(x) * math.sin(y) * math.sin(z)
        m12 = math.sin(x) * math.cos(z) + math.cos(x) * math.sin(y) * math.sin(z)
        m20 = math.sin(y)
        m21 = -math.sin(x) * math.cos(y)
        m22 = math.cos(x) * math.cos(y)
        return Matrix3(m00, m01, m02, m10, m11, m12, m20, m21, m22)
    
    @staticmethod
    def from_xml(xml:str):
        # 3 ROWs

        # get the rows thru ElementTree
        data = ElementTree.fromstring(xml)
        row1 = data.find("ROW")
        row2 = data.find("ROW[2]")
        row3 = data.find("ROW[3]")

        # remove whitespace from the rows and split them
        row1 = row1.text.replace(" ", "").split(",")
        row2 = row2.text.replace(" ", "").split(",")
        row3 = row3.text.replace(" ", "").split(",")

        # get the values from the rows
        m00 = float(row1[0])
        m01 = float(row1[1])
        m02 = float(row1[2])
        m10 = float(row2[0])
        m11 = float(row2[1])
        m12 = float(row2[2])
        m20 = float(row3[0])
        m21 = float(row3[1])
        m22 = float(row3[2])

        return Matrix3(m00, m01, m02, m10, m11, m12, m20, m21, m22)

    @staticmethod
    def from_dict(d:dict):
        # get the values from the dict
        m00 = d["m"][0][0]
        m01 = d["m"][0][1]
        m02 = d["m"][0][2]
        m10 = d["m"][1][0]
        m11 = d["m"][1][1]
        m12 = d["m"][1][2]
        m20 = d["m"][2][0]
        m21 = d["m"][2][1]
        m22 = d["m"][2][2]
        return Matrix3(m00, m01, m02, m10, m11, m12, m20, m21, m22)

class ColorRGB:
    r:float
    g:float
    b:float

    def __init__(self, r:float = 1.0, g:float = 1.0, b:float = 1.0):
        self.r = r
        self.g = g
        self.b = b
    
    def unpack(self, fm:FileManipulator):
        self.r = fm.r_float()
        self.g = fm.r_float()
        self.b = fm.r_float()
        return fm
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_float(self.r)
        fm.w_float(self.g)
        fm.w_float(self.b)
        return fm.getbuffer()
    
    def __str__(self):
        return f"({self.r}, {self.g}, {self.b})"
    
    def __repr__(self):
        return f"ColorRGB({self.r}, {self.g}, {self.b})"
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash((self.r, self.g, self.b))
    
    def to_tuple(self):
        return (self.r, self.g, self.b)
    
    def to_list(self):
        return [self.r, self.g, self.b]
    
    def to_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b}
    
    def to_xml(self):
        return f"{self.r}, {self.g}, {self.b}"
    
    def to_int(self):
        return int(self.r * 255) << 16 | int(self.g * 255) << 8 | int(self.b * 255)
    
    def to_hex(self):
        return hex(self.to_int())
    
    @staticmethod
    def from_hex(hex:str):
        return ColorRGB.from_int(int(hex, 16))
    
    @staticmethod
    def from_xml(xml:str):
        # remove whitespace and split the values
        data = xml.replace(" ", "").split(",")
        r = float(data[0])
        g = float(data[1])
        b = float(data[2])
        return ColorRGB(r, g, b)
    
    @staticmethod
    def from_int(i:int):
        r = (i >> 16) & 0xFF
        g = (i >> 8) & 0xFF
        b = i & 0xFF
        return ColorRGB(r / 255, g / 255, b / 255)
    
    @staticmethod
    def from_ints(r:int, g:int, b:int):
        r /= 255
        g /= 255
        b /= 255
        return ColorRGB(r, g, b)

    @staticmethod
    def from_dict(d:dict):
        return ColorRGB(d["r"], d["g"], d["b"])

class ColorRGBA:
    r:float
    g:float
    b:float
    a:float

    def __init__(self, r:float = 1.0, g:float = 1.0, b:float = 1.0, a:float = 1.0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
    
    def unpack(self, fm:FileManipulator):
        self.r = fm.r_float()
        self.g = fm.r_float()
        self.b = fm.r_float()
        self.a = fm.r_float()
        return fm
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_float(self.r)
        fm.w_float(self.g)
        fm.w_float(self.b)
        fm.w_float(self.a)
        return fm.getbuffer()
    
    def __str__(self):
        return f"({self.r}, {self.g}, {self.b}, {self.a})"
    
    def __repr__(self):
        return f"ColorRGBA({self.r}, {self.g}, {self.b}, {self.a})"
    
    def __eq__(self, other):
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash((self.r, self.g, self.b, self.a))
    
    def to_tuple(self):
        return (self.r, self.g, self.b, self.a)
    
    def to_list(self):
        return [self.r, self.g, self.b, self.a]
    
    def to_dict(self):
        return {"r": self.r, "g": self.g, "b": self.b, "a": self.a}

    def to_xml(self):
        return f"{self.r}, {self.g}, {self.b}, {self.a}"

    def to_int(self):
        return int(self.r * 255) << 24 | int(self.g * 255) << 16 | int(self.b * 255) << 8 | int(self.a * 255)
    
    def to_hex(self):
        return hex(self.to_int())
    
    @staticmethod
    def from_int(i:int):
        r = (i >> 24) & 0xFF
        g = (i >> 16) & 0xFF
        b = (i >> 8) & 0xFF
        a = i & 0xFF
        return ColorRGBA(r / 255, g / 255, b / 255, a / 255)
    
    @staticmethod
    def from_ints(r:int, g:int, b:int, a:int):
        # translate from ints to floats
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        a = int(a * 255)
        return ColorRGBA(r, g, b, a)
    
    @staticmethod
    def from_rgb(color:ColorRGB):
        return ColorRGBA(color.r, color.g, color.b, 1.0)
    
    @staticmethod
    def from_hex(hex:str):
        return ColorRGBA.from_int(int(hex, 16))
    
    @staticmethod
    def from_xml(xml:str):
        # remove whitespace and split the values
        data = xml.replace(" ", "").split(",")
        r = float(data[0])
        g = float(data[1])
        b = float(data[2])
        a = float(data[3])
        return ColorRGBA(r, g, b, a)

    @staticmethod
    def from_dict(d:dict):
        return ColorRGBA(d["r"], d["g"], d["b"], d["a"])

class ID:
    num:int

    def __init__(self, num:int = 0):
        self.num = num
    
    def to_str(self, length:int = 4, fill=True) -> str:
        # convert the number to hex
        hex_num = hex(self.num)[2:]
        # add 0s to the front of the hex number until it is the correct length
        while len(hex_num) < (length * 2):
            hex_num = "0" + hex_num
        # split the hex number into groups of 2
        hex_num = [hex_num[i:i+2] for i in range(0, len(hex_num), 2)]
        if fill == False:
            new_hex_num = []
            for entry in hex_num:
                # if the first character is 0, remove it
                if entry[0] == "0":
                    entry = entry[1]
                new_hex_num.append(entry)
            hex_num = new_hex_num
        # get the string of the list (, seperated)
        hex_num = ",".join(hex_num)
        # return the string
        return hex_num
    
    def to_bytes(self, length:int = 4, endian:EndianType = EndianType.BIG) -> bytes:
        # convert the number to bytes
        fm = FileManipulator(endian=endian)
        if length == 4:
            fm.w_u32(self.num)
        elif length == 8:
            fm.w_u64(self.num)
        elif length == 16:
            fm.w_u128(self.num)
        else:
            raise Exception("Invalid ID length")
        # return the bytes
        return fm.getbuffer()
    
    def __str__(self):
        return self.to_str()
    
    def __int__(self):
        return self.num

    @staticmethod
    def from_str(s:str):
        # remove whitespace and split the values
        data = s.replace(" ", "").split(",")
        fm = FileManipulator(endian=EndianType.BIG)
        for d in data:
            fm.w_u8(int(d, 16))
        
        fm.seek(0)
        
        num = 0
        if len(data) == 4:
            num = fm.r_u32()
        elif len(data) == 8:
            num = fm.r_u64()
        elif len(data) == 16:
            num = fm.r_u128()
        else:
            raise Exception("Invalid ID length")
        
        return ID(num)
    
    @staticmethod
    def from_int(i:int):
        return ID(i)
    
    @staticmethod
    def from_bytes(b:bytes):
        # convert to a list of hex strings
        hex_num = ",".join([hex(b[i])[2:] for i in range(len(b))])
        # return the ID from the hex string
        return ID.from_str(hex_num)

class EntityPointer:
    ref_link_id:ID

    def __init__(self, ref_link_id:ID = ID()):
        self.ref_link_id = ref_link_id
    
    def unpack(self, fm:FileManipulator):
        self.ref_link_id = ID.from_int(fm.r_u32())
        return fm
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        fm.w_u32(self.ref_link_id.num)
        return fm.getbuffer()
    
    def __str__(self):
        return f"{self.ref_link_id}"
    
    def __repr__(self):
        return f"EntityPointer({self.ref_link_id})"
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash(self.ref_link_id)

class Property:
    class_name:str
    name:str
    asset:bool
    palette:bool
    template:bool
    value:object

    def __init__(self, class_name:str = "", name:str = "", asset:bool = False, palette:bool = False, template:bool = False, value:object = None):
        self.class_name = class_name
        self.name = name
        self.asset = asset
        self.palette = palette
        self.template = template
        self.value = value

    def to_xml(self) -> str:
        # <PROPERTY Class="class_name" Name="name"> value </PROPERTY>
        property = Element("PROPERTY")
        property.set("Class", self.class_name)
        property.set("Name", self.name)
        if self.asset == True:
            property.set("Asset", "TRUE")
        if self.palette == True:
            property.set("Palette", "TRUE")
        if self.template == True:
            property.set("Template", "TRUE")
        
        stuff_to_run_thru = []
        list_mode = False

        # if the value is a list, add values to stuff_to_run_thru and set list_mode to True
        if isinstance(self.value, list):
            stuff_to_run_thru = self.value
            list_mode = True
        else:
            stuff_to_run_thru.append(self.value)
        
        for v in stuff_to_run_thru:
            # if list_mode is True, set the xml object to a new ITEM, otherwise set it to PROPERTY
            item = SubElement(property, "ITEM") if list_mode else property
            # if its an entity pointer, set the RefLinkID attribute
            if isinstance(v, EntityPointer):
                if v.ref_link_id.num == 0:
                    item.set("RefLinkID", "NULL")
                elif v.ref_link_id != None:
                    item.set("RefLinkID", str(v.ref_link_id))
                # continue to the next value
                continue
            # otherwise, set the text to the value
            try:
                if self.class_name == "Matrix3":
                    matrix_list = v.to_list()
                    # add a subelement for each row
                    for i in range(3):
                        row = SubElement(item, "ROW")
                        row.text = f"{matrix_list[i*3]}, {matrix_list[i*3+1]}, {matrix_list[i*3+2]}"
                else:
                    item.text = v.to_xml()
            except:
                if v != None:
                    if v.__class__.__name__ == "bool":
                        item.text = "TRUE" if v else "FALSE"
                    else:
                        item.text = str(v)
        
        # if list mode is true but the list is empty, add an empty ITEM
        if list_mode and len(stuff_to_run_thru) == 0:
            SubElement(property, "ITEM")
        
        return tostring(property)
    
    @staticmethod
    def get_json_for_value(class_name:str, value:object):
        if class_name == "Entity Pointer":
            return value.ref_link_id.num
        elif class_name in [
            "Float",
            "Unsigned Integer",
            "Integer",
            "Unsigned Short",
            "Short",
            "Boolean",
            "String"
        ]:
            return value
        else:
            return value.to_dict()
    
    def to_dict(self):
        json_data = {}
        json_data["class"] = self.class_name
        json_data["name"] = self.name
        json_data["asset"] = self.asset
        json_data["palette"] = self.palette
        json_data["template"] = self.template
        if isinstance(self.value, list):
            json_data["value"] = [self.get_json_for_value(self.class_name, v) for v in self.value]
        else:
            json_data["value"] = self.get_json_for_value(self.class_name, self.value)
        return json_data
    
    def unpack_value(self, fm:FileManipulator, version:int = SceneFileVersion.VERSION_1):
        value = None
        if self.class_name == "Entity Pointer":
            value = EntityPointer()
            fm = value.unpack(fm)
        elif self.class_name == "Color (RGB)":
            value = ColorRGB()
            fm = value.unpack(fm)
        elif self.class_name == "Color (RGBA)":
            value = ColorRGBA()
            fm = value.unpack(fm)
        elif self.class_name == "Point2":
            value = Point2()
            fm = value.unpack(fm)
        elif self.class_name == "Point3":
            value = Point3()
            fm = value.unpack(fm)
        elif self.class_name == "Matrix3":
            value = Matrix3()
            fm = value.unpack(fm)
        elif self.class_name == "Boolean":
            value = fm.r_bool()
        elif self.class_name == "Integer":
            value = fm.r_s32()
        elif self.class_name == "Unsigned Integer":
            value = fm.r_u32()
        elif self.class_name == "Float":
            value = fm.r_float()
        elif self.class_name == "String":
            pointer = fm.r_u32()
            if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
                pointer += 4
            pos = fm.tell()
            fm.seek(pointer)
            value = fm.r_str_jps()
            fm.seek(pos)
        elif self.class_name == "Short":
            value = fm.r_s16()
            fm.move(2)
        elif self.class_name == "Unsigned Short":
            value = fm.r_u16()
            fm.move(2)
        else:
            raise Exception(f"Unknown data type: {self.class_name}")

        return fm, value

    def pack_value(self, value, strings_offsets:dict, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        if self.class_name == "Entity Pointer":
            fm.write(value.pack(endian=endian))
        elif self.class_name == "Color (RGB)":
            fm.write(value.pack(endian=endian))
        elif self.class_name == "Color (RGBA)":
            fm.write(value.pack(endian=endian))
        elif self.class_name == "Point2":
            fm.write(value.pack(endian=endian))
        elif self.class_name == "Point3":
            fm.write(value.pack(endian=endian))
        elif self.class_name == "Matrix3":
            fm.write(value.pack(endian=endian))
        elif self.class_name == "Boolean":
            fm.w_bool(value)
        elif self.class_name == "Integer":
            fm.w_s32(value)
        elif self.class_name == "Unsigned Integer":
            fm.w_u32(value)
        elif self.class_name == "Float":
            fm.w_float(value)
        elif self.class_name == "String":
            pointer = strings_offsets[value]
            fm.w_u32(pointer)
        elif self.class_name == "Short":
            fm.w_s16(value)
            fm.write(b"\xCD\xCD")
        elif self.class_name == "Unsigned Short":
            fm.w_u16(value)
            fm.write(b"\xCD\xCD")
        else:
            raise Exception(f"Unknown data type: {self.class_name}")
        
        return fm.getbuffer()
    
    def unpack(self, fm:FileManipulator, version:int = SceneFileVersion.VERSION_1):
        # read the class name
        name_pointer = fm.r_u32()
        class_name_pointer = fm.r_u32()
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            name_pointer += 4
            class_name_pointer += 4

        pos = fm.tell()

        
        fm.seek(name_pointer)
        self.name = fm.r_str_jps()

        fm.seek(class_name_pointer)
        self.class_name = fm.r_str_jps()


        fm.seek(pos)
        
        data_type = fm.r_u32()

        list_mode = False

        if data_type == 1:
            list_mode = True
        if data_type == 2:
            self.asset = True
        elif data_type == 3:
            self.asset = True
            list_mode = True
        elif data_type == 4:
            self.palette = True
        elif data_type == 5:
            self.template = True
            list_mode = True
        
        amount = fm.r_u32()

        if amount == 0 and list_mode:
            self.value = []
            return fm
        
        values = []
        for _ in range(amount):
            fm, value = self.unpack_value(fm, version=version)
            values.append(value)

        if not list_mode:
            self.value = values[0]
        else:
            self.value = values
        
        return fm
    
    def pack(self, strings_offsets:dict, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        
        # write the name
        fm.w_u32(strings_offsets[self.name])
        # write the class name
        fm.w_u32(strings_offsets[self.class_name])
        # write the data type
        data_type = 0
        # if its a list but not an asset, set the data type to 1
        if (isinstance(self.value, list) == True) and (self.asset == False) and (self.palette == False) and (self.template == False):
            data_type = 1
        # if its not a list but an asset, set the data type to 2
        elif (isinstance(self.value, list) == False) and (self.asset == True):
            data_type = 2
        # if its a list and an asset, set the data type to 3
        elif (isinstance(self.value, list) == True) and (self.asset == True):
            data_type = 3
        elif self.palette:
            data_type = 4
        elif self.template:
            data_type = 5
        fm.w_u32(data_type)
        # write the amount of values
        amount = 1
        if isinstance(self.value, list):
            amount = len(self.value)
        fm.w_u32(amount)
        # write the values
        if isinstance(self.value, list):
            for v in self.value:
                fm.write(self.pack_value(v, strings_offsets, endian=endian))
        else:
            fm.write(self.pack_value(self.value, strings_offsets, endian=endian))
        return fm.getbuffer()
    
    @staticmethod
    def from_xml(xml:str):
        # load the xml using ElementTree
        property = ElementTree.fromstring(xml)

        # get the class name
        class_name = property.get("Class")
        # get the name
        name = property.get("Name")
        # get the asset
        asset = property.get("Asset") == "TRUE"
        # get the palette
        palette = property.get("Palette") == "TRUE"
        # get the template
        template = property.get("Template") == "TRUE"
        # get the value
        value = None

        list_mode = False
        # if the property has a child ITEM, set list_mode to True
        if property.find("ITEM") != None:
            list_mode = True
        
        value = []

        elements_to_run_thru = []
        # if list_mode is True, set the elements to run thru to the ITEMs
        if list_mode:
            elements_to_run_thru = property.findall("ITEM")
        else:
            elements_to_run_thru.append(property)
        
        for item in elements_to_run_thru:
            # run thru data types using the class name
            # if the class name is EntityPointer, set the value to an EntityPointer
            if class_name == "Entity Pointer":

                #value.append(EntityPointer(int(item.get("RefLinkID"))))
                if item.get("RefLinkID") == "NULL":
                    value.append(EntityPointer(ID(0)))
                else:
                    value.append(EntityPointer(ID.from_str(item.get("RefLinkID"))))
            elif class_name == "Color (RGB)":
                value.append(ColorRGB.from_xml(item.text))
            elif class_name == "Color (RGBA)":
                value.append(ColorRGBA.from_xml(item.text))
            elif class_name == "Point2":
                value.append(Point2.from_xml(item.text))
            elif class_name == "Point3":
                value.append(Point3.from_xml(item.text))
            elif class_name == "Matrix3":
                # if there are ROWs, set the value to a Matrix3
                value.append(Matrix3.from_xml(tostring(item)))
            elif class_name == "Boolean":
                value.append(item.text == "TRUE")
            elif class_name == "Integer":
                value.append(int(item.text))
            elif class_name == "Unsigned Integer":
                value.append(int(item.text))
            elif class_name == "Float":
                value.append(float(item.text))
            elif class_name == "String":
                value.append(item.text)
            elif class_name == "Short":
                value.append(int(item.text))
            elif class_name == "Unsigned Short":
                value.append(int(item.text))

        # if list_mode is False, set the value to the first item in the list
        if not list_mode:
            value = value[0]
        
        return Property(class_name, name, asset, palette, template, value)
    
    @staticmethod
    def get_value_from_json(class_name:str, value:object):
        if class_name == "Entity Pointer":
            return EntityPointer(ID(value))
        elif class_name == "Color (RGB)":
            return ColorRGB.from_dict(value)
        elif class_name == "Color (RGBA)":
            return ColorRGBA.from_dict(value)
        elif class_name == "Point2":
            return Point2.from_dict(value)
        elif class_name == "Point3":
            return Point3.from_dict(value)
        elif class_name == "Matrix3":
            return Matrix3.from_dict(value)
        elif class_name == "Boolean":
            return value
        elif class_name == "Integer":
            return value
        elif class_name == "Unsigned Integer":
            return value
        elif class_name == "Float":
            return value
        elif class_name == "String":
            return value
        elif class_name == "Short":
            return value
        elif class_name == "Unsigned Short":
            return value
        else:
            raise Exception(f"Unknown data type: {class_name}")
    
    @staticmethod
    def from_dict(d:dict):
        class_name = d["class"]
        name = d["name"]
        asset = d["asset"]
        palette = d["palette"]
        template = d["template"]
        value = None
        if isinstance(d["value"], list):
            value = [Property.get_value_from_json(class_name, v) for v in d["value"]]
        else:
            value = Property.get_value_from_json(class_name, d["value"])
        return Property(class_name, name, asset, palette, template, value)

    def __str__(self):
        return f"Property(class_name={self.class_name}, name={self.name}, asset={self.asset}, palette={self.palette}, template={self.template}, value={self.value})"

class Component:
    class_name:str
    name:str
    template_id:ID
    link_id:ID
    master_link_id:ID
    properties:list[Property]

    def __init__(self, class_name:str = "", name:str = "", template_id:ID = ID(), link_id:ID = ID(), master_link_id:ID = ID(), properties:list[Property] = []):
        self.class_name = class_name
        self.name = name
        self.template_id = template_id
        self.link_id = link_id
        self.master_link_id = master_link_id
        self.properties = properties
    
    def unpack(self, fm:FileManipulator, version:int = SceneFileVersion.VERSION_1):
        class_name_pointer = fm.r_u32()
        template_id_pointer = fm.r_u32()
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            class_name_pointer += 4
            template_id_pointer += 4
        pos = fm.tell()
        fm.seek(class_name_pointer)
        self.class_name = fm.r_str_jps()
        fm.seek(template_id_pointer)
        template_id = fm.r_str_jps()
        self.template_id = ID.from_str(template_id)
        fm.seek(pos)
        self.link_id = ID.from_int(fm.r_u32())
        self.master_link_id = ID.from_int(fm.r_u32())
        # if master link id is 0, set it to None
        if self.master_link_id.num == 0:
            self.master_link_id = None
        amount = fm.r_u32()
        self.properties = []
        for _ in range(amount):
            property = Property()
            property.unpack(fm, version=version)
            self.properties.append(property)
        self.fill_name_from_class_name()
        return fm
    
    def pack(self, strings_offsets:dict, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        # write the class name
        fm.w_u32(strings_offsets[self.class_name])
        # write the template id
        fm.w_u32(strings_offsets[self.template_id.to_str(fill=False)])
        # write the link id
        fm.w_u32(self.link_id.num)
        # write the master link id
        if self.master_link_id == None:
            fm.w_u32(0)
        else:
            fm.w_u32(self.master_link_id.num)
        # write the amount of properties
        fm.w_u32(len(self.properties))
        # write the properties
        for p in self.properties:
            fm.write(p.pack(strings_offsets, endian=endian))
        return fm.getbuffer()
    
    def fill_name_from_class_name(self):
        mapping = {
            "NiTransformationComponent": "Transformation",
            "JPSTransformationComponent": "Transformation",
            "NiSceneGraphComponent": "Scene Graph",
            "JPSSceneGraphComponent": "Scene Graph",
            "NiLightComponent": "Light",
            "JPSLightComponent": "Light",
            "NiCameraComponent": "Camera",
            "JPSCameraComponent": "Camera"
        }
        if self.class_name in mapping:
            self.name = mapping[self.class_name]
        else:
            self.name = "unknown"
    
    def to_xml(self):
        # create the component
        component = Element("COMPONENT")
        # set the class name
        component.set("Class", self.class_name)
        # set the name (if it exists)
        if self.name != "":
            component.set("Name", self.name)
        # set the template id
        component.set("TemplateID", str(self.template_id))
        # set the link id
        component.set("LinkID", str(self.link_id))
        # set the master link id
        if self.master_link_id != None:
            component.set("MasterLinkID", str(self.master_link_id))
        # add the properties
        for p in self.properties:
            component.append(ElementTree.fromstring(p.to_xml()))
        # return the xml
        return tostring(component)
    
    def to_dict(self):
        json_data = {}
        json_data["class_name"] = self.class_name
        json_data["name"] = self.name
        json_data["template_id"] = str(self.template_id)
        json_data["link_id"] = self.link_id.num
        if self.master_link_id != None and self.master_link_id.num != 0:
            json_data["master_link_id"] = self.master_link_id.num
        json_data["properties"] = [p.to_dict() for p in self.properties]
        return json_data
    
    @staticmethod
    def from_xml(xml:str):
        # load the xml using ElementTree
        component = ElementTree.fromstring(xml)

        # get the class name
        class_name = component.get("Class")
        # get the name
        name = component.get("Name")
        # get the template id
        template_id = ID.from_str(component.get("TemplateID"))
        # get the link id
        link_id = ID.from_str(component.get("LinkID"))
        # get the master link id if it exists
        master_link_id = None
        if component.get("MasterLinkID") != None:
            master_link_id = ID.from_str(component.get("MasterLinkID"))
        # get the properties
        properties = []
        for p in component.findall("PROPERTY"):
            properties.append(Property.from_xml(tostring(p)))
        
        return Component(class_name, name, template_id, link_id, master_link_id, properties)
    
    @staticmethod
    def from_dict(d:dict):
        class_name = d["class_name"]
        name = d["name"]
        template_id = ID.from_str(d["template_id"])
        link_id = ID.from_int(d["link_id"])
        if "master_link_id" in d:
            master_link_id = ID.from_int(d["master_link_id"])
        else:
            master_link_id = None
        properties = [Property.from_dict(p) for p in d["properties"]]
        return Component(class_name, name, template_id, link_id, master_link_id, properties)

    def __str__(self):
        return f"Property(class_name={self.class_name}, name={self.name}, template_id={self.template_id}, link_id={self.link_id}, master_link_id={self.master_link_id}, properties={self.properties})"

class Entity:
    class_name:str
    name:str
    link_id:ID
    master_link_id:ID
    unknown:int
    unknown_em2:int
    components:list[Component]

    def __init__(self, class_name:str = "JPSGeneralEntity", name:str = "", link_id:ID = ID(), master_link_id:ID = ID(), unknown:int = 0, unknown_em2:int = 0, components:list[Component] = []):
        self.class_name = class_name
        self.name = name
        self.link_id = link_id
        self.master_link_id = master_link_id
        self.unknown = unknown
        self.unknown_em2 = unknown_em2
        self.components = components
    
    def fill_class_name(self):
        self.class_name = "JPSGeneralEntity"
    
    def unpack(self, fm:FileManipulator, version:int = SceneFileVersion.VERSION_1):
        name_pointer = fm.r_u32()
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            name_pointer += 4
        pos = fm.tell()
        fm.seek(name_pointer)
        self.name = fm.r_str_jps()
        fm.seek(pos)
        self.link_id = ID.from_int(fm.r_u32())
        self.master_link_id = ID.from_int(fm.r_u32())
        if self.master_link_id.num == 0:
            self.master_link_id = None
        self.unknown = fm.r_u32()
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            self.unknown_em2 = fm.r_u32()
        amount = fm.r_u32()
        self.components = []
        for _ in range(amount):
            component = Component()
            component.unpack(fm, version=version)
            self.components.append(component)
        return fm
    
    def pack(self, strings_offsets:dict, endian:EndianType = EndianType.BIG, version:int = SceneFileVersion.VERSION_1) -> bytes:
        fm = FileManipulator(endian=endian)
        # write the name
        fm.w_u32(strings_offsets[self.name])
        # write the link id
        fm.w_u32(self.link_id.num)
        # write the master link id
        if self.master_link_id == None:
            fm.w_u32(0)
        else:
            fm.w_u32(self.master_link_id.num)
        # write the unknown
        fm.w_u32(self.unknown)
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            fm.w_u32(self.unknown_em2)
        # write the amount of components
        fm.w_u32(len(self.components))
        # write the components
        for c in self.components:
            fm.write(c.pack(strings_offsets, endian=endian))
        return fm.getbuffer()
    
    def to_xml(self, version:int = SceneFileVersion.VERSION_1) -> str:
        # create the entity
        entity = Element("ENTITY")
        # set the class name
        entity.set("Class", self.class_name)
        # set the name
        entity.set("Name", self.name)
        # set the link id
        entity.set("LinkID", str(self.link_id))
        # set the master link id
        if self.master_link_id != None:
            entity.set("MasterLinkID", str(self.master_link_id))
        # set the unknown
        if self.unknown != 0:
            entity.set("Unknown", str(self.unknown))
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            entity.set("UnknownEM2", str(self.unknown_em2))
        # add the components
        for c in self.components:
            entity.append(ElementTree.fromstring(c.to_xml()))
        # return the xml
        return tostring(entity)
    
    def to_dict(self, version:int = SceneFileVersion.VERSION_1):
        json_data = {}
        json_data["class_name"] = self.class_name
        json_data["name"] = self.name
        json_data["link_id"] = self.link_id.num
        if self.master_link_id != None and self.master_link_id.num != 0:
            json_data["master_link_id"] = self.master_link_id.num
        json_data["unknown"] = self.unknown
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            json_data["unknown_em2"] = self.unknown_em2
        json_data["components"] = [c.to_dict() for c in self.components]
        return json_data
    
    @staticmethod
    def from_xml(xml:str):
        # load the xml using ElementTree
        entity = ElementTree.fromstring(xml)

        # get the class name
        class_name = entity.get("Class")
        # get the name
        name = entity.get("Name")
        # get the link id
        link_id = ID.from_str(entity.get("LinkID"))
        # get the master link id if it exists
        master_link_id = None
        if entity.get("MasterLinkID") != None:
            master_link_id = ID.from_str(entity.get("MasterLinkID"))
        # get the unknown if it exists
        unknown = 0
        if entity.get("Unknown") != None:
            unknown = int(entity.get("Unknown"))
        unknown_em2 = 0
        if entity.get("UnknownEM2") != None:
            unknown_em2 = int(entity.get("UnknownEM2"))
        # get the components
        components = []
        for c in entity.findall("COMPONENT"):
            components.append(Component.from_xml(tostring(c)))
        
        return Entity(class_name, name, link_id, master_link_id, unknown, unknown_em2, components)

    @staticmethod
    def from_dict(d:dict):
        class_name = d["class_name"]
        name = d["name"]
        link_id = ID.from_int(d["link_id"])
        if "master_link_id" in d:
            master_link_id = ID.from_int(d["master_link_id"])
        else:
            master_link_id = None
        unknown = d["unknown"]
        unknown_em2 = 0
        if "unknown_em2" in d:
            unknown_em2 = d["unknown_em2"]
        components = [Component.from_dict(c) for c in d["components"]]
        return Entity(class_name, name, link_id, master_link_id, unknown, unknown_em2, components)
    
    def __str__(self):
        return f"Entity(class_name={self.class_name}, name={self.name}, link_id={self.link_id}, master_link_id={self.master_link_id}, unknown={self.unknown}, components={self.components})"

class Scene:
    referenced_entities:list[ID]

    def __init__(self, referenced_entities:list[ID] = []):
        self.referenced_entities = referenced_entities
    
    def to_xml(self):
        # create the scene
        scene = Element("SCENE")
        # set class to NiScene
        scene.set("Class", "NiScene")
        # set the name to "Main Scene"
        scene.set("Name", "Main Scene")
        # add the referenced entities
        for e in self.referenced_entities:
            # create ENTITY
            entity = SubElement(scene, "ENTITY")
            # set the link id
            entity.set("RefLinkID", str(e))
        # return the xml
        return tostring(scene)
    
    def to_dict(self):
        return [e.num for e in self.referenced_entities]
    
    @staticmethod
    def from_xml(xml:str):
        # load the xml using ElementTree
        scene = ElementTree.fromstring(xml)

        # get the referenced entities
        referenced_entities = []
        for e in scene.findall("ENTITY"):
            referenced_entities.append(ID.from_str(e.get("RefLinkID")))
        
        return Scene(referenced_entities)
    
    def __str__(self):
        return f"Scene(referenced_entities={self.referenced_entities})"
    
    @staticmethod
    def from_dict(d:dict):
        return Scene([ID(e) for e in d])
    
class Objects:
    entities:list[Entity]

    def __init__(self, entities:list[Entity] = []):
        self.entities = entities
    
    def to_xml(self):
        # create the objects
        objects = Element("OBJECTS")
        # add the entities
        for e in self.entities:
            objects.append(ElementTree.fromstring(e.to_xml()))
        # return the xml
        return tostring(objects)
    
    def to_dict(self):
        return [e.to_dict() for e in self.entities]
    
    @staticmethod
    def from_xml(xml:str):
        # load the xml using ElementTree
        objects = ElementTree.fromstring(xml)

        # get the entities
        entities = []
        for e in objects.findall("ENTITY"):
            entities.append(Entity.from_xml(tostring(e)))
        
        return Objects(entities)
    
    def __str__(self):
        return f"Objects(entities={self.entities})"
    
    @staticmethod
    def from_dict(d:dict):
        return Objects([Entity.from_dict(e) for e in d])

class SceneFile:
    objects:Objects
    scene:Scene
    em2_extra_strings:list[str]
    guid:ID
    version:int

    def __init__(self, scene:Scene = Scene(), objects:Objects = Objects(), guid:ID = ID(), em2_extra_strings:list[str] = [], version:int = SceneFileVersion.VERSION_1):
        self.scene = scene
        self.objects = objects
        self.guid = guid
        self.em2_extra_strings = em2_extra_strings
        self.version = version

    def em1_to_em2p6(self):
        # print all template ids
        for e in self.objects.entities:
            for c in e.components:
                print(c.class_name, c.template_id)
    
    def remove_like_data_and_update_master_link_ids(self, other_entities:list[Entity]):
        # get a list of entity names that are in both scene files
        entity_names = []

        for entity in self.objects.entities:
            for other_entity in other_entities:
                if entity.name.lower() == other_entity.name.lower():
                    entity_names.append(entity.name)

        for entity_name in entity_names:
            this_entity = None
            other_entity = None

            for entity in self.objects.entities:
                if entity.name.lower() == entity_name.lower():
                    this_entity = entity
                    break
            
            for entity in other_entities:
                if entity.name.lower() == entity_name.lower():
                    other_entity = entity
                    break

            for entity in self.objects.entities:
                if str(entity.master_link_id) == str(this_entity.link_id):
                    entity.master_link_id = other_entity.link_id
                # for each component that has the same name, set the master link id to the other entity's link id
                for component in entity.components:
                    for other_component in other_entity.components:
                        if component.class_name == other_component.class_name:
                            component.master_link_id = other_component.link_id
                        for property in component.properties:
                            if property.name == "Objects To Spawn":
                                for value in property.value:
                                    continue
        
        # remove all entities in this scene file that are in the other scene file
        for entity_name in entity_names:
            for entity in self.objects.entities:
                if entity.name.lower() == entity_name.lower():
                    self.objects.entities.remove(entity)
    
    def unpack(self, fm:FileManipulator):
        if self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            fm.move(4)
        # read data offset
        data_offset = fm.r_u32()
        if self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            data_offset += 4
        fm.seek(data_offset)
        # read the guid
        if self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            fm.move(4)
        if self.version == SceneFileVersion.VERSION_1 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            self.guid = ID.from_bytes(fm.read(16))
        if self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            num_extra_strings = fm.r_u32()
            self.em2_extra_strings = []
            for _ in range(num_extra_strings):
                self.em2_extra_strings.append(fm.r_str_jps())
        entity_amount = fm.r_u32()
        ref_ids_amount = fm.r_u32()

        # read the entities
        self.objects.entities = []
        for _ in range(entity_amount):
            entity = Entity()
            entity.unpack(fm, self.version)
            self.objects.entities.append(entity)
        
        # read the referenced entities
        self.scene.referenced_entities = []
        for _ in range(ref_ids_amount):
            self.scene.referenced_entities.append(ID.from_int(fm.r_u32()))
        
        return fm
    
    def add_string_to_strings(self, strings_offsets:dict, strings_section:bytes, start_offset:int, string:str) -> tuple[dict, bytes]:
        if string in strings_offsets:
            return strings_offsets, strings_section
        strings_offsets[string] = len(strings_section) + start_offset
        fm = FileManipulator(endian=EndianType.BIG)
        fm.w_str_jps(string)
        strings_section += fm.getbuffer()
        return strings_offsets, strings_section
    
    def build_strings(self) -> dict:
        strings_offsets = {}
        strings_section = b""
        start_offset = 4
        for e in self.objects.entities:
            strings_offsets, strings_section = self.add_string_to_strings(
                strings_offsets,
                strings_section,
                start_offset,
                e.name
            )
            for c in e.components:
                strings_offsets, strings_section = self.add_string_to_strings(
                    strings_offsets,
                    strings_section,
                    start_offset,
                    c.class_name
                )
                strings_offsets, strings_section = self.add_string_to_strings(
                    strings_offsets,
                    strings_section,
                    start_offset,
                    c.template_id.to_str(fill=False)
                )
                for p in c.properties:
                    strings_offsets, strings_section = self.add_string_to_strings(
                        strings_offsets,
                        strings_section,
                        start_offset,
                        p.name
                    )
                    strings_offsets, strings_section = self.add_string_to_strings(
                        strings_offsets,
                        strings_section,
                        start_offset,
                        p.class_name
                    )
                    
                    if isinstance(p.value, str):
                        strings_offsets, strings_section = self.add_string_to_strings(
                            strings_offsets,
                            strings_section,
                            start_offset,
                            p.value
                        )
                    elif isinstance(p.value, list):
                        for v in p.value:
                            if isinstance(v, str):
                                strings_offsets, strings_section = self.add_string_to_strings(
                                    strings_offsets,
                                    strings_section,
                                    start_offset,
                                    v
                                )
        return strings_offsets, strings_section
    
    def pack(self, endian:EndianType = EndianType.BIG) -> bytes:
        fm = FileManipulator(endian=endian)
        # build the strings
        strings_offsets, strings_section = self.build_strings()
        if self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            fm.w_u32(0x01000001)
        # write the data offset
        fm.w_u32(4 + len(strings_section))
        # write the strings section
        fm.write(strings_section)
        if self.version == SceneFileVersion.VERSION_2:
            fm.w_u32(0x02000002)
        elif self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            fm.w_u32(0x02000001)
        if self.version == SceneFileVersion.VERSION_1 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            # write the guid
            fm.write(self.guid.to_bytes(16, endian=endian))
        if self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            fm.w_u32(len(self.em2_extra_strings))
            for s in self.em2_extra_strings:
                fm.w_str_jps(s)
        # write the entity amount
        fm.w_u32(len(self.objects.entities))
        # write the ref ids amount
        fm.w_u32(len(self.scene.referenced_entities))
        # write the entities
        for e in self.objects.entities:
            fm.write(e.pack(strings_offsets, endian=endian, version=self.version))
        # write the referenced entities
        for e in self.scene.referenced_entities:
            fm.w_u32(e.num)
        return fm.getbuffer()
    
    def display(self):
        # use plt
        import matplotlib.pyplot as plt
        # create the figure
        fig = plt.figure()
        # add the scene
        ax = fig.add_subplot(111, projection="3d")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")

        # set scene limits
        ax.set_xlim(-100, 100)
        ax.set_ylim(-100, 100)
        ax.set_zlim(-100, 100)

        # for every entity
        for e in self.objects.entities:
            # for every component
            for c in e.components:
                if c.class_name == "JPSTransformationComponent":
                    for p in c.properties:
                        if p.name == "Translation":
                            x = -p.value.z
                            y = p.value.y
                            z = p.value.x
                            if (x, y, z) != (0, 0, 0):
                                # plot with a label of the entity name
                                ax.scatter(x, y, z)
                                ax.text(x, y, z, e.name)
        # show the plot
        plt.show()
    
    def to_binary(self, endian:EndianType = EndianType.BIG) -> bytes:
        return self.pack(endian=endian)
    
    def to_binary_path(self, path:str, endian:EndianType = EndianType.BIG):
        with open(path, "wb") as f:
            f.write(self.to_binary(endian=endian))
    
    def to_xml(self, pretty:bool = True) -> str:
        # create the scene file
        scene_file = Element("GSA")

        # version
        scene_file.set("Major", "2")
        scene_file.set("Minor", "0")
        scene_file.set("Patch", "0")

        scene_file.set("Version", str(self.version))

        if self.version == SceneFileVersion.VERSION_1 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            # set the unique id
            scene_file.set("UniqueID", self.guid.to_str(16))
        elif self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            # add the extra strings in a child section
            extra_strings = SubElement(scene_file, "EM2ExtraStrings")
            for s in self.em2_extra_strings:
                string = SubElement(extra_strings, "String")
                string.text = s

        # add the scene
        scene_file.append(ElementTree.fromstring(self.scene.to_xml()))
        # add the objects
        scene_file.append(ElementTree.fromstring(self.objects.to_xml()))
        # return the xml
        string = tostring(scene_file, encoding="utf-8")
        # pretty print the xml
        if pretty:
            string = minidom.parseString(string).toprettyxml(indent="    ")
        return string
    
    def to_xml_path(self, path:str, pretty:bool = True):
        with open(path, "w") as f:
            f.write(self.to_xml(pretty=pretty))
    
    def to_scene_designer_xml(self, pretty:bool = True) -> str:
        initial_xml = ElementTree.fromstring(self.to_xml(pretty=False))
        # for every COMPONENT, if the class name begins with JPS, change it to Ni
        # get OBJECTS
        objects = initial_xml.find("OBJECTS")
        # get all ENTITYs
        entities = objects.findall("ENTITY")
        # 00,00,00,00,00,00,00,00,00,00,00,00,
        id_prefix = ",".join(["00"] * 12) + ","
        # for every ENTITY
        for e in entities:
            class_name = e.get("Class")
            if class_name.startswith("JPS"):
                e.set("Class", "Ni" + class_name[3:])
            # add 12 before the link id
            link_id = e.get("LinkID")
            e.set("LinkID", id_prefix + link_id)
            # add 12 before the master link id if it exists
            master_link_id = e.get("MasterLinkID")
            if master_link_id != None:
                e.set("MasterLinkID", id_prefix + master_link_id)
            # get all COMPONENTs
            components = e.findall("COMPONENT")
            # for every COMPONENT
            for c in components:
                # add 12 before the link id
                link_id = c.get("LinkID")
                c.set("LinkID", id_prefix + link_id)
                # add 12 before the master link id if it exists
                master_link_id = c.get("MasterLinkID")
                if master_link_id != None:
                    c.set("MasterLinkID", id_prefix + master_link_id)
                # add 12 before the template id
                template_id = c.get("TemplateID")
                c.set("TemplateID", id_prefix + template_id)
                # get the class name
                class_name = c.get("Class")
                # if the class name begins with JPS, change it to Ni
                if class_name.startswith("JPS"):
                    c.set("Class", "Ni" + class_name[3:])
                
                class_name = c.get("Class")
                
                # if class name does not start with "Ni", remove the component and continue to the next component
                if not class_name.startswith("Ni") or class_name == "NiPrefabComponent":
                    e.remove(c)
                    continue

                # get all PROPERTYs
                properties = c.findall("PROPERTY")
                # for every PROPERTY
                for p in properties:
                    # get the class name
                    class_name = p.get("Class")
                    if class_name == "Entity Pointer":
                        # add 12 before the ref link id if it exists
                        ref_link_id = p.get("RefLinkID")

                        if ref_link_id != "NULL" and ref_link_id != None:
                            p.set("RefLinkID", id_prefix + ref_link_id)
                    
                    # if the name of the property is DisallowRotation, remove the property
                    name = p.get("Name")
                    property_removal_names = [
                        "DisallowRotation",
                        "Force Update",
                        "Stop Scene Designer Updates",
                        "NoBatch",
                        "Light Group",
                        "Unique",
                        "Static Lighting Participation",
                        "Hardware Lighting Participation",
                        "Special Rendering",
                        "StartAnimationUsingGlobalTime",
                        "AnimateWhenThinned",
                        "Parent Entity",
                        "Bone Attach Name",
                        "Bone Attach Rotate Mode",
                        "Bone Attach Offset",
                        "Use Delta Time",
                        "Dynamic Light Layers",
                        "Hardware Light Affected Entities",
                        "Player Camera",
                        "Inherit Default Camera Properties"
                    ]
                    if name in property_removal_names:
                        c.remove(p)
        
        scene = initial_xml.find("SCENE")
        # get all ENTITYs
        entities = scene.findall("ENTITY")
        # for every ENTITY
        for e in entities:
            # add 12 before the ref link id if it exists
            ref_link_id = e.get("RefLinkID")
            if ref_link_id != None:
                e.set("RefLinkID", id_prefix + ref_link_id)
        
        # move all components into the same pool as the entities, and put COMPONENTs in the ENTITYs with a RefLinkID to the COMPONENTs link id
        # get all COMPONENTs
        
        objects = initial_xml.find("OBJECTS")
        entities = objects.findall("ENTITY")

        for e in entities:
            # get all COMPONENTs
            components = e.findall("COMPONENT")
            # for every COMPONENT
            for c in components:
                # create a copy of the COMPONENT with a parent of OBJECTS
                objects.append(c)
                # remove the COMPONENT from the ENTITY
                e.remove(c)
                # create a new component with a parent of ENTITY
                component = SubElement(e, "COMPONENT")
                # set the ref link id to the COMPONENTs link id
                component.set("RefLinkID", c.get("LinkID"))
        
        # return the xml
        string = tostring(initial_xml, encoding="utf-8")
        # pretty print the xml
        if pretty:
            string = minidom.parseString(string).toprettyxml(indent="    ")
        return string
    
    def to_dict(self):
        dictionary = {}
        dictionary["version"] = self.version
        dictionary["scene"] = self.scene.to_dict()
        dictionary["objects"] = self.objects.to_dict()
        if self.version == SceneFileVersion.VERSION_1 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            dictionary["guid"] = self.guid.to_str(16)
        elif self.version == SceneFileVersion.VERSION_2 or self.version == SceneFileVersion.VERSION_2_PROTOTYPE:
            dictionary["em2_extra_strings"] = self.em2_extra_strings
        return dictionary
    
    def to_json(self, pretty:bool = True) -> str:
        return json.dumps(self.to_dict(), indent=4 if pretty else None)
    
    def to_json_path(self, path:str, pretty:bool = True):
        with open(path, "w") as f:
            f.write(self.to_json(pretty=pretty))
    
    @staticmethod
    def from_xml(xml:str):
        # load the xml using ElementTree
        scene_file = ElementTree.fromstring(xml)

        version = int(scene_file.get("Version"))
        em2_extra_strings = []
        guid = ID()
        if version == SceneFileVersion.VERSION_1 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            # get the unique id
            guid = ID.from_str(scene_file.get("UniqueID"))
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            for s in scene_file.find("EM2ExtraStrings"):
                em2_extra_strings.append(s.text)

        # get the scene
        scene = Scene.from_xml(tostring(scene_file.find("SCENE")))
        # get the objects
        objects = Objects.from_xml(tostring(scene_file.find("OBJECTS")))
        
        return SceneFile(scene, objects, guid, em2_extra_strings, version)

    @staticmethod
    def from_xml_path(path:str):
        with open(path, "r") as f:
            return SceneFile.from_xml(f.read())
    
    @staticmethod
    def from_binary(data:bytes, endian:EndianType = EndianType.BIG):
        fm = FileManipulator(data, endian=endian)
        start_pos = fm.tell()
        first_four_bytes = fm.r_u32()
        version = SceneFileVersion.VERSION_1
        if first_four_bytes == 0x01000001:
            offset = fm.r_u32() + 4
            fm.seek(offset)
            # if its 0x02000002, its version 2, if its 0x02000001, its version 2 prototype
            num = fm.r_u32()
            if num == 0x02000002:
                version = SceneFileVersion.VERSION_2
            elif num == 0x02000001:
                version = SceneFileVersion.VERSION_2_PROTOTYPE
            else:
                raise Exception(f"Unknown version number: {num}")
        fm.seek(start_pos)
        scene_file = SceneFile(version=version)
        scene_file.unpack(fm)
        return scene_file
    
    @staticmethod
    def from_binary_path(path:str, endian:EndianType = EndianType.BIG):
        with open(path, "rb") as f:
            return SceneFile.from_binary(f.read(), endian=endian)
    
    @staticmethod
    def from_path_auto(path:str, endian:EndianType = EndianType.BIG):
        scene = None
        try:
            scene = SceneFile.from_xml_path(path)
        except:
            scene = SceneFile.from_binary_path(path, endian=endian)
        return scene
    
    @staticmethod
    def from_dict(d:dict):
        version = d["version"]
        scene = Scene.from_dict(d["scene"])
        objects = Objects.from_dict(d["objects"])
        em2_extra_strings = []
        guid = ID()
        if version == SceneFileVersion.VERSION_1 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            guid = ID.from_str(d["guid"])
        if version == SceneFileVersion.VERSION_2 or version == SceneFileVersion.VERSION_2_PROTOTYPE:
            em2_extra_strings = d["em2_extra_strings"]
            
        return SceneFile(scene, objects, guid, em2_extra_strings, version)
    
    @staticmethod
    def from_json(json_str:str):
        return SceneFile.from_dict(json.loads(json_str))
    
    @staticmethod
    def from_json_path(path:str):
        with open(path, "r") as f:
            return SceneFile.from_json(f.read())
    
    def __str__(self):
        return f"SceneFile(scene={self.scene}, objects={self.objects})"