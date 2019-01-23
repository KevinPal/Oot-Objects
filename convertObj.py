import sys
from pathlib import Path
import pprint
import os
from enum import Enum
import copy

path = sys.argv[1]
print(path)
my_file = Path(path)
if not my_file.is_file():
    print("File " + str(path) + " not found")
    sys.exit()

f_size = os.stat(path).st_size
f = open(path, "rb")

all_data = []

for line in range(0, int(f_size / 8)):
    all_data.append(f.read(8))


class Arg():

    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __str__(self):
        return self.name

class Opcode():
    
    def __init__(self, name, check_hex, *args, is_data=False):
        self.args = args
        self.name = name
        self.check_hex = list(check_hex)
        self.is_data = is_data

    def copy(self):
        return copy.deepcopy(self)

    def load_data(self, data):

        self.is_data = False

        try:
            hex(data)
            str_data = list(str(hex(data))[2:].zfill(16))
            for i in range(0, len(self.check_hex)):
                if '0' <= self.check_hex[i]  <= '9':
                    if self.check_hex[i] != str_data[i]:
                        self.is_data = True
                        break
        except TypeError:
            str_data = [j for i in [list(hex(d)[2:].zfill(16)) for d in data] for j in i]
            for i in range(0, len(self.check_hex)):
                if '0' <= self.check_hex[i]  <= '9':
                    if self.check_hex[i] != str(hex(data[i % 16]))[i+2]:
                        self.is_data = True
                        break
        values = []
        for a in self.args:
            values.append(a.func(data))
        copy = self.copy()
        copy.values = values
        copy.__dict__.update({self.args[i].name: values[i] for i in range(0, len(values))})
        return copy

    def __str__(self):
        str_args = ""
        for i in range(0, len(self.args)):
            str_args += str(self.args[i].name)
            str_args += ' = '
            try:
                str_args += str(hex(self.values[i]))
            except Exception:
                str_args += str(self.values[i])
            if i != len(self.args) - 1:
                str_args += ", "
        return (self.name + "(" + str_args + ")" ) if not self.is_data else "-- ? --"

def mask(x, arg):
    val = 0
    output_mask = 0xFF
    input_mask = 0x1
    first_mask = -1
    for i in range(0, 8):
        if arg & input_mask != 0:
            val = val | output_mask
            if first_mask == -1:
                first_mask = i
        input_mask = input_mask << 1
        output_mask = output_mask << 8
    x = x & val
    x = x >> first_mask * 8
    return x

class G_MTX(Enum):
    G_MTX_NOPUSH = 0x00
    G_MTX_PUSH = 0x01
    G_MTX_MUL = 0x00
    G_MTX_LOAD = 0x02
    G_MTX_MODELVIEW = 0x00
    G_MTX_PROJECTION = 0x04

class G_MWWD(Enum):
    G_MW_MATRIX = 0x00
    G_MW_NUMLIGHT = 0x02
    G_MW_CLIP = 0x04
    G_MW_SEGMENT = 0x06
    G_MW_FOG = 0x08
    G_MW_LIGHTCOL = 0x0A
    G_MW_FORCEMTX = 0x0C
    G_MW_PERSPNORM = 0x0E

class G_MWMEM(Enum):
    G_MV_MMTX = 2
    G_MV_PMTX = 6
    G_MV_VIEWPORT = 8
    G_MV_LIGHT = 10
    G_MV_POINT = 12
    G_MV_MATRIX = 14

opcode_data = {
        0: Opcode("gsDPNoOpTag", "00000000tttttttt", Arg("tag", lambda x: mask(x, 0x0F))),
        1: Opcode("gsSPVertex", "010nn0aavvvvvvvv",
            Arg("vaddr", lambda x: mask(x, 0x0F)),
            Arg("numv", lambda x: mask(x, 0x60) >> 4),
            Arg("vbidx", lambda x: (mask(x, 0x10) >> 1) - (mask(x, 0x60) >> 8))),
        2: Opcode("gsSPModifyVertex", "02wwnnnnvvvvvvvv",
            Arg("vbidx", lambda x: mask(x, 0x30)/2), 
            Arg("where", lambda x: mask(x, 0x40)), 
            Arg("val", lambda x: mask(x, 0x0F))),
        3: Opcode("gsSPCullDisplayList", "0300vvvv0000wwww",
            Arg("vfirst", lambda x: mask(x, 0x30)/2), 
            Arg("vlast", lambda x: mask(x, 0x03)/2)),
        5: Opcode("gsSP1Triangle", "05aabbcc00000000",
            Arg("v0", lambda x: mask(x, 0x40)/2), 
            Arg("v1", lambda x: mask(x, 0x20)/2), 
            Arg("v2", lambda x: mask(x, 0x10)/2)),
        6: Opcode("gsSP2Triangle", "06aabbcc00ddeeff",
            Arg("v00", lambda x: mask(x, 0x40)/2), 
            Arg("v01", lambda x: mask(x, 0x20)/2), 
            Arg("v02", lambda x: mask(x, 0x10)/2),
            Arg("v10", lambda x: mask(x, 0x04)/2),
            Arg("v11", lambda x: mask(x, 0x02)/2), 
            Arg("v12", lambda x: mask(x, 0x01)/2)),

        0xD3: Opcode("G_SPECIAL_3", "D3??????????????"),
        0xD4: Opcode("G_SPECIAL_2", "D2??????????????"),
        0xD5: Opcode("G_SPECIAL_1", "D1??????????????"),

        0xD7: Opcode("gsSPTexture", "D700nnssssttttBB",
            Arg("scaleS", lambda x: mask(x, 0x18)),
            Arg("scaleT", lambda x: mask(x, 0x06)),
            Arg("level", lambda x: (x & 0x31) >> 3),
            Arg("tile", lambda x: (x & 0x3)),
            Arg("on", lambda x: mask(x, 0x20))),
        0xD8: Opcode("gsSPPopMatrixN", "D8380002aaaaaaaa",
            Arg("which", lambda x: 0),
            Arg("num", lambda x: mask(x, 0x0F) * 64)),
        0xD9: Opcode("gsSPGeomentryMode", "D9ccccccssssssss",
            Arg("clearbits", lambda x: ~mask(x, 0x70)),
            Arg("setbits", lambda x: mask(x, 0x0F))),
        0xDA: Opcode("gsSPMatrix", "DA3800ppmmmmmmmm",
            Arg("mtxaddr", lambda x: mask(x, 0x0F)),
            Arg("params", lambda x: (mask(x, 0x10)))),
        0xDB: Opcode("gsMoveWd","DBiioooodddddddd",
            Arg("index", lambda x: (mask(x, 0x40))),
            Arg("offset", lambda x: mask(x, 0x30)),
            Arg("data", lambda x: mask(x, 0x0F))),
        0xDC: Opcode("gsMoveMem", "DCnnooiiaaaaaaaa",
            Arg("size", lambda x: (((mask(x, 0x40) >> 3) + 1) * 8)),
            Arg("index", lambda x: (mask(x, 0x10))),
            Arg("offset", lambda x: mask(x, 0x20) * 8),
            Arg("address", lambda x: mask(x, 0x0F))),
        0xDE: Opcode("gsSPBranch/DisplayList", "DEpp0000dddddddd",
            Arg("branchOrDisplay", lambda x: mask(x, 0x40)),
            Arg("address", lambda x: mask(x, 0x0F))),
        0xDF: Opcode("gsSPEndDisplayList", "DF00000000000000"),
        0xE0: Opcode("gsSpNoOp", "E000000000000000"),
        0xE1: Opcode("gsDPWord", "E1000000hhhhhhhh",
            Arg("wordhi", lambda x: mask(x, 0x0F))),
        0xE2: Opcode("gsSPSetOtherMode", "E200ssnndddddddd",
            Arg("const", lambda x: 0xE2),
            Arg("shift", lambda x: 32 - mask(x, 0x02) - (mask(x, 0x01) - 1)),
            Arg("length", lambda x: mask(x, 0x01) + 1),
            Arg("Idata", lambda x: mask(x, 0x0F))),
        0xE3: Opcode("gsSPSetOtherMode", "E300ssnndddddddd",
            Arg("const", lambda x: 0xE3),
            Arg("sIhift", lambda x: 32 - mask(x, 0x02) - (mask(x, 0x01) - 1)),
            Arg("length", lambda x: mask(x, 0x01) + 1),
            Arg("data", lambda x: mask(x, 0x0F))),
        0xE4: Opcode("gsSPTextireRectangle", "E4xxxyyy0iXXXYYYE1000000ssssttttF1000000ddddeeee",
            Arg("ulx", lambda x: mask(x[0], 0x06) >> 24),
            Arg("uly", lambda x: mask(x[0], 0x03) & 0xFFF),
            Arg("lrxI", lambda x: mask(x[0], 0x60) >> 24),
            Arg("lry", lambda x: mask(x[0], 0x30) & 0xFFF),
            Arg("tile", lambda x: mask(x[0], 0x08)),
            Arg("uls", lambda x: mask(x[1], 0x0C)),
            Arg("ult", lambda x: mask(x[1], 0x03)),
            Arg("dsdx", lambda x: mask(x[2], 0x0C)),
            Arg("dtdy", lambda x: mask(x[2], 0x03))),
        0xE5: Opcode("gsSPTextireRectangleFlip", "E4xxxyyy0iXXXYYYE1000000ssssttttF1000000ddddeeee",
            Arg("ulx", lambda x: mask(x[0], 0x06) >> 24),
            Arg("uly", lambda x: mask(x[0], 0x03) & 0xFFF),
            Arg("lrx", lambda x: mask(x[0], 0x60) >> 24),
            Arg("lry", lambda x: mask(x[0], 0x30) & 0xFFF),
            Arg("tile", lambda x: mask(x[0], 0x08)),
            Arg("uls", lambda x: mask(x[1], 0x0C)),
            Arg("ult", lambda x: mask(x[1], 0x03)),
            Arg("dsdx", lambda x: mask(x[2], 0x0C)),
            Arg("dtdy", lambda x: mask(x[2], 0x03))),
        0xE6: Opcode("gsDPLoadSync", "E600000000000000"),
        0xE7: Opcode("gsDPPipeSync", "E700000000000000"),
        0xE8: Opcode("gsDPTileSync", "E800000000000000"),
        0xE9: Opcode("gsDPFullSync", "E900000000000000"),
        0xEA: Opcode("gsDPSetKeyGB", "EAwwwxxxccssddtt",
            Arg("centerG", lambda x: mask(x, 0x08)),
            Arg("scaleG", lambda x: mask(x, 0x04)),
            Arg("widthG", lambda x: mask(x, 0x60) >> 8),
            Arg("centerB", lambda x: mask(x, 0x02)),
            Arg("scaleB", lambda x: mask(x, 0x01)),
            Arg("widthB", lambda x: mask(x, 0x30) & 0xFFF)),
        0xEB: Opcode("gsDPSetKeyR", "EB0000000wwwccss",
            Arg("centerR", lambda x: mask(x, 0x02)),
            Arg("widthR", lambda x: mask(x, 0x0C)),
            Arg("scaleR", lambda x: mask(x, 0x01))),
        0xF7: Opcode("gsDPSetFillColor", "F7000000cccccccc",
            Arg("color", lambda x: mask(x, 0x0F))),
        0xF8: Opcode("gsDPSetFogColor", "F8000000rrggbbaa",
            Arg("R", lambda x: mask(x, 0x08)),
            Arg("G", lambda x: mask(x, 0x04)),
            Arg("B", lambda x: mask(x, 0x02)),
            Arg("A", lambda x: mask(x, 0x01))),
        0xF9: Opcode("gsDPBlendColor", "F9000000rrggbbaa",
            Arg("R", lambda x: mask(x, 0x08)),
            Arg("G", lambda x: mask(x, 0x04)),
            Arg("B", lambda x: mask(x, 0x02)),
            Arg("A", lambda x: mask(x, 0x01))),
        0xFA: Opcode("gsDPSetPrimColor", "FA000000rrggbbaa",
            Arg("minlevel", lambda x: mask(x, 0x20)),
            Arg("lodfrac", lambda x: mask(x, 0x10)),
            Arg("R", lambda x: mask(x, 0x08)),
            Arg("G", lambda x: mask(x, 0x04)),
            Arg("B", lambda x: mask(x, 0x02)),
            Arg("A", lambda x: mask(x, 0x01))),
        0xFB: Opcode("gsDPSetEnvColor", "FB000000rrggbbaa",
            Arg("R", lambda x: mask(x, 0x08)),
            Arg("G", lambda x: mask(x, 0x04)),
            Arg("B", lambda x: mask(x, 0x02)),
            Arg("A", lambda x: mask(x, 0x01))),
        0xFD: Opcode("gsDPSetTextureImage", "FD0wwwiiiiiiiiFS",
            Arg("fmt", lambda x: mask(x, 0x40) >> 20),
            Arg("siz", lambda x: (mask(x, 0x40) >> 12) & 0x3),
            Arg("width", lambda x: mask(x, 0x30)),
            Arg("imgaddr", lambda x: mask(x, 0x0F))),
        0xFE: Opcode("gsDPSetDepthImage", "FE000000iiiiiiii",
            Arg("imgaddr", lambda x: mask(x, 0x0F))),
        0xFF: Opcode("gsDPSetColorImage", "FF0wwwiiiiiiiiFS",
            Arg("fmt", lambda x: mask(x, 0x40) >> 20),
            Arg("siz", lambda x: (mask(x, 0x40) >> 12) & 0x3),
            Arg("width", lambda x: mask(x, 0x30)),
            Arg("imgaddr", lambda x: mask(x, 0x0F)))



}


iterator = iter(all_data)
line = 0

opcodes = []

while(True):
    data = ""
    try:
        data = next(iterator)
    except StopIteration:
        break

    code = mask(int.from_bytes(data, 'big'), 0x80)
    if code in opcode_data:
        if(code in [0xE4, 0xE5]):
            multi_line = [int.from_bytes(data, 'big')]
            multi_line.append( int.from_bytes(next(iterator), 'big'))
            multi_line.append( int.from_bytes(next(iterator), 'big'))
            opcode.load_data(multi_line)
            line += 3
        elif(code == 4 or code == 0xDD):
            print("\n\n\nTODO code 4\n\n\n")
            line += 1
        elif(code == 7):
            print("Converting quad to 2 triangles")
            code = 6
            opcode_raw = opcode_data[code]
            opcode = opcode_raw.load_data(int.from_bytes(data, 'big'))
            line += 1
        else:
            opcode_raw = opcode_data[code]
            opcode = opcode_raw.load_data(int.from_bytes(data, 'big'))
            line += 1
    else:
        line += 1
        opcode = None

    opcodes.append(opcode)

for opcode in opcodes:
    if opcode != None and opcode.name == "gsSPVertex" and not opcode.is_data:
        start_offset = int(mask(opcode.vaddr, 0x07) / 8)
        for line in range(start_offset, start_offset + opcode.numv):
            opcodes[line] = " -- VERTEX DATA -- "

for line, opcode in enumerate(opcodes):
    print(str(hex(line)) + "  " + str(opcode))


