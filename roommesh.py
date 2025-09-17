"""
roommesh.py
-----------
Author: Joel Nelems
Last revision: 8/8/2025
Project version: 1.0

There isn't much support for the RoomMesh file type. This module converts RoomMesh data into a much easier
to work with Python class, containing data for meshes, collision, triggers, and points. The parsing function
can take a RoomMesh and save its data to the class instance, which can then be used to create new conversion
tools. Similarly, the write function can take the data stored in the class instance and generate a new
RoomMesh that can be used within SCP: Containment Breach.
"""

# Import modules
from abc import abstractmethod
import struct
import sys
from typing import BinaryIO, TextIO

# Define helper functions
def read_byte(file: BinaryIO,
              context: str = 'byte data') -> int:
    """
    Reads a single byte from a file and returns the value as an 8-bit integer.

    Args:
        file (BinaryIO): The file to read from.
        context (str): The type of data being read. Used for debugging.

    Returns:
        int: The byte represented as an integer.
    """

    # Read byte
    byte: bytes = file.read(1)

    # Ensure byte read properly
    if len(byte) != 1:
        raise EOFError(f"Unexpected end-of-file while reading {context}.")

    # Convert byte to integer
    return struct.unpack('B', byte)[0]

def read_integer(file: BinaryIO,
              context: str = 'integer data') -> int:
    """
    Reads a 32-bit integer from a file and returns the value. Always little-endian and unsigned.

    Args:
        file (BinaryIO): The file to read from.
        context (str): The type of data being read. Used for debugging.

    Returns:
        int: The integer read.
    """

    # Read integer
    integer_bytes: bytes = file.read(4)

    # Ensure integer read properly
    if len(integer_bytes) != 4:
        raise EOFError(f"Unexpected end-of-file while reading {context}.")

    # Convert bytes to integer
    return struct.unpack('<I', integer_bytes)[0]

def read_float(file: BinaryIO,
              context: str = 'float data') -> float:
    """
    Reads a 32-bit float from a file and returns the value. Always little-endian.

    Args:
        file (BinaryIO): The file to read from.
        context (str): The type of data being read. Used for debugging.

    Returns:
        float: The float read.
    """

    # Read float
    float_bytes: bytes = file.read(4)

    # Ensure float read properly
    if len(float_bytes) != 4:
        raise EOFError(f"Unexpected end-of-file while reading {context}.")

    # Convert bytes to float
    return struct.unpack('<f', float_bytes)[0]

def read_string(file: BinaryIO,
                context: str = 'string data') -> str:
    """
    Reads an integer and string from a file and returns the string. Always ASCII.

    Args:
        file (BinaryIO): The file to read from.
        context (str): The type of data being read. Used for debugging.
    """

    # Read string length
    string_length: int = read_integer(file, context)

    # Read string
    string_bytes: bytes = file.read(string_length)

    # Ensure string read properly
    if len(string_bytes) < string_length:
        raise EOFError(f"Unexpected end-of-file while reading {context}.")

    # Convert bytes to string
    return string_bytes.decode('ascii')

def write_byte(file: BinaryIO,
               value: int,
               context: str = 'byte data') -> None:
    """
    Writes a single byte to a file.

    Args:
        file (BinaryIO): The file to write to.
        value (int): The value to write. Must be between 0 and 255 (inclusive).
        context (str): The type of data being written. Used for debugging.

    Returns:
        None.
    """

    # Convert integer to bytes
    value_bytes: bytes = struct.pack('B', value)

    # Write byte value
    if file.write(value_bytes) != 1:
        raise OSError(f"Unable to write byte for {context}")

def write_integer(file: BinaryIO,
                value: int,
                context: str = 'integer data') -> None:
    """
    Writes a 32-bit integer to a file. Always little-endian and unsigned.

    Args:
        file (BinaryIO): The file to write to.
        value (int): The value to write. Must be between 0 and 4,294,967,295 (inclusive).
        context (str): The type of data being written. Used for debugging.

    Returns:
        None.
    """

    # Convert integer to bytes
    value_bytes: bytes = value.to_bytes(4, 'little', signed=False)

    # Write integer value
    if file.write(value_bytes) < 4:
        raise OSError(f"Unable to write integer for {context}")

def write_float(file: BinaryIO,
                value: float,
                context: str = 'float data') -> None:
    """
    Writes a 32-bit float to a file. Always little-endian.

    Args:
        file (BinaryIO): The file to write to.
        value (float): The value to write.
        context (str): The type of data being written. Used for debugging.

    Returns:
        None.
    """

    # Convert float to bytes
    value_bytes: bytes = struct.pack('<f', value)

    # Write float value
    if file.write(value_bytes) < 4:
        raise OSError(f"Unable to write float for {context}")

def write_string(file: BinaryIO,
                string: str,
                context: str = 'string data') -> None:
    """
    Writes a string to a file. Always ASCII.

    Args:
        file (BinaryIO): The file to write to.
        string (str): The string to write.
        context (str): The type of data being written. Used for debugging.
    """

    # Write string length
    write_integer(file, len(string), f"{context} length")

    # Convert string to bytes
    string_bytes: bytes = string.encode('ascii')

    # Write string
    if file.write(string_bytes) < len(string):
        raise OSError(f"Unable to write string for {context}")

# Define classes
class Texture:
    """
    Stores the data for a texture in a RoomMesh file.
    """

    def __init__(self, layer_ID: int = 1,
                 filename: str = '') -> None:
        """
        Creates a Texture instance.

        Args:
            layer_ID (int): The Texture's texture type.
            filename (str): The Texture's filename.

        Returns:
            None.
        """

        # Define Texture attributes
        self.layer_ID: int = layer_ID
        self.filename: str = filename

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the texture data from an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get layer ID
        self.layer_ID = read_byte(file, 'texture layer ID')

        # Handle empty texture
        if self.layer_ID == 0:
            # Set empty filename and return
            self.filename = ''
            return

        # Get filename
        self.filename = read_string(file, 'texture_filename')

    def write(self, file: BinaryIO) -> None:
        """
        Writes the texture data to an object in an RoomMesh file.

        Args:
             file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Handle empty texture
        if self.layer_ID == 0:
            write_byte(file, 0, 'empty texture')
            return

        # Write layer ID
        write_byte(file, self.layer_ID, 'texture layer ID')

        # Write filename length and filename
        write_string(file, self.filename, 'texture filename')

class Coordinate3:
    """
    Stores the data for a 3D coordinate in a RoomMesh file.
    """

    def __init__(self, x: float = 0.0,
                 y: float = 0.0,
                 z: float = 0.0) -> None:
        """
        Creates a Coordinate3 instance.

        Args:
            x (float): The x-position of the Coordinate3.
            y (float): The y-position of the Coordinate3.
            z (float): The z-position of the Coordinate3.

        Returns:
            None.
        """

        # Define Coordinate3 attributes
        self.x: float = x
        self.y: float = y
        self.z: float = z

    @property
    def pos(self) -> tuple[float, float, float]:
        """
        Returns the Coordinate3 as a tuple of floats.

        Returns:
            tuple[float, float, float]: The position of the Coordinate3.
        """

        # Return position
        return self.x, self.y, self.z

    def set_pos(self, x: float,
                y: float,
                z: float) -> None:
        """
        Sets the Coordinate3's position.

        Args:
            x (float): The x-position of the Coordinate3.
            y (float): The y-position of the Coordinate3.
            z (float): The z-position of the Coordinate3.

        Returns:
            None.
        """

        # Set position
        self.x = x
        self.y = y
        self.z = z

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the position data from an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position data
        self.set_pos(x=read_float(file, 'x-position'),
                     z=read_float(file, 'z-position'),
                     y=read_float(file, 'y-position'))

    def write(self, file: BinaryIO) -> None:
        """
        Writes the position data for an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write position data
        write_float(file, self.x, 'x-position')
        write_float(file, self.z, 'z-position')
        write_float(file, self.y, 'y-position')

class UV:
    """
    Stores the data for a UV coordinate in a RoomMesh file.
    """

    def __init__(self, u: float = 0.0,
                 v: float = 0.0) -> None:
        """
        Creates a UV instance.

        Args:
            u (float): The u-position of the UV.
            v (float): The v-position of the UV.

        Returns:
            None.
        """

        # Define UV attributes
        self.u: float = u
        self.v: float = v

    @property
    def pos(self) -> tuple[float, float]:
        """
        Returns the UV as a tuple of floats.

        Returns:
            tuple[float, float]: The position of the UV.
        """

        # Return position
        return self.u, self.v

    def set_pos(self, u: float,
                v: float) -> None:
        """
        Sets the UV's position.

        Args:
            u (float): The u-position of the UV.
            v (float): The v-position of the UV.

        Returns:
            None.
        """

        # Set position
        self.u = u
        self.v = v

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the UV data from an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get uv data
        self.set_pos(read_float(file, 'u-position'),
                     read_float(file, 'v-position'))

    def write(self, file: BinaryIO) -> None:
        """
        Writes the UV data for an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write UV data
        write_float(file, self.u, 'u-position')
        write_float(file, self.v, 'v-position')

class Color:
    """
    Stores the data for a color in a RoomMesh file.
    """

    def __init__(self, r: int = 0,
                 g: int = 0,
                 b: int = 0) -> None:
        """
        Creates a Color instance.

        Args:
            r (int): The red value of the Color.
            g (int): The green value of the Color.
            b (int): The blue value of the Color.

        Returns:
            None.
        """

        # Define Color attributes
        self.r: int = r
        self.g: int = g
        self.b: int = b

    @property
    def rgb(self) -> tuple[int, int, int]:
        """
        Returns the Color as a tuple of integers.

        Returns:
            tuple[int, int, int]: The RGB data of the Color.
        """

        # Return RGB
        return self.r, self.g, self.b

    def set_rgb(self, r: int,
                g: int,
                b: int) -> None:
        """
        Sets the Color's RGB values.

        Args:
            r (int): The red value.
            g (int): The green value.
            b (int): The blue value.

        Returns:
            None.
        """

        # Set RGB values
        self.r = r
        self.g = g
        self.b = b

    def parse_as_bytes(self, file: BinaryIO) -> None:
        """
        Parses the color data from an object in a RoomMesh file in the format 'BBB'.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get color data
        self.set_rgb(read_byte(file, 'red value'),
                     read_byte(file, 'green value'),
                     read_byte(file, 'blue value'))

    def parse_as_string(self, file: BinaryIO) -> None:
        """
        Parses the color data from an object in a RoomMesh file in the format 'R G B'.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get color data
        color_string: str = read_string(file, 'color string')
        self.set_rgb(*map(int, color_string.split()))

    def write_as_bytes(self, file: BinaryIO) -> None:
        """
        Writes the color data for an object in a RoomMesh file in the format 'BBB'.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write color data
        write_byte(file, self.r, 'red value')
        write_byte(file, self.g, 'green value')
        write_byte(file, self.b, 'blue value')

    def write_as_string(self, file: BinaryIO) -> None:
        """
        Writes the color data for an object in a RoomMesh file in the format 'R G B'.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write color string length and color string
        color_string: str = f"{self.r} {self.g} {self.b}"
        write_string(file, color_string, "color string")

class Angle:
    """
    Stores the data for an angle in a RoomMesh file.
    """

    def __init__(self, pitch: float = 0.0,
                 yaw: float = 0.0,
                 roll: float = 0.0) -> None:
        """
        Creates an Angle instance.

        Args:
            pitch (float): The angle's rotation around the vertical axis.
            yaw (float): The angle's rotation around the side axis.
            roll (float): The angle's rotation around the forward axis.

        Returns:
            None.
        """

        # Define Angle attributes
        self.pitch: float = pitch
        self.yaw: float = yaw
        self.roll: float = roll

    @property
    def angle(self) -> tuple[float, float, float]:
        """
        Returns the Angle as a tuple of floats.

        Returns:
            tuple[float, float, float]: The angle data of the Angle.
        """

        # Return angle
        return self.pitch, self.yaw, self.roll

    def set_angle(self, pitch: float,
                yaw: float,
                roll: float) -> None:
        """
        Sets the Angle's angle values.

        Args:
            pitch (float): The angle's rotation around the vertical axis.
            yaw (float): The angle's rotation around the side axis.
            roll (float): The angle's rotation around the forward axis.

        Returns:
            None.
        """

        # Set Angle values
        self.pitch = pitch
        self.yaw = yaw
        self.roll = roll

    def parse_as_bytes(self, file: BinaryIO) -> None:
        """
        Parses the angle data from an object in a RoomMesh file in the format '<fff'.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get angle data
        self.set_angle(read_float(file, 'pitch value'),
                       read_float(file, 'yaw value'),
                       read_float(file, 'roll value'))

    def parse_as_string(self, file: BinaryIO) -> None:
        """
        Parses the angle data from an object in a RoomMesh file in the format 'P Y R'. These values are
        assumed to be integers.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get angle data
        angle_string: str = read_string(file, 'angle string')
        self.set_angle(*map(int, angle_string.split()))

    def write_as_bytes(self, file: BinaryIO) -> None:
        """
        Writes the angle data for an object in a RoomMesh file in the format '<fff'.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write angle data
        write_float(file, self.pitch, 'pitch value')
        write_float(file, self.yaw, 'yaw value')
        write_float(file, self.roll, 'roll value')

    def write_as_string(self, file: BinaryIO) -> None:
        """
        Writes the angle data for an object in a RoomMesh file in the format 'P Y R'. These values will be
        converted to integers.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write angle string length and angle string
        angle_string: str = f"{round(self.pitch)} {round(self.yaw)} {round(self.roll)}"
        write_string(file, angle_string, "angle string")

class Scale:
    """
    Stores the data for a 3D scale in a RoomMesh file.
    """

    def __init__(self, x_scale: float = 1.0,
                 y_scale: float = 1.0,
                 z_scale: float = 1.0) -> None:
        """
        Creates a Scale instance.

        Args:
            x_scale (float): The x-scale of the Scale.
            y_scale (float): The y-scale of the Scale.
            z_scale (float): The z-scale of the Scale.

        Returns:
            None.
        """

        # Define Scale attributes
        self.x_scale: float = x_scale
        self.y_scale: float = y_scale
        self.z_scale: float = z_scale

    @property
    def scale(self) -> tuple[float, float, float]:
        """
        Returns the Scale as a tuple of floats.

        Returns:
            tuple[float, float, float]: The scale of the Scale.
        """

        # Return scale
        return self.x_scale, self.y_scale, self.z_scale

    def set_scale(self, x_scale: float = 0.0,
                 y_scale: float = 0.0,
                 z_scale: float = 0.0) -> None:
        """
        Sets the Scale's scale.

        Args:
            x_scale (float): The x-scale of the Scale.
            y_scale (float): The y-scale of the Scale.
            z_scale (float): The z-scale of the Scale.

        Returns:
            None.
        """

        # Set scale
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the scale data from an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get scale data
        self.set_scale(read_float(file, 'x-scale'),
                     read_float(file, 'y-scale'),
                     read_float(file, 'z-scale'))

    def write(self, file: BinaryIO) -> None:
        """
        Writes the scale data for an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write scale data
        write_float(file, self.x_scale, 'x-scale')
        write_float(file, self.y_scale, 'y-scale')
        write_float(file, self.z_scale, 'z-scale')

class Vertex:
    """
    Stores data for a vertex in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Vertex instance.

        Returns:
            None.
        """

        # Define Vertex attributes
        self.pos: Coordinate3 = Coordinate3()
        self.uv_1: UV = UV()
        self.uv_2: UV = UV()
        self.color: Color = Color()

    def set_pos(self, x: float,
                y: float,
                z: float) -> None:
        """
        Sets the Vertex's position.

        Args:
            x (float): The x-position of the Vertex.
            y (float): The y-position of the Vertex.
            z (float): The z-position of the Vertex.

        Returns:
            None.
        """

        # Set position
        self.pos.set_pos(x, y, z)

    def set_uv_1(self, u: float,
                v: float) -> None:
        """
        Sets the first texture's UV's position.

        Args:
            u (float): The u-position of the UV.
            v (float): The v-position of the UV.

        Returns:
            None.
        """

        # Set position
        self.uv_1.u = u
        self.uv_1.v = v

    def set_uv_2(self, u: float,
                 v: float) -> None:
        """
        Sets the second texture's UV's position.

        Args:
            u (float): The u-position of the UV.
            v (float): The v-position of the UV.

        Returns:
            None.
        """

        # Set position
        self.uv_2.u = u
        self.uv_2.v = v

    def set_color(self, r: int,
                g: int,
                b: int) -> None:
        """
        Sets the Vertex's RGB values.

        Args:
            r (int): The red value.
            g (int): The green value.
            b (int): The blue value.

        Returns:
            None.
        """

        # Set RGB values
        self.color.set_rgb(r, g, b)

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the vertex data from an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Parse coordinate data
        self.pos.parse(file)

        # Parse UV data
        self.uv_1.parse(file)
        self.uv_2.parse(file)

        # Parse color data
        self.color.parse_as_bytes(file)

    def write(self, file: BinaryIO):
        """
        Writes the vertex data to an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write position data
        self.pos.write(file)

        # Write UV data
        self.uv_1.write(file)
        self.uv_2.write(file)

        # Write color data
        self.color.write_as_bytes(file)

class Triangle:
    """
    Stores data for a triangle in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Triangle instance.

        Returns:
            None.
        """

        # Save Triangle attributes
        self.index_1: int = 0
        self.index_2: int = 0
        self.index_3: int = 0

    @property
    def indices(self) -> tuple[int, int, int]:
        """
        Returns the Triangle as a tuple of vertex indices.

        Returns:
            tuple[int, int, int]: The vertex indices of the Triangle.
        """

        # Return indices
        return self.index_1, self.index_2, self.index_3

    def set_indices(self, index_1: int,
                    index_2: int,
                    index_3: int) -> None:
        """
        Sets the Triangle's vertex indices.

        Args:
            index_1 (int): The index of the first vertex.
            index_2 (int): The index of the second vertex.
            index_3 (int): The index of the third vertex.

        Returns:
            None.
        """

        # Set indices
        self.index_1 = index_1
        self.index_2 = index_2
        self.index_3 = index_3

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the triangle data from an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get vertex index data
        self.set_indices(read_integer(file, "triangle index 1"),
                         read_integer(file, "triangle index 2"),
                         read_integer(file, "triangle index 3"))

    def write(self, file: BinaryIO) -> None:
        """
        Writes the triangle data to an object in a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write vertex index data
        write_integer(file, self.index_1)
        write_integer(file, self.index_2)
        write_integer(file, self.index_3)

class Object:
    """
    Stores data for an object in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates an Object instance.

        Returns:
            None.
        """

        # Define Object attributes
        self.textures: list[Texture] = []
        self.vertices: list[Vertex] = []
        self.triangles: list[Triangle] = []

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the object data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get textures
        for _ in range(2):
            # Get texture
            texture: Texture = Texture()
            texture.parse(file)
            self.textures.append(texture)

        # Get vertex count
        vertex_count: int = read_integer(file, 'object vertex count')

        # Get vertices
        for _ in range(vertex_count):
            # Get vertex
            vertex: Vertex = Vertex()
            vertex.parse(file)
            self.vertices.append(vertex)

        # Get triangle count
        triangle_count: int = read_integer(file, 'object triangle count')

        # Get triangles
        for _ in range(triangle_count):
            # Get triangle
            triangle: Triangle = Triangle()
            triangle.parse(file)
            self.triangles.append(triangle)

    def write(self, file: BinaryIO) -> None:
        """
        Writes the object data to a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Ensure object has the correct number of textures
        while len(self.textures) < 2:
            # Append empty texture
            self.textures.insert(0, Texture())

        # Write textures
        for texture in self.textures:
            texture.write(file)

        # Write vertex count
        write_integer(file, len(self.vertices), 'object vertex count')

        # Write vertices
        for vertex in self.vertices:
            vertex.write(file)

        # Write triangle count
        write_integer(file, len(self.triangles), 'object triangle count')

        # Write triangles
        for triangle in self.triangles:
            triangle.write(file)

class Collision:
    """
    Stores data for collision in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Collision instance.

        Returns:
            None.
        """

        # Define collision attributes
        self.vertices: list[Coordinate3] = []
        self.triangles: list[Triangle] = []

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the collision data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get vertex count
        vertex_count: int = read_integer(file, 'collision vertex count')

        # Get vertices
        for _ in range(vertex_count):
            # Get vertex
            vertex: Coordinate3 = Coordinate3()
            vertex.parse(file)
            self.vertices.append(vertex)

        # Get triangle count
        triangle_count: int = read_integer(file, 'collision triangle count')

        # Get triangles
        for _ in range(triangle_count):
            # Get triangle
            triangle: Triangle = Triangle()
            triangle.parse(file)
            self.triangles.append(triangle)

    def write(self, file: BinaryIO) -> None:
        """
        Writes the collision data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write vertex count
        write_integer(file, len(self.vertices), 'collision vertex count')

        # Write vertices
        for vertex in self.vertices:
            # Write vertex
            vertex.write(file)

        # Write triangle count
        write_integer(file, len(self.triangles), 'collision triangle count')

        # Write triangles
        for triangle in self.triangles:
            # Write triangle
            triangle.write(file)

class TriggerBox:
    """
    Stores data for a trigger box in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a TriggerBox instance.

        Returns:
            None.
        """

        # Define trigger box attributes
        self.collisions: list[Collision] = []
        self.name: str = ''

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the trigger box data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get collision count
        collision_count: int = read_integer(file, 'trigger box collision count')

        # Get collisions
        for _ in range(collision_count):
            # Get collision
            collision: Collision = Collision()
            collision.parse(file)
            self.collisions.append(collision)

        # Get trigger name
        self.name = read_string(file, 'trigger box name')

    def write(self, file: BinaryIO) -> None:
        """
        Writes the trigger box data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write collision count
        write_integer(file, len(self.collisions), 'trigger box collision count')

        # Write collisions
        for collision in self.collisions:
            # Write collision
            collision.write(file)

        # Write trigger name
        write_string(file, self.name, 'trigger box name')

class Point:
    """
    Base class for all Point objects. Primarily for typing.
    """

    def __init__(self, classname: str) -> None:
        """
        Creates a Point instance.

        Args:
            classname (str): The name of the point type.

        Returns:
            None.
        """

        # Define point attributes
        self.classname: str = classname
        self.pos: Coordinate3 = Coordinate3()

    @abstractmethod
    def parse(self, file: BinaryIO) -> None:
        """
        Abstract method for parsing point data.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """
        pass

    @abstractmethod
    def write(self, file: BinaryIO) -> None:
        """
        Abstract method for writing point data.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """
        pass

class Screen(Point):
    """
    Stores data for a screen point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Screen instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('screen')

        # Define Point attributes.
        self.pos: Coordinate3 = Coordinate3()
        self.path: str = ''

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the screen data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position
        self.pos.parse(file)

        # Get image path
        self.path = read_string(file, 'screen image path')

    def write(self, file: BinaryIO) -> None:
        """
        Writes the screen data to a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'screen classname')

        # Write position
        self.pos.write(file)

        # Write image path
        write_string(file, self.path, 'screen image path')

class Waypoint(Point):
    """
    Stores data for a waypoint point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Waypoint instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('waypoint')

        # Define Waypoint attributes
        self.pos: Coordinate3 = Coordinate3()

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the waypoint data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position
        self.pos.parse(file)

    def write(self, file: BinaryIO) -> None:
        """
        Writes the waypoint data to a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'waypoint classname')

        # Write position
        self.pos.write(file)

class Light(Point):
    """
    Stores data for a light point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Light instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('light')

        # Define light attributes
        self.pos: Coordinate3 = Coordinate3()
        self.range: float = 0.0
        self.color: Color = Color()
        self.intensity: float = 0.0

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the light data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position
        self.pos.parse(file)

        # Get range
        self.range = read_float(file, 'light range')

        # Get color
        self.color.parse_as_string(file)

        # Get intensity
        self.intensity = read_float(file, 'light intensity')

    def write(self, file: BinaryIO) -> None:
        """
        Writes the light data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'light classname')

        # Write position
        self.pos.write(file)

        # Write range
        write_float(file, self.range, 'light range')

        # Write color
        self.color.write_as_string(file)

        # Write intensity
        write_float(file, self.intensity, 'light intensity')

class Spotlight(Point):
    """
    Stores data for a light point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Spotlight instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('spotlight')

        # Define Spotlight attributes
        self.pos: Coordinate3 = Coordinate3()
        self.range: float = 0.0
        self.color: Color = Color()
        self.intensity: float = 0.0
        self.angle: Angle = Angle()
        self.inner_angle: int = 0
        self.outer_angle: int = 0

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the spotlight data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position
        self.pos.parse(file)

        # Get range
        self.range = read_float(file, 'spotlight range')

        # Get color
        self.color.parse_as_string(file)

        # Get intensity
        self.intensity = read_float(file, 'spotlight intensity')

        # Get angle
        self.angle.parse_as_string(file)

        # Parse inner cone angle
        self.inner_angle = read_integer(file, 'spotlight inner angle')

        # Parse outer cone angle
        self.outer_angle = read_integer(file, 'spotlight outer angle')

    def write(self, file: BinaryIO) -> None:
        """
        Writes the spotlight data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'spotlight classname')

        # Write position
        self.pos.write(file)

        # Write range
        write_float(file, self.range, 'spotlight range')

        # Write color
        self.color.write_as_string(file)

        # Write intensity
        write_float(file, self.intensity, 'spotlight intensity')

        # Write angle
        self.angle.write_as_string(file)

        # Write inner cone angle
        write_integer(file, self.inner_angle, 'spotlight inner angle')

        # Write outer cone angle
        write_integer(file, self.outer_angle, 'spotlight outer angle')

class SoundEmitter(Point):
    """
    Stores data for a sound emitter point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a SoundEmitter instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('soundemitter')

        # Define SoundEmitter attributes
        self.pos: Coordinate3 = Coordinate3()
        self.sound: int = 0
        self.range: float = 0.0

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the sound emitter data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position
        self.pos.parse(file)

        # Get sound
        self.sound = read_integer(file, 'sound emitter sound')

        # Get range
        self.range = read_float(file, "sound emitter range")

    def write(self, file: BinaryIO) -> None:
        """
        Writes the sound emitter data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'sound emitter classname')

        # Write position
        self.pos.write(file)

        # Write sound
        write_integer(file, self.sound, "sound emitter sound")

        # Write range
        write_float(file, self.range, 'sound emitter range')

class PlayerStart(Point):
    """
    Stores data for a player start point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a PlayerStart instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('playerstart')

        # Define PlayerStart attributes
        self.pos: Coordinate3 = Coordinate3()
        self.angle: Angle = Angle()

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the player start data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get position
        self.pos.parse(file)

        # Get angle
        self.angle.parse_as_string(file)

    def write(self, file: BinaryIO) -> None:
        """
        Writes the player start data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'player start classname')

        # Write position
        self.pos.write(file)

        # Write angle
        self.angle.write_as_string(file)

class Model(Point):
    """
    Stores data for a model point in a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a Model instance.

        Returns:
            None.
        """

        # Initialize superclass
        super().__init__('model')

        # Define Model attributes
        self.path: str = ''
        self.pos: Coordinate3 = Coordinate3()
        self.angle: Angle = Angle()
        self.scale: Scale = Scale()

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the model data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get path
        self.path = read_string(file, "model path")

        # Get position
        self.pos.parse(file)

        # Get angle
        self.angle.parse_as_bytes(file)

        # Get scale
        self.scale.parse(file)

    def write(self, file: BinaryIO) -> None:
        """
        Writes the model data to a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write classname
        write_string(file, self.classname, 'model classname')

        # Write path
        write_string(file, self.path, "model path")

        # Write position
        self.pos.write(file)

        # Write angle
        self.angle.write_as_bytes(file)

        # Write scale
        self.scale.write(file)

class RoomMesh:
    """
    Stores data for a RoomMesh file.
    """

    def __init__(self) -> None:
        """
        Creates a RoomMesh instance.

        Returns:
            None.
        """

        # Define RoomMesh attributes
        self.signature: str = ''
        self.objects: list[Object] = []
        self.collisions: list[Collision] = []
        self.triggers: list[TriggerBox] = []
        self.points: list[Point] = []

    def parse(self, file: BinaryIO) -> None:
        """
        Parses the data from a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary read mode.

        Returns:
            None.
        """

        # Get signature
        self.signature = read_string(file, "file signature")

        # Ensure signature matches expected signature
        if self.signature not in ("RoomMesh", "RoomMesh.HasTriggerBox"):
            raise ValueError(f"Unexpected signature string: {self.signature}.")

        # Get object count
        object_count: int = read_integer(file, "object count")

        # Get objects
        for _ in range(object_count):
            # Get object
            mesh: Object = Object()
            mesh.parse(file)
            self.objects.append(mesh)

        # Get collision count
        collision_count: int = read_integer(file, 'collision count')

        # Get collisions
        for _ in range(collision_count):
            # Get collision
            collision: Collision = Collision()
            collision.parse(file)
            self.collisions.append(collision)

        # Get trigger boxes
        if self.signature == 'RoomMesh.HasTriggerBox':
            # Get trigger count
            trigger_count: int = read_integer(file, 'trigger count')

            # Parse triggers
            for _ in range(trigger_count):
                # Get trigger
                trigger: TriggerBox = TriggerBox()
                trigger.parse(file)
                self.triggers.append(trigger)

        # Get point count
        point_count: int = read_integer(file, "point count")

        # Get points
        for _ in range(point_count):
            # Get classname
            classname: str = read_string(file, "point classname")

            # Match point class
            match classname:
                # Get point
                case 'screen':
                    screen: Screen = Screen()
                    screen.parse(file)
                    self.points.append(screen)
                case 'waypoint':
                    waypoint: Waypoint = Waypoint()
                    waypoint.parse(file)
                    self.points.append(waypoint)
                case 'light':
                    light: Light = Light()
                    light.parse(file)
                    self.points.append(light)
                case 'spotlight':
                    spotlight: Spotlight = Spotlight()
                    spotlight.parse(file)
                    self.points.append(spotlight)
                case 'soundemitter':
                    sound_emitter: SoundEmitter = SoundEmitter()
                    sound_emitter.parse(file)
                    self.points.append(sound_emitter)
                case 'playerstart':
                    player_start: PlayerStart = PlayerStart()
                    player_start.parse(file)
                    self.points.append(player_start)
                case 'model':
                    model: Model = Model()
                    model.parse(file)
                    self.points.append(model)

    def write(self, file: BinaryIO) -> None:
        """
        Writes the data for a RoomMesh file.

        Args:
            file (BinaryIO): The RoomMesh file opened in binary write mode.

        Returns:
            None.
        """

        # Write signature
        write_string(file, self.signature, "file signature")

        # Write object count
        write_integer(file, len(self.objects), "object count")

        # Write objects
        for mesh in self.objects:
            # Write object
            mesh.write(file)

        # Write collision count
        write_integer(file, len(self.collisions), "collision count")

        # Write collisions
        for collision in self.collisions:
            collision.write(file)

        # Write trigger boxes
        if len(self.triggers) > 0:
            # Write trigger count
            write_integer(file, len(self.triggers), "trigger count")

            # Write triggers
            for trigger in self.triggers:
                # Write trigger
                trigger.write(file)

        # Write point count
        write_integer(file, len(self.points), "point count")

        # Write points
        for point in self.points:
            # Write point
            point.write(file)

        # Write EOF
        write_string(file, "EOF", "end of file")

    def write_info(self, file: TextIO) -> None:
        """
        Writes the information of a RoomMesh file to a text file in a human-readable format.

        Args:
            file (TextIO): The file to write to.

        Returns:
            None.
        """

        # Write file signature
        file.write(f"File signature: {self.signature}\n")
        file.write("\n")

        # Write object count
        file.write(f"Object count: {len(self.objects)}\n")

        # Write object info
        for obj_index, obj in enumerate(self.objects):
            # Write object index
            file.write(f"Object {obj_index}:\n")

            # Write texture info
            for tex_index, texture in enumerate(obj.textures):
                # Write texture info
                file.write(f"\tTexture ID: {texture.layer_ID}\n")
                file.write(f"\tTexture name: {texture.filename}\n")
            file.write("\n")

            # Write vertex count
            file.write(f"\tVertex count: {len(obj.vertices)}\n")

            # Write vertex info
            for vert_index, vertex in enumerate(obj.vertices):
                # Write vertex index
                file.write(f"\tVertex {vert_index}:\n")

                # Write vertex data
                file.write(f"\t\tPos: {vertex.pos.pos}\n")
                file.write(f"\t\tDiffuse UV: {vertex.uv_1.pos}\n")
                file.write(f"\t\tLightmap UV: {vertex.uv_2.pos}\n")
                file.write(f"\t\tColor: {vertex.color.rgb}\n")
            file.write("\n")

            # Write triangle count
            file.write(f"\tTriangle count: {len(obj.triangles)}\n")

            # Write triangle info
            for tri_index, triangle in enumerate(obj.triangles):
                # Write triangle index
                file.write(f"\tTriangle {tri_index}:\n")

                # Write triangle data
                file.write(f"\t\tVertex indices: {triangle.indices}\n")
            file.write("\n")

        # Write collision count
        file.write(f"Collision count: {len(self.collisions)}:\n")

        # Write collision info
        for col_index, collision in enumerate(self.collisions):
            # Write collision index
            file.write(f"Collision {col_index}:\n")

            # Write vertex count
            file.write(f"\tVertex count: {len(collision.vertices)}\n")

            # Write vertex info
            for vert_index, vertex in enumerate(collision.vertices):
                # Write vertex index
                file.write(f"\tVertex {vert_index}:\n")

                # Write vertex data
                file.write(f"\t\tPosition: {vertex.pos}\n")
            file.write("\n")

            # Write triangle count
            file.write(f"\tTriangle count: {len(collision.triangles)}\n")

            # Write triangle info
            for tri_index, triangle in enumerate(collision.triangles):
                # Write triangle index
                file.write(f"\tTriangle {tri_index}\n")

                # Write triangle data
                file.write(f"\t\tVertex indices: {triangle.indices}\n")
            file.write("\n")

        # Write trigger count
        file.write(f"Trigger count: {len(self.triggers)}\n")

        # Write trigger info
        for trig_index, trigger in enumerate(self.triggers):
            # Write trigger name and index
            file.write(f"Trigger {trig_index} - {trigger.name}:\n")

            # Write collision info
            for col_index, collision in enumerate(trigger.collisions):
                # Write collision index
                file.write(f"\tCollision {col_index}:\n")

                # Write vertex count
                file.write(f"\t\tVertex count: {len(collision.vertices)}\n")

                # Write vertex info
                for vert_index, vertex in enumerate(collision.vertices):
                    # Write vertex index
                    file.write(f"\t\tVertex {vert_index}:\n")

                    # Write vertex data
                    file.write(f"\t\t\tPosition: {vertex.pos}\n")
                file.write("\n")

                # Write triangle count
                file.write(f"\t\tTriangle count: {len(collision.triangles)}\n")

                # Write triangle info
                for tri_index, triangle in enumerate(collision.triangles):
                    # Write triangle index
                    file.write(f"\t\tTriangle {tri_index}\n")

                    # Write triangle data
                    file.write(f"\t\t\tVertex indices: {triangle.indices}\n")
                file.write("\n")

        # Write point count
        file.write(f"Point count: {len(self.points)}\n")

        # Write point info
        for point_index, point in enumerate(self.points):
            # Write point type and index
            file.write(f"Point {point_index} - {point.classname}:\n")

            # Write point info
            if isinstance(point, Screen):
                # Write screen data
                file.write(f"\tPosition: {point.pos}\n")
                file.write(f"\tImage: {point.path}\n")
            if isinstance(point, Waypoint):
                # Write waypoint data
                file.write(f"\tPosition: {point.pos}\n")
            if isinstance(point, Light):
                # Write light data
                file.write(f"\tPosition: {point.pos}\n")
                file.write(f"\tIntensity: {point.intensity}\n")
                file.write(f"\tRange: {point.range}\n")
                file.write(f"\tColor: {point.color.rgb}\n")
            if isinstance(point, Spotlight):
                # Write spotlight data
                file.write(f"\tPosition: {point.pos}\n")
                file.write(f"\tIntensity: {point.intensity}\n")
                file.write(f"\tRange: {point.range}\n")
                file.write(f"\tColor: {point.color.rgb}\n")
                file.write(f"\tInner angle: {point.inner_angle}\n")
                file.write(f"\tOuter angle: {point.outer_angle}\n")
                file.write(f"\tRotation: {point.angle.angle}\n")
            if isinstance(point, SoundEmitter):
                # Write sound emitter data
                file.write(f"\tPosition: {point.pos}\n")
                file.write(f"\tRange: {point.range}\n")
                file.write(f"\tSound ID: {point.sound}\n")
            if isinstance(point, Model):
                # Write model data
                file.write(f"\tPosition: {point.pos}\n")
                file.write(f"\tModel: {point.path}\n")
                file.write(f"\tRotation: {point.angle.angle}\n")
                file.write(f"\tScale: {point.scale.scale}\n")

# Testing
def main(filename: str) -> int:
    """
    The entry point for RoomMesh conversion testing.

    Args:
        filename (str): The filename of the RoomMesh file.

    Returns:
        int: The exit code of the program.
    """

    try:
        # Create empty RoomMesh
        room: RoomMesh = RoomMesh()

        # Attempt to parse file data and reconstruct it
        with open(filename, 'rb') as file:
            room.parse(file)
        with open('info.txt', 'w') as file:
            room.write_info(file)

        # Return successfully
        return 0
    except Exception as e:
        # Print error
        print(e)

        # Exit unsuccessfully
        return 1

# Ensure direct execution
if __name__ == "__main__":
    # Exit with exit code
    exit(main(sys.argv[1]))