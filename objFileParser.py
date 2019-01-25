import sys

def hexstr(val, minlen):
    return str(hex(int(val)))[2:].zfill(minlen)

class Vector4f():

    def __init__(self, x, y, z, w):
        self.x = x
        self.y = y
        self.z = z
        self.w = w

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ", " + str(self.w) + ")"

    def __eq__(self, other):
        return other != None and type(self) == type(other) and self.x == other.x and self.y == other.y and self.z == other.z and self.w == other.w

class Vector3f():

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def to_int64(self, scale=1):
        out = 0
        out = out | ((int(self.x*scale) & 0xFFFF) << 48)
        out = out | ((int(self.y*scale) & 0xFFFF) << 32)
        out = out | ((int(self.z*scale) & 0xFFFF) << 16)
        return out

    def to_int32(self, scale=1):
        out = 0
        out = out | ((int(self.x*scale) & 0xFF) << 24)
        out = out | ((int(self.y*scale) & 0xFF) << 16)
        out = out | ((int(self.z*scale) & 0xFF) << 8)
        return out
    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ", " + str(self.z) + ")"

    def __eq__(self, other):
        return other != None and type(self) == type(other) and self.x == other.x and self.y == other.y and self.z == other.z

class Vector2f():

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_2fixed10_5(self):
        out = 0
        out = out | (int((self.x * 1023.96875*2-1023.96875) * 32) & 0xFFFF) << 16
        out = out | (int((self.y * 1023.96875*2-1023.96875) * 32) & 0xFFFF)
        return out

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __eq__(self, other):
        return other != None and type(self) == type(other) and self.x == other.x and self.y == other.y


class Vertex():

    def __init__(self, coordinate=None, texture=None, normal=None, color=None):
        self.coordinate = coordinate
        self.texture = texture
        self.normal = normal
        self.color = color


    def update_vertex(self, vector, v_type):
        #Type 0 for coordinates, 1 for normals, 2 for textures, 3 for colors
        if v_type == 0:
            self.coordinate = vector
        elif v_type == 1:
            self.normal = vector
        elif v_type == 2:
            self.texture = vector
        elif v_type == 3:
            self.color = vector

    def to_F3DZEX(self, scale=1):
        out = ""
        out += hexstr(self.coordinate.to_int64(scale), 16) + "\n"
        out += hexstr(self.texture.to_2fixed10_5(), 8) if self.texture != None else "00000000"
        alpha = 0xFF if self.color == None or type(self) != "Vector4f" else self.color.w
        shading = self.normal
        shading = Vector3f(shading.x, shading.y, shading.z) 
        out += hexstr(shading.to_int32(127) >> 8, 6)
        out += hexstr(alpha, 2)
        return out

    def __str__(self):
        out = ""
        if self.coordinate != None:
            out += " Coordinate: " + str(self.coordinate)
        if self.normal != None:
            out += " Normal: " + str(self.normal)
        if self.texture != None:
            out += " Texture: " + str(self.texture)
        if self.color != None:
            out += " Color: " + str(self.color)

        return out

    def __eq__(self, other):
        return other != None and self.coordinate == other.coordinate and self.normal == other.normal and self.texture == other.texture and self.color == other.color

class Face():
    
    def __init__(self, vindx1, vindx2, vindx3):
        self.vindx1 = vindx1
        self.vindx2 = vindx2
        self.vindx3 = vindx3


    def to_F3DZEX_05(self):
        out = "05"
        out += hexstr(self.vindx1*2, 2)
        out += hexstr(self.vindx2*2, 2)
        out += hexstr(self.vindx3*2, 2)
        out += "00000000"
        return out

    def to_F3DZEX_06(self, face):
        face1out = "06" + self.to_F3DZEX_05()[2:8]
        face2out = "00" + face.to_F3DZEX_05()[2:8]
        return face1out + face2out


    def __str__(self):
        return "(" + str(self.vindx1) + ", " + str(self.vindx2) + ", " + str(self.vindx3) + ")"

try:
    import pywavefront
except ImportError:
    print("You need to pywavefront module for parsing objects. run pip install PyWavefront")
    sys.exit(1)

if len(sys.argv)<2:
    print("Please pass in the .obj file to parse")
    sys.exit(1)

path = sys.argv[1]
try:
    scene = pywavefront.Wavefront(path)
except FileNotFoundError:
    print("Could not find file: " + path);
    sys.exit(1)

vertices = []


# Iterate vertex data collected in each material
for name, material in scene.materials.items():
    # Contains the vertex format (string) such as "T2F_N3F_V3F"
    vertex_format_str = material.vertex_format.split("_")
    #Type 0 for coordinates, 1 for normals, 2 for textures, 3 for colors
    vertex_format = []
    for v_format in vertex_format_str:
        if v_format[0] == 'V':
            d_type = 0
        elif v_format[0] == 'N':
            d_type = 1
        elif v_format[0] == 'T':
            d_type = 2
        elif v_format[0] == 'C':
            d_type = 3

        d_len = int(v_format[1])

        vertex_format.append( (d_type, d_len))
        
    print(str(vertex_format))
    print(str(material.vertices))
    vertex_len = sum(v[1] for v in vertex_format)
    for index in range(0, int(len(material.vertices) / vertex_len)):
        vertex = Vertex()
        offset = 0
        for d_type in vertex_format:
            if d_type[1] == 4:
                data = Vector3f(material.vertices[index * vertex_len + offset],
                        material.vertices[index * vertex_len + offset + 1],
                        material.vertices[index * vertex_len + offset + 2],
                        material.vertices[index * vertex_len + offset + 3])
            elif d_type[1] == 3:
                data = Vector3f(material.vertices[index * vertex_len + offset],
                        material.vertices[index * vertex_len + offset + 1],
                        material.vertices[index * vertex_len + offset + 2])
            elif d_type[1] == 2:
                data = Vector2f(material.vertices[index * vertex_len + offset],
                        material.vertices[index * vertex_len + offset + 1])

            offset += d_type[1]

            vertex.update_vertex(data, d_type[0])
        vertices.append(vertex)


print(len(vertices))


vertex_buffer = []
faces = []
for index in range(0, int(len(vertices)/3)):
    vbix = [-1, -1, -1]
    for i in range(0, 3):
        v = vertices[index * 3 + i]
        try:
            v_index = vertex_buffer.index(v)
            vbix[i] = v_index
        except ValueError:
            vertex_buffer.append(v)
            vbix[i] = len(vertex_buffer)-1
    print(str(vbix))
    faces.append( Face(*vbix))

print("faces: " + str(len(faces)))
print("verticies: " + str(len(vertex_buffer)))

for v in vertex_buffer:
    print(v)

for f in faces:
    print(f)

for v in vertex_buffer:
    print(v.to_F3DZEX(0x50))

print("\n\n")

for i in range(0, int(len(faces)/2)):
    print(faces[2*i].to_F3DZEX_06(faces[2*i+1]))

if len(faces) % 2 != 0:
    print(faces[-1].to_F3DZEX_05())


#for face in faces:
#    print(face.to_F3DZEX_05())
