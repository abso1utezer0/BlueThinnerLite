# epicmickeylib/formats/texture.py
#
# texture wrapper class that allows for easy conversion of formats

# Texture research done by AltruisticNut, implemented by me

from nifgen.formats.dds import DdsFile
from nifgen.formats.dds.enums.FourCC import FourCC
from nifgen.formats.nif import NifFile
from io import BytesIO
import PIL
import PIL.Image
from epicmickeylib.internal.file_manipulator import FileManipulator
from nifgen.formats.nif.enums.AlphaFormat import AlphaFormat
from nifgen.formats.nif.enums.MipMapFormat import MipMapFormat
from nifgen.formats.nif.enums.PixelComponent import PixelComponent
from nifgen.formats.nif.enums.PixelLayout import PixelLayout
from nifgen.formats.nif.enums.PixelRepresentation import PixelRepresentation
from nifgen.formats.nif.enums.PixelTiling import PixelTiling
from nifgen.formats.nif.enums.PlatformID import PlatformID
from nifgen.formats.nif.enums.PixelFormat import PixelFormat
from nifgen.formats.nif.enums.EndianType import EndianType
from nifgen.formats.nif.nimain.niobjects.NiPersistentSrcTextureRendererData import NiPersistentSrcTextureRendererData
from nifgen.formats.nif.nimain.niobjects.NiSourceTexture import NiSourceTexture
from nifgen.formats.nif.nimain.structs.MipMap import MipMap as NifMipMap
from nifgen.formats.nif.nimain.structs.FormatPrefs import FormatPrefs
from nifgen.formats.nif.nimain.structs.PixelFormatComponent import PixelFormatComponent

class TileUtil:
    def untile_pixels(pixels: list, width: int) -> list:

        """
        Untiles pixels. 

        Args:
        - pixels: the pixels to be untiled
        - width: the width of the texture
        - row_order: the order of the rows (default: [0, 1, 2, 3])
        
        Returns:
        The untiled pixels.
        """

        rearranged_pixels = []
        num = width * 4
        for i in range(0, len(pixels), num):
            for j in range(0, 16, 4):
                for k in range(i+j, i+num+j, 16):
                    pixels_to_add = pixels[k:k+4]
                    for pixel in pixels_to_add:
                        rearranged_pixels.append(pixel)
        return rearranged_pixels
    
    

class MipMap:
    width:int
    height:int
    data:bytes
    def __init__(self, width:int, height:int, data:bytes):
        self.width = width
        self.height = height
        self.data = data
    
    def to_wii_rgba_32(self):
        pixels = []
        for i in range(0, len(self.data), 4):
            pixel = self.data[i:i+4]
            pixels.append(pixel)
        tiles = TileUtil.untile_pixels(pixels, self.width)
        new_pixel_data = b""
        for tile in tiles:
            for pixel in tile:
                new_pixel_data += bytes([pixel])
        return new_pixel_data

    @staticmethod
    def from_wii_dxt1(width:int, height:int, data):
        # convert data to bytes
        data = bytes(data)
        
        bytes_per_chunk = width * 4
        
        chunks = []
        crop = (width * height) // 2
        data_to_use = data
        for i in range(0, len(data_to_use), bytes_per_chunk):
            chunks.append(data_to_use[i:i+bytes_per_chunk])
        new_bytes_to_use = b""
        for chunk in chunks:
            # split the chunk into rows, each row is 16 bytes (but each tile is 8 bytes)
            rows = []
            for i in range(0, len(chunk), 8):
                rows.append(chunk[i:i+8])
            group_one = []
            group_two = []
            for i in range(0, len(rows), 4):
                group_one.append(rows[i])
                if i + 1 < len(rows):
                    group_one.append(rows[i+1])
                if i + 2 < len(rows):
                    group_two.append(rows[i+2])
                if i + 3 < len(rows):
                    group_two.append(rows[i+3])
            final_rows = []
            for i in range(0, len(group_one)):
                final_rows.append(group_one[i])
            for i in range(0, len(group_two)):
                final_rows.append(group_two[i])
            for row in final_rows:
                for byte in row:
                    new_bytes_to_use += bytes([byte])
        data = []
        for byte in new_bytes_to_use:
            data.append(byte)
        # run through every 8 bytes
        for i in range(0, len(data), 8):
            chunk = data[i:i+8]
            new_chunk = []
            new_chunk.append(chunk[1])
            new_chunk.append(chunk[0])
            new_chunk.append(chunk[3])
            new_chunk.append(chunk[2])
            nibble_map = {
                "e": "b",
                "d": "7",
                "c": "3",
                "b": "e",
                "9": "6",
                "8": "2",
                "7": "d",
                "6": "9",
                "4": "1",
                "3": "c",
                "2": "8",
                "1": "4"
            }
            # for the last 4 bytes, reverse them (e.g. 0x0F -> 0xF0)
            for j in range(4, 8):
                # reverse the byte
                byte = chunk[j]
                hex_byte = hex(byte)[2:]
                if len(hex_byte) == 1:
                    hex_byte = "0" + hex_byte
                first_nibble = hex_byte[0]
                second_nibble = hex_byte[1]
                new_byte = second_nibble + first_nibble
                # replace the nibbles if they need to be replaced
                for k in range(len(new_byte)):
                    nibble = new_byte[k]
                    if nibble in nibble_map:
                        new_byte = new_byte[:k] + nibble_map[nibble] + new_byte[k+1:]
                # convert the byte back to an int
                new_byte = int(new_byte, 16)
                new_chunk += bytes([new_byte])
            
            # replace the chunk
            for j in range(8):
                data[i+j] = new_chunk[j]

        # create dds with header from the data
        file = DdsFile()
        file.flags.caps = 1
        file.flags.height = 1
        file.flags.width = 1
        file.flags.pixel_format = 1
        file.flags.mipmap_count = 1
        file.flags.linear_size = 0
        file.height = height
        file.width = width
        file.linear_size = 0
        file.mipmap_count = 1
        file.pixel_format.flags.four_c_c = 1
        file.pixel_format.four_c_c = FourCC.DXT1
        file.pixel_format.bit_count = 0
        file.pixel_format.r_mask = 0
        file.pixel_format.g_mask = 0
        file.pixel_format.b_mask = 0
        file.pixel_format.a_mask = 0
        file.caps_1.complex = 1
        file.caps_1.texture = 1
        file.caps_1.mipmap = 1
        file.buffer = bytes(data)
        
        # create stream
        stream = BytesIO()
        # write the dds file to the stream
        file.write(stream)
        # get the data from the stream
        data = stream.getvalue()
        # convert to a PIL image, get the raw rgba data, and use it for MipMap.data
        image = PIL.Image.open(BytesIO(data))
        image = image.convert("RGBA")
        data = image.tobytes()
        return MipMap(width, height, data)
    
    @staticmethod
    def from_wii_rgba_16(width:int, height:int, data):
        pixels = []
        def bits_to_channel(bits: list) -> int:
            binary = ""
            for bit in bits:
                binary += str(bit)
            multiply_by = 2**(8-len(bits))
            return int(binary, 2) * multiply_by
        for i in range(0, len(data), 2):
            pixel_bytes = data[i:i+2]
            # convert to binary list (0 or 1)
            binary_list = []
            for byte in pixel_bytes:
                binary = bin(byte)[2:]
                # pad with 0s
                while len(binary) < 8:
                    binary = "0" + binary
                for bit in binary:
                    binary_list.append(int(bit))
            alpha = 0
            red = 0
            green = 0
            blue = 0
            read_alpha = False
            if binary_list[0] == 0:
                read_alpha = True
            if read_alpha:
                alpha = bits_to_channel(binary_list[1:4])
                red = bits_to_channel(binary_list[4:8])
                green = bits_to_channel(binary_list[8:12])
                blue = bits_to_channel(binary_list[12:16])
            else:
                alpha = 255
                red = bits_to_channel(binary_list[1:6])
                green = bits_to_channel(binary_list[6:11])
                blue = bits_to_channel(binary_list[11:16])
            pixels.append([red, green, blue, alpha])
        new_pixel_data = b""
        pixels = TileUtil.untile_pixels(pixels, width)
        for pixel in pixels:
            for byte in pixel:
                new_pixel_data += bytes([byte])
        
        data = new_pixel_data

        # create the mipmap
        return MipMap(width, height, data)
    
    @staticmethod
    def from_wii_rgba_32(width:int, height:int, data):
        tiles = []
        # each tile is 64 bytes
        for i in range(0, len(data), 64):
            first_half = data[i:i+32]
            second_half = data[i+32:i+64]

            tile_data = []

            alpha_values = []
            red_values = []
            green_values = []
            blue_values = []
            # alphas
            for j in range(0, len(first_half), 2):
                alpha_values.append(first_half[j])
            # reds
            for j in range(1, len(first_half), 2):
                red_values.append(first_half[j])
            # greens
            for j in range(0, len(second_half), 2):
                green_values.append(second_half[j])
            # blues
            for j in range(1, len(second_half), 2):
                blue_values.append(second_half[j])
            
            # create the tile data
            for j in range(len(alpha_values)):
                tile_data.append(red_values[j])
                tile_data.append(green_values[j])
                tile_data.append(blue_values[j])
                tile_data.append(alpha_values[j])
            
            tiles.append(tile_data)
        
        new_pixel_data = b""

        for tile in tiles:
            for byte in tile:
                new_pixel_data += bytes([byte])

        pixels = []
        for i in range(0, len(new_pixel_data), 4):
            pixels.append(new_pixel_data[i:i+4])
        
        pixels = TileUtil.untile_pixels(pixels, width)

        new_pixel_data = b""
        for pixel in pixels:
            for byte in pixel:
                new_pixel_data += bytes([byte])
        
        data = new_pixel_data

        # create the mipmap
        return MipMap(width, height, data)
    
    @staticmethod
    def from_rgb_32(width:int, height:int, data):
        # convert RGB to RGBA using PIL
        image = PIL.Image.frombytes("RGB", (width, height), data)
        image = image.convert("RGBA")
        data = image.tobytes()
        return MipMap(width, height, data)
    
    @staticmethod
    def from_wii_2ch(width:int, height:int, data):
        pixels = []
        for i in range(0, len(data), 2):
            pixel = []
            # alpha is the first byte
            alpha = data[i]
            # intensity is the second byte
            intensity = data[i+1]
            for j in range(3):
                pixel.append(intensity)
            pixel.append(alpha)
            pixels.append(pixel)
        pixels = TileUtil.untile_pixels(pixels, width)
        new_pixel_data = b""
        for pixel in pixels:
            for byte in pixel:
                new_pixel_data += bytes([byte])
        data = new_pixel_data
        return MipMap(width, height, data)
    
    @staticmethod
    def from_wii_1ch_4(width:int, height:int, data):
        pixels = []
        for i in range(0, len(data), 2):
            # split byte into two nibbles
            byte = data[i]
            hex_byte = hex(byte)[2:]
            if len(hex_byte) == 1:
                hex_byte = "0" + hex_byte
            first_nibble = bytes.fromhex(hex_byte[0] + hex_byte[0])
            second_nibble = bytes.fromhex(hex_byte[1] + hex_byte[1])
            for nibble in [first_nibble, second_nibble]:
                pixel = []
                # intensity is the nibble
                intensity = nibble[0]
                for j in range(4):
                    pixel.append(intensity)
                pixels.append(pixel)
        pixels = TileUtil.untile_pixels(pixels, width)
        new_pixel_data = b""
        for pixel in pixels:
            for byte in pixel:
                new_pixel_data += bytes([byte])
        data = new_pixel_data
        return MipMap(width, height, data)
    
    @staticmethod
    def from_wii_1ch_8(width:int, height:int, data):
        pixels = []
        # 2ch but without alpha (1 byte per pixel)
        for i in range(len(data)):
            pixel = []
            # intensity is the byte
            intensity = data[i]
            for j in range(4):
                pixel.append(intensity)
            pixels.append(pixel)
        pixels = TileUtil.untile_pixels(pixels, width)
        new_pixel_data = b""
        for pixel in pixels:
            for byte in pixel:
                new_pixel_data += bytes([byte])
        data = new_pixel_data
        return MipMap(width, height, data)

    def to_format(self, format:str="png", quality:int=100):
        image = PIL.Image.frombytes("RGBA", (self.width, self.height), self.data)
        stream = BytesIO()
        image.save(stream, format=format, quality=quality)
        return stream.getvalue()
    
    def to_format_path(self, path:str, format:str="png", quality:int=100):
        data = self.to_format(format=format, quality=quality)
        with open(path, "wb") as f:
            f.write(data)
    
    def to_dict(self):
        data = []
        for byte in self.data:
            data.append(byte)
        return {
            "width": self.width,
            "height": self.height,
            "data": data
        }

class Texture:
    platform:str
    target_format:str
    mipmaps:list[MipMap]

    def __init__(self, mipmaps:list[MipMap]=[]):
        self.mipmaps = mipmaps
    
    def to_format(self, format:str="png", quality:int=100):
        mipmap = self.mipmaps[0]
        return mipmap.to_format(format=format, quality=quality)
    
    def to_format_path(self, path:str, format:str="png", quality:int=100):
        mipmap = self.mipmaps[0]
        mipmap.to_format_path(path, format=format, quality=quality)
    
    @staticmethod
    def from_binary(data:bytes):
        # create stream
        stream = BytesIO(data)
        # open the data as a nif file
        nif = NifFile.from_stream(stream)
        # convert the nif file to a texture
        texture = Texture.from_nif(nif)
        return texture
    
    @staticmethod
    def from_binary_path(path:str):
        with open(path, "rb") as f:
            data = f.read()
        return Texture.from_binary(data)

    @staticmethod
    def from_nif(nif:NifFile):
        #print(nif.blocks[1])
        #exit()
        texture = Texture()
        mipmaps = []
        for block in nif.blocks:
            if block.__class__.__name__ == "NiPersistentSrcTextureRendererData":
                size_per_pixel = block.bytes_per_pixel
                if block.pixel_format == PixelFormat.FMT_DXT1:
                    size_per_pixel = 8
                
                for mipmap in block.mipmaps:
                    width = mipmap.width
                    height = mipmap.height
                    offset = mipmap.offset
                    data_length = int((width * height) * size_per_pixel)
                    data = block.pixel_data[offset:offset+data_length]
                    if block.platform == PlatformID.WII:
                        texture.platform = "wii"
                        if block.pixel_format == PixelFormat.FMT_DXT1:
                            texture.target_format = "dxt1"
                            mipmaps.append(MipMap.from_wii_dxt1(width, height, data))
                        elif block.pixel_format == PixelFormat.FMT_RGBA:
                            if size_per_pixel == 2:
                                texture.target_format = "rgba16"
                                mipmaps.append(MipMap.from_wii_rgba_16(width, height, data))
                            elif size_per_pixel == 4:
                                texture.target_format = "rgba32"
                                mipmaps.append(MipMap.from_wii_rgba_32(width, height, data))
                        elif block.pixel_format == PixelFormat.FMT_RGB:
                            if size_per_pixel == 4:
                                texture.target_format = "rgb32"
                                mipmaps.append(MipMap.from_rgb_32(width, height, data))
                            else:
                                raise Exception("Unsupported pixel byte length for RGB pixel data: " + str(size_per_pixel))
                        elif block.pixel_format == PixelFormat.FMT_2CH:
                            texture.target_format = "2ch"
                            mipmaps.append(MipMap.from_wii_2ch(width, height, data))
                        elif block.pixel_format == PixelFormat.FMT_1CH:
                            if size_per_pixel == 1:
                                texture.target_format = "1ch8"
                                mipmaps.append(MipMap.from_wii_1ch_8(width, height, data))
                            elif size_per_pixel == 0.5:
                                texture.target_format = "1ch4"
                                mipmaps.append(MipMap.from_wii_1ch_4(width, height, data))
                            else:
                                raise Exception("Unsupported pixel byte length for 1CH pixel data: " + str(size_per_pixel))
                        else:
                            raise Exception("Unsupported pixel format: " + str(block.pixel_format))
                    else:
                        raise Exception("Unsupported platform: " + str(block.platform))
        
        texture.mipmaps = mipmaps
        return texture
    
    def to_dict(self):
        mipmaps = []
        for mipmap in self.mipmaps:
            mipmaps.append(mipmap.to_dict())
        return {
            "platform": self.platform,
            "target_format": self.target_format,
            "mipmaps": mipmaps
        }
    
    def to_nif(self) -> NifFile:
        nif = NifFile()
        nif.header_string = "Gamebryo File Format, Version 20.6.5.0"
        nif.version = 335938816
        nif.endian_type = EndianType.ENDIAN_BIG
        nif.user_version = 14
        nif.num_blocks = 2
        nif.num_block_types = 2
        nif.block_types = ["NiSourceTexture", "NiPersistentSrcTextureRendererData"]
        nif.block_type_index = [0, 1]
        nif.num_strings = 0
        nif.max_string_length = 0
        nif.strings = []
        nif.num_groups = 0
        nif.groups = []
        nif.blocks = []
        ni_source_texture = NiSourceTexture(nif)
        ni_source_texture.name = ""
        ni_source_texture.num_extra_data_list = 0
        ni_source_texture.extra_data_list = []
        ni_source_texture.controller = None
        ni_source_texture.use_external = 0
        ni_source_texture.file_name = ""
        ni_source_texture.format_prefs = FormatPrefs(nif)
        ni_source_texture.format_prefs.pixel_layout = PixelLayout.LAY_DEFAULT
        ni_source_texture.format_prefs.use_mipmaps = MipMapFormat.MIP_FMT_DEFAULT
        ni_source_texture.format_prefs.alpha_format = AlphaFormat.ALPHA_DEFAULT
        ni_source_texture.is_static = 1
        ni_source_texture.direct_render = 0
        ni_source_texture.persist_render_data = 1

        ni_persistent_src_texture_renderer_data = NiPersistentSrcTextureRendererData(nif)
        pixel_format = None
        bits_per_pixel = 0
        if self.target_format == "rgba32":
            pixel_format = PixelFormat.FMT_RGBA
            bits_per_pixel = 32
        else:
            # TODO: add more formats
            raise Exception("Unsupported target format: " + self.target_format)
        ni_persistent_src_texture_renderer_data.pixel_format = pixel_format
        ni_persistent_src_texture_renderer_data.bits_per_pixel = bits_per_pixel
        ni_persistent_src_texture_renderer_data.renderer_hint = 4294967295
        ni_persistent_src_texture_renderer_data.extra_data = 0
        ni_persistent_src_texture_renderer_data.flags = 1
        tiling = None
        if self.platform == "wii":
            tiling = PixelTiling.TILE_WII
        else:
            raise Exception("Unsupported platform: " + self.platform)
        ni_persistent_src_texture_renderer_data.s_r_g_b_space
        ni_persistent_src_texture_renderer_data.channels = []
        for i in range(4):
            pixel_format_component = PixelFormatComponent(nif)
            if i == 0:
                pixel_format_component.type = PixelComponent.COMP_COMPRESSED
                pixel_format_component.convention = PixelRepresentation.REP_COMPRESSED
            else:
                pixel_format_component.type = PixelComponent.COMP_EMPTY
                pixel_format_component.convention = PixelRepresentation.REP_UNKNOWN
            pixel_format_component.bits_per_channel = 8
            pixel_format_component.is_signed = 0
            ni_persistent_src_texture_renderer_data.channels.append(pixel_format_component)
        ni_persistent_src_texture_renderer_data.palette = None
        ni_persistent_src_texture_renderer_data.num_mipmaps = 1
        ni_persistent_src_texture_renderer_data.bytes_per_pixel = bits_per_pixel // 8
        ni_persistent_src_texture_renderer_data.mipmaps = []
        pixel_data = b""
        for mipmap in self.mipmaps:
            mipmap_data = mipmap.to_wii_rgba_32()
            width = mipmap.width
            height = mipmap.height
            offset = len(pixel_data)
            nif_mipmap = NifMipMap(nif)
            nif_mipmap.width = width
            nif_mipmap.height = height
            nif_mipmap.offset = offset
            ni_persistent_src_texture_renderer_data.mipmaps.append(nif_mipmap)
            pixel_data += mipmap_data
            break
        ni_persistent_src_texture_renderer_data.num_pixels = len(pixel_data) // 4
        ni_persistent_src_texture_renderer_data.pad_num_pixels = 0
        ni_persistent_src_texture_renderer_data.num_faces = 1
        if self.platform == "wii":
            ni_persistent_src_texture_renderer_data.platform = PlatformID.WII
        else:
            raise Exception("Unsupported platform: " + self.platform)
        ni_persistent_src_texture_renderer_data.pixel_data = pixel_data
        ni_source_texture.pixel_data = ni_persistent_src_texture_renderer_data
        nif.blocks.append(ni_source_texture)
        nif.blocks.append(ni_persistent_src_texture_renderer_data)
        return nif
    
    def to_binary(self) -> bytes:
        nif = self.to_nif()
        stream = BytesIO()
        nif.write(stream)
        return stream.getvalue()
    
    def to_binary_path(self, path:str):
        data = self.to_binary()
        with open(path, "wb") as f:
            f.write(data)