# Import modules
from pathlib import Path
import bpy
from bpy.props import StringProperty
from bpy.types import (Context, FloatColorAttribute, Image, Material, Menu, Mesh, MeshPolygon, MeshVertex,
                       Node,NodeSocket, Object as BObject, Operator, MeshUVLoopLayer)
from bpy_extras.io_utils import ExportHelper
from mathutils import Vector
from . import roommesh
from .roommesh_import import report

def transform_pos(obj: bpy.types.Object,
                  local: tuple[float, float, float] | None = None) -> tuple[float, float, float]:
    """
    Applies the necessary transforms for converting Blender meshes to RoomMesh ones.

    Args:
        obj (Object): The Blender object to apply transforms to.
        local (tuple[float, float, float] | None): The origin of the object. If none is provided, world origin is
        used.

    Returns:
        Vector: The resulting position.
    """

    # Get world position
    if local is None:
        world_position = obj.matrix_world.translation
    else:
        world_position = obj.matrix_world @ Vector(local)

    # Return scaled world position
    return world_position * 160.0

# Define material functions
def get_diffuse(obj: bpy.types.Object) -> bpy.types.Image | None:
    """
    Gets the diffuse map off an object, if one exists.

    Args:
        obj (Object): The object to use.

    Returns:
        Image | None: The diffuse map, if one exists.
    """

    # Ensure object has material available
    if not obj.data.materials:
        # Write warning
        report("Attempted to get textures from an object without any", "Material Error", "ERROR")

        # Return None
        return None

    # Retrieve material
    material: Material | None = obj.active_material or next((m for m in obj.data.materials if m), None)

    # Ensure material has node data
    if not material.use_nodes:
        # Write warning
        report("Attempted to get textures from an object without any nodes",
               "Material Error", "ERROR")

        # Return None
        return None

    # Save BSDF node
    principled: Node | None = None

    # Loop through material nodes
    for node in material.node_tree.nodes:
        # Search for BSDF
        if node.type == "BSDF_PRINCIPLED":
            # Save BSDF and stop search
            principled = node
            break

    # Return if no principled is found
    if not principled:
        # Write warning
        report("Attempted to get textures from an object without a BSDF",
               "Material Error", "WARNING")

        # Return None
        return None

    # Attempt to get diffuse link
    diffuse_link: NodeSocket | None = principled.inputs.get('Base Color')

    # Ensure diffuse link was found and linked
    if diffuse_link and diffuse_link.is_linked:
        # Get diffuse node
        diffuse_node: Node = diffuse_link.links[0].from_node
        print("Dif link")

        # Ensure node is an image
        if diffuse_node.type == "TEX_IMAGE":
            # Get image
            image: Image = diffuse_node.image
            print("node image")

            # Return image
            return image

    # Write warning
    report("Unable to get diffuse texture", "Material Error", "ERROR")

    # Return None
    return None

def export_image(image: bpy.types.Image, out_dir: Path) -> None:
    """
    Exports an image into a given directory.

    Args:
        image (Image): The image to export.
        out_dir (Path): The place to store the image.

    Returns:
        None.
    """

# Define conversion functions
def convert_texture(image: bpy.types.Image,
                    layer_ID: int) -> roommesh.Texture:
    """
    Converts an image into a Texture object.

    Args:
        image (Image): The image to convert.
        layer_ID (int): The type of map the image represents.

    Returns:
        Texture: The created Texture.
    """

    # Create new Texture
    texture: roommesh.Texture = roommesh.Texture(layer_ID, image.name_full)

    # Return Texture
    return texture

# Define object functions
def normalize_color(r: float,
                    g: float,
                    b: float) -> tuple[int, int, int]:
    """
    Converts a Blender color using floats to a RoomMesh color of 3 integers.

    Args:
        r (float): The red value.
        g (float): The green value.
        b (float): The blue value.

    Returns:
        tuple[int, int, int]: The RoomMesh color.
    """

    # Return color
    return int(r * 255), int(g * 255), int(b * 255)

def convert_vertex(mesh: Mesh,
                   poly_index: int,
                   vertex_index: int,
                   vertex: MeshVertex) -> roommesh.Vertex:
    """
    Converts a Blender Vertex into a RoomMesh Vertex.

    Args:
        mesh (Mesh): The Mesh the vertex is attached to.
        poly_index (int): The index of the polygon containing the vertex.
        vertex_index (int): The index of the vertex being converted.
        vertex (MeshVertex): The Vertex to convert.

    Returns:
        room Vertex: The created Vertex.
    """

    # Create empty Vertex
    room_vertex: roommesh.Vertex = roommesh.Vertex()

    # Set Vertex position
    room_vertex.set_pos(*tuple(vertex.co))

    # Create UV data
    uv_layer: bpy.types.MeshUVLoopLayer | None = mesh.uv_layers.active

    # Loop through mesh loops
    if uv_layer is not None:
        for loop_index in mesh.polygons[poly_index].loop_indices:
            # Check if vertex is found
            if mesh.loops[loop_index].vertex_index == vertex_index:
                # Set vertex UVs
                room_vertex.set_uv_1(*tuple(uv_layer.data[loop_index].uv))
                break

    # Set color data
    vertex_colors: FloatColorAttribute = mesh.color_attributes.active_color

    # Check if vertex colors exist
    if vertex_colors is None:
        # Default to white
        room_vertex.set_color(255, 255, 255)

        # Return vertex
        return room_vertex

    # Get Vertex color
    color: tuple[float, float, float, float] = vertex_colors.data[vertex_index].color
    room_vertex.set_color(*normalize_color(color[0], color[1], color[2]))

    # Return Vertex
    return room_vertex

def convert_object(obj: bpy.types.Object, filepath: Path) -> roommesh.Object:
    """
    Converts a Blender Object into a RoomMesh Object, complete with texture and mesh data.

    Args:
        obj (blend Object): The Blender Object to convert.
        filepath (Path): Place that the roommesh is saved, for texture saving.

    Returns:
        room Object: The created RoomMesh Object.
    """

    # Create new Object
    room_obj: roommesh.Object = roommesh.Object()

    # Get textures
    diffuse_image: bpy.types.Image | None = get_diffuse(obj)
    if diffuse_image:
        diffuse: roommesh.Texture = convert_texture(diffuse_image, 1)

        # Assign textures
        room_obj.textures.append(diffuse)

    # Ensure triangles are updated
    if not obj.data.loop_triangles:
        obj.data.calc_loop_triangles()

    # Get UV data
    uv_layer = obj.data.uv_layers.active
    first_uv: dict = {}

    if uv_layer is not None:
        for poly in obj.data.polygons:
            for loop_index in poly.loop_indices:
                vi = obj.data.loops[loop_index].vertex_index
                if vi not in first_uv:
                    u, v = uv_layer.data[loop_index].uv
                    first_uv[vi] = (u, 1.0 - v)

    # Get vertices
    positions = [transform_pos(obj, vertex.co) for vertex in obj.data.vertices]
    triangles = [tuple(tri.vertices) for tri in obj.data.loop_triangles]

    # Assign vertices
    for vi, v in enumerate(obj.data.vertices):
        # Create vertex
        vertex = roommesh.Vertex()
        vertex.set_pos(*transform_pos(obj, tuple(v.co)))

        if vi in first_uv:
            u, v = first_uv[vi]
            vertex.set_uv_1(u, v)

        # Append vertex
        room_obj.vertices.append(vertex)

    # Assign faces
    for tri in obj.data.loop_triangles:
        # Create triangle
        triangle = roommesh.Triangle()
        triangle.set_indices(*tri.vertices)

        # Append triangle
        room_obj.triangles.append(triangle)

    # Return RoomMesh Object
    return room_obj

def convert_collision(obj: BObject) -> roommesh.Collision:
    """
    Converts a Blender Object into a RoomMesh Collision, complete with mesh data.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        Collision: The created RoomMesh Collision.
    """

    # Create new Object
    collision: roommesh.Collision = roommesh.Collision()

    # Get vertices
    positions = [transform_pos(obj, vertex.co) for vertex in obj.data.vertices]
    triangles = [tuple(tri.vertices) for tri in obj.data.loop_triangles]

    # Assign vertices
    for index, position in enumerate(positions):
        # Create vertex
        vertex = roommesh.Vertex()
        vertex.set_pos(*positions[index])

        # Append vertex
        collision.vertices.append(vertex.pos)

    # Assign triangles
    for face in triangles:
        # Create triangle
        triangle = roommesh.Triangle()
        triangle.set_indices(*face)

        # Append triangle
        collision.triangles.append(triangle)

    # Return RoomMesh Object
    return collision

def convert_trigger_box(room: roommesh.RoomMesh,
                        obj: bpy.types.Object) -> None:
    """
    Converts a Blender Object into a RoomMesh Trigger Box. Added to the room automatically.

    Args:
        room (RoomMesh): The full RoomMesh, checking for existing trigger collection.
        obj (blend Object): The Blender Object to convert.

    Returns:
        None.
    """

    # Get collision object
    collision: roommesh.Collision = convert_collision(obj)

    # Loop through triggers
    for trigger in room.triggers:
        # Look for existing trigger
        if obj.roommesh.trigger_name == trigger.name:
            # Append to existing trigger
            trigger.collisions.append(collision)

            # Return
            return

    # Create new trigger
    trigger: roommesh.TriggerBox = roommesh.TriggerBox()

    # Set trigger properties
    trigger.name = obj.roommesh.trigger_name
    trigger.collisions.append(collision)

    # Add trigger to room
    room.triggers.append(trigger)

def convert_screen(obj: bpy.types.Object) -> roommesh.Screen:
    """
    Converts a Blender Object into a RoomMesh Screen.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        Screen: The created RoomMesh Screen.
    """

    # Create new Screen
    screen: roommesh.Screen = roommesh.Screen()



    # Get screen data
    screen.pos.set_pos(*transform_pos(obj))

    # Ensure screen type is image
    if getattr(obj, "empty_display_type", "") != "IMAGE":
        return screen

    screen.path = str(Path(obj.data.filepath).name)

    # Return screen
    return screen

def convert_waypoint(obj: bpy.types.Object) -> roommesh.Waypoint:
    """
    Converts a Blender Object into a RoomMesh Waypoint.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        Waypoint: The created RoomMesh Waypoint.
    """

    # Create new Waypoint
    waypoint: roommesh.Waypoint = roommesh.Waypoint()

    # Get waypoint data
    waypoint.pos.set_pos(*transform_pos(obj))

    # Return waypoint
    return waypoint

def convert_light(obj: bpy.types.Object) -> roommesh.Light:
    """
    Converts a Blender Object into a RoomMesh Light.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        Light: The created RoomMesh Light.
    """

    # Create new Light
    light: roommesh.Light = roommesh.Light()

    # Get light data
    light.pos.set_pos(*transform_pos(obj))
    if obj.data.use_custom_distance:
        light.range = obj.data.cutoff_distance
    else:
        light.range = 40.0
    light.color.set_rgb(*normalize_color(obj.data.color[0], obj.data.color[1], obj.data.color[2]))
    light.intensity = obj.data.energy / 50

    # Return light
    return light

def convert_spotlight(obj: bpy.types.Object) -> roommesh.Spotlight:
    """
    Converts a Blender Object into a RoomMesh Spotlight.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        Spotlight: The created RoomMesh Spotlight.
    """

    # Create new Spotlight
    spotlight: roommesh.Spotlight = roommesh.Spotlight()

    # Get light data
    spotlight.pos.set_pos(*transform_pos(obj))
    if obj.data.use_custom_distance:
        spotlight.range = obj.data.cutoff_distance
    spotlight.color.set_rgb(*normalize_color(obj.data.color[0], obj.data.color[1], obj.data.color[2]))
    spotlight.intensity = obj.data.energy / 50

    # Get spotlight data
    spotlight.outer_angle = obj.data.spot_size
    spotlight.inner_angle = obj.data.spot_blend * (spotlight.outer_angle if spotlight.outer_angle > 0.0 else 1.0)

    # Return spotlight
    return spotlight

def convert_soundemitter(obj: bpy.types.Object) -> roommesh.SoundEmitter:
    """
    Converts a Blender Object into a RoomMesh Sound Emitter.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        SoundEmitter: The created RoomMesh SoundEmitter.
    """

    # Create new SoundEmitter
    sound_emitter: roommesh.SoundEmitter = roommesh.SoundEmitter()

    # Get sound emitter data
    sound_emitter.pos.set_pos(*transform_pos(obj))
    sound_emitter.sound = obj.roommesh.sound_ID
    sound_emitter.range = obj.data.distance_max

    # Return sound emitter
    return sound_emitter

def convert_playerstart(obj: bpy.types.Object) -> roommesh.PlayerStart:
    """
    Converts a Blender Object into a RoomMesh PlayerStart.

    Args:
        obj (bpy Object): The Blender Object to convert.

    Returns:
        PlayerStart: The created RoomMesh PlayerStart.
    """

    # Create new PlayerStart
    player_start: roommesh.PlayerStart = roommesh.PlayerStart()

    # Get player start data
    player_start.pos.set_pos(*transform_pos(obj))

    # Return player start
    return player_start

# Define export functions
def export_roommesh(context: Context,
                    filepath: Path) -> set[str]:
    """
    Generates and saves a RoomMesh file.

    Args:
        context (Context): The current state of Blender.
        filepath (Path): The path of the file to save.

    Returns:
        set[str]: The result of the export process.
    """

    # Create new RoomMesh
    room: roommesh.RoomMesh = roommesh.RoomMesh()

    # Loop through scene objects
    for obj in context.scene.objects:
        # Match object type
        match obj.type:
            # Handle mesh objects
            case 'MESH':
                # Check if it is collision
                if obj.roommesh.is_collision:
                    # Check if it is a trigger
                    if obj.roommesh.is_trigger:
                        # Add trigger
                        convert_trigger_box(room, obj)

                        # Continue loop
                        continue

                    # Generate collision
                    collision: roommesh.Collision = convert_collision(obj)

                    # Append collision
                    room.collisions.append(collision)

                    # Continue loop
                    continue

                # Generate object
                room_object: roommesh.Object = convert_object(obj, filepath)

                # Append object
                room.objects.append(room_object)

                # Continue loop
                continue
            # Handle empty objects
            case 'EMPTY':
                # Match point name
                match obj.roommesh.role:
                    # Handle screens
                    case 'SCREEN':
                        # Build screen
                        screen: roommesh.Screen = convert_screen(obj)

                        # Append screen
                        room.points.append(screen)

                    # Handle waypoints
                    case 'WAYPOINT':
                        # Build waypoint
                        waypoint: roommesh.Waypoint = convert_waypoint(obj)

                        # Append waypoint
                        room.points.append(waypoint)

                    # Handle player starts
                    case 'PLAYERSTART':
                        # Build player start
                        player_start: roommesh.PlayerStart = convert_playerstart(obj)

                        # Append player start
                        room.points.append(player_start)
            # Handle lights
            case 'LIGHT':
                # Get light type
                if obj.data.type == 'SPOT':
                    # Build spotlight
                    spotlight: roommesh.Spotlight = convert_spotlight(obj)

                    # Append spotlight
                    room.points.append(spotlight)
                else:
                    # Build point light
                    light: roommesh.Light = convert_light(obj)

                    # Append point light
                    room.points.append(light)
            # Handle speakers
            case 'SPEAKER':
                # Build sound emitter
                sound_emitter: roommesh.SoundEmitter = convert_soundemitter(obj)

                # Append sound emitter
                room.points.append(sound_emitter)

    # Check trigger count
    if len(room.triggers) > 0:
        # Write file signature
        room.signature = "RoomMesh.HasTriggerBox"
    else:
        # Write file signature
        room.signature = "RoomMesh"

    # Open RoomMesh file
    with open(filepath, 'wb') as file:
        # Write RoomMesh file
        room.write(file)

    # Return successfully
    return {'FINISHED'}

# Define export classes
class ExportRoomMesh(Operator, ExportHelper):
    """
    Allows the exporting of RoomMesh files in Blender.
    """

    # Set class information
    bl_idname = 'export_scene.roommesh'
    bl_label = "RoomMesh Export"

    # Set file information
    filename_ext = '.rmesh'
    filter_glob: StringProperty(
        default="*.rmesh",
        options={'HIDDEN'}
    )

    # Set menu options
    bl_options = {'PRESET'}

    def execute(self, context: Context) -> set[str]:
        """
        Generates and saves a RoomMesh file.

        Args:
            context (Context): The current state of Blender.

        Returns:
            set[str]: The result of the export process.
        """

        # Attempt export and return result
        try:
            # Get file path
            path: Path = Path(self.filepath).with_suffix(self.filename_ext)

            # Attempt to export
            return export_roommesh(context, path)
        except Exception as e:
            # Report exception
            self.report({'ERROR'}, f"Export failed: {e}")

            # Return unsuccessfully
            return {'CANCELLED'}

# Define menu functions
def menu_func_export(self: Menu,
                     context: Context) -> None:
    """
    Adds the RoomMesh export button to the export menu.

    Args:
        self (Menu): The menu to add to.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Add export option
    self.layout.operator(ExportRoomMesh.bl_idname, text="RoomMesh (.rmesh)")

# Define registration functions
def register() -> None:
    """
    Registers RoomMesh export classes and menus.

    Returns:
        None.
    """

    # Register export classes
    bpy.utils.register_class(ExportRoomMesh)

    # Register operators
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister() -> None:
    """
    Unregisters RoomMesh export classes and menus.

    Returns:
        None.
    """

    # Register operators
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    # Unregister export classes
    bpy.utils.unregister_class(ExportRoomMesh)