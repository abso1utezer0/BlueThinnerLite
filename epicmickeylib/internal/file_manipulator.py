# epicmickeylib/internal/file_manipulator.py
#
# "advanced" random access file manipulator
# probably inefficient

from io import BytesIO
import os
import struct

class EndianType:
    BIG     = 0
    LITTLE  = 1

class WriteMode:
    OVERWRITE = 0
    INSERT    = 1

class FileManipulator(BytesIO):
    # controls whether the file should r/w with a big or little endianess
    endian:EndianType = EndianType.BIG

    # controls whether the file should insert or overwrite data
    write_mode:WriteMode = WriteMode.OVERWRITE

    def __init__(self, data:bytes=b"", endian:EndianType=EndianType.BIG, write_mode:WriteMode=WriteMode.OVERWRITE) -> "FileManipulator":
        super().__init__(data)
        self.endian = endian
        self.write_mode = write_mode
    
    def read_backwards(self, length:int) -> bytes:
        # move backwards through the file
        data = bytes()
        for _ in range(length):
            self.move(-1)
            data += self.read(1)
            self.move(-1)
        return data
    
    def write(self, __buffer: bytes):
        if self.write_mode == WriteMode.OVERWRITE:
            super().write(__buffer)
        elif self.write_mode == WriteMode.INSERT:
            # insert data
            pos = self.tell()
            data = self.read()
            self.seek(pos)
            super().write(__buffer)
            super.write(data)
            # move file pointer
            self.seek(pos + len(__buffer))
    
    def get_struct_order_prefix(self):
        if self.endian == EndianType.BIG:
            return ">"
        elif self.endian == EndianType.LITTLE:
            return "<"
        return "@" # if no endian is somehow specified or it is invalid, default to the machine's byte ordering

    def read_type(self, data_type) -> any:

        """
        Reads data from the file and unpacks it from the specified format.

        Args:
        - data_type (str): The type of data to be read.
        - length (int): The length of the data to be read.

        Returns:
        - The data that was read.
        """

        prefix = self.get_struct_order_prefix()
        format_str = prefix + data_type
        size = struct.calcsize(format_str)
        values = struct.unpack(format_str, self.read(size))
        if len(values) == 1:
            return values[0]
        return values
    
    def r_u8(self) -> int:
        """
        Reads a byte from the file.

        Returns:
        - The byte that was read.
        """
        return self.read_type("B")
    
    def r_s8(self) -> int:
        """
        Reads a byte from the file.

        Returns:
        - The byte that was read.
        """
        return self.read_type("b")
    
    def r_u16(self) -> int:

        """
        Reads a 2-byte unsigned short from the file.

        Returns:
        - The unsigned short that was read.
        """

        return self.read_type("H")
    
    def r_u16_jps(self) -> int:
        """
        Reads a 2-byte unsigned short from the file.

        Returns:
        - The unsigned short that was read.
        """
        data = self.read_type("H")
        self.move(2)
        return data
    
    def r_s16(self) -> int:
            
        """
        Reads a 2-byte signed short from the file.

        Returns:
        - The short that was read.
        """

        return self.read_type("h")
    
    def r_u32(self) -> int:
            
        """
        Reads a 4-byte unsigned integer from the file.

        Returns:
        - The unsigned integer that was read.
        """

        return self.read_type("I")
    
    def r_s32(self) -> int:
                
        """
        Reads a 4-byte signed integer from the file.

        Returns:
        - The integer that was read.
        """

        return self.read_type("i")
    
    def r_u64(self) -> int:
                
        """
        Reads an 8-byte unsigned integer from the file.

        Returns:
        - The unsigned integer that was read.
        """

        return self.read_type("Q")
    
    def r_s64(self) -> int:
                
        """
        Reads an 8-byte signed integer from the file.

        Returns:
        - The integer that was read.
        """

        return self.read_type("q")
    
    def r_u128(self) -> int:
        
        """
        Reads a 16-byte unsigned integer from the file.

        Returns:
        - The unsigned integer that was read.
        """

        data = self.read_type("QQ") 
        return (data[0] << 64) | data[1]
    
    def r_s128(self) -> int:

        """
        Reads a 16-byte signed integer from the file.

        Returns:
        - The integer that was read.
        """

        data = self.read_type("qq") 
        return (data[0] << 64) | data[1]
    
    def r_float(self) -> float:
        return self.read_type("f")
    
    def r_str(self, length) -> str:

        """
        Reads a specified amount of characters from the file.

        Args:
        - length (int): The length of the characters to be read.

        Returns:
        - The characters that were read.
        """

        return self.read(length).decode("utf-8")
    
    def r_str_jps(self) -> str:
        size = self.r_u8()
        text_length = self.r_u8()
        text = self.r_str_null()
        self.align()
        return text
    
    def r_str_null(self, encoding="utf-8") -> str:

        """
        Reads a null-terminated string from the file.

        Returns:
        - The string that was read.
        """
        
        string = b""
        while True:
            char = self.read(1)
            if char == b"\x00":
                break
            string += char
        return string.decode(encoding, errors="backslashreplace")
    
    def r_bool(self) -> bool:
        value = False
        data = self.read(4)

        ffs_encountered = 0
        for num in data:
            if num == 255:
                ffs_encountered += 1
        
        if ffs_encountered == 4:
            value = True
        
        return value
    
    def write_type(self, data_type:str, data:any) -> None:

        """
        Packs the given data into the specified format and writes it to the file.

        Args:
        - data_type (str): The type of data to be packed.
        - data (Any): The data to be packed.
        """

        prefix = self.get_struct_order_prefix()
        format_str = prefix + data_type
        self.write(struct.pack(format_str, data))
    
    def w_u8(self, data) -> None:
        """
        Writes an unsigned byte to the file.
        """
        self.write_type("B", data)
    
    def w_s8(self, data) -> None:
        """
        Writes a signed byte to the file.
        """
        self.write_type("b", data)
    
    def w_u16(self, data) -> None:

        """
        Writes a 2-byte unsigned short to the file.
        """

        self.write_type("H", data)
    
    def w_u16_jps(self, data, mode:int=0) -> None:
        """
        Writes a 2-byte unsigned short to the file.
        """
        self.write_type("H", data)
        byte_to_write = b""
        if mode == 0:
            byte_to_write = b"\xCD"
        elif mode == 1:
            byte_to_write = b"\xFF"
        for _ in range(2):
            self.write(byte_to_write)
    
    def w_s16(self, data) -> None: 
        """
        Writes a 2-byte signed short to the file.
    
        Returns:
        - The short that was read.
        """
    
        self.write_type("h", data)
    
    def w_u32(self, data) -> None:
            
        """
        Writes a 4-byte unsigned integer to the file.
        """

        self.write_type("I", data)
    
    def w_s32(self, data) -> None:
                
        """
        Writes a 4-byte signed integer to the file.
        """

        self.write_type("i", data)
    
    def w_u64(self, data) -> None:
        
        """
        Writes an 8-byte unsigned integer to the file.
        """

        self.write_type("Q", data)
    
    def w_s64(self, data) -> None:
        
        """
        Writes an 8-byte signed integer to the file.
        """

        self.write_type("q", data)
    
    def w_u128(self, data) -> None:
            
        """
        Writes a 16-byte unsigned integer to the file.
        """

        self.write_type("Q", data >> 64)
        self.write_type("Q", data & 0xFFFFFFFFFFFFFFFF)
    
    def w_s128(self, data) -> None:

        """
        Writes a 16-byte signed integer to the file.
        """

        self.write_type("q", data >> 64)
        self.write_type("q", data & 0xFFFFFFFFFFFFFFFF)
    
    def w_float(self, data) -> None:
        self.write_type("f", data)

    def w_str(self, text:str) -> None:
        self.write(text.encode("utf-8"))
    
    def w_str_jps(self, text:str) -> None:
        text_length = len(text)
        if text_length > 0:
            text_length += 1
        size = text_length + 2
        while (size % 4) != 0:
            size += 1
        self.w_u8(size)
        self.w_u8(text_length)
        self.w_str_null(text)
        self.pad()

    def w_str_null(self, text:str) -> None:
        self.w_str(text)
        self.w_u8(0)
    
    def w_bool(self, value:bool) -> None:
        num = 0
        if value == True:
            num = 255
        for _ in range(4):
            self.w_u8(num)
    
    def flip_endian(self) -> None:
        if self.endian == EndianType.BIG:
            self.endian = EndianType.LITTLE
        else:
            self.endian = EndianType.BIG
    
    def move(self, amount:int=1) -> None:

        """
        Moves the file pointer a specified amount of bytes.

        Args:
        - amount (int): The amount of bytes to move the file pointer.
        """

        self.seek(self.tell() + amount)

    def align(self, num:int = 4) -> None:

        """
        Aligns the file pointer to a specified byte boundary.

        Args:
        - num (int): The byte boundary to align the file pointer to.
        """

        pos = self.tell()
        if pos % num != 0:
            self.seek(pos + (num - (pos % num)))
    
    def pad(self, amount:int = 4):
        """
        Performs like `align()`, but writes data instead of seeking.

        Args:
        - amount (int): The byte boundary to align the file pointer to.
        """
            
        pos = self.tell()
        if pos % amount != 0:
            self.write(b"\x00" * (amount - (pos % amount)))
    
    def size(self) -> int:
            
        """
        Gets the size of the file.

        Returns:
        - The size of the file.
        """

        return len(self.getbuffer())

    def set_endian(self, endian:str) -> None:
        if endian == "big":
            self.endian = EndianType.BIG
        elif endian == "little":
            self.endian = EndianType.LITTLE
        else:
            raise ValueError("Invalid endian type")
    
    def to_path(self, path:str):
        with open(path, "wb") as f:
            f.write(self.getbuffer())

    @staticmethod
    def from_path(path:str, endian:EndianType=EndianType.BIG, write_mode:WriteMode=WriteMode.OVERWRITE) -> "FileManipulator":
        file = open(path, "rb")
        fm = FileManipulator(data=file.read(), endian=endian, write_mode=write_mode)
        file.close()
        return fm
