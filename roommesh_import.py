# Import modules
import bpy
import math
import mathutils
from pathlib import Path

from . import roommesh
from .bve import direct_x

# Define debug functions
def report(message: str,
           title: str="Notice",
           icon: str="INFO") -> None:
    """
    Reports information, warnings, and errors within the Blender editor.

    Args:
        message (str): The message to display.
        title (str): The title of the message.
        icon (str): The type of message.

    Returns:
        None.
    """

    # Define draw function
    def draw(self: bpy.types.Menu, context: bpy.types.Context) -> None:
        """
        Draws the message.

        Args:
            self (Menu): The menu displaying the message.
            context (Context): The current state of Blender.

        Returns:
            None.
        """

        # Set message text
        for line in message.split('\n'):
            self.layout.label(text=line)

    # Attempt popup
    try:
        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    except Exception as e:
        # Print error
        print(f"Unable to report message: {e}")

        # Default to printing
        print(f"{icon}: {title} - {message}")

# Define RoomMesh conversion functions
def normalize_color(color: roommesh.Color,
                    use_alpha: bool = True) -> tuple[float, float, float] | tuple[float, float, float, float]:
    """
    Takes a RoomMesh Color and converts it into float data, optionally with an alpha value.

    Args:
        color (Color): The RGB data to convert.
        use_alpha (bool): Toggles an alpha value.

    Returns:
        tuple[...]: The normalized RGB(A) data.
    """

    # Return normalized values
    if use_alpha:
        return (color.r / 255.0), (color.g / 255.0), (color.b / 255.0), 1.0
    else:
        return (color.r / 255.0), (color.g / 255.0), (color.b / 255.0)

def transform_mesh(obj: bpy.types.Object, is_point: bool = False) -> None:
    """
    Applies the necessary transforms for converting RoomMesh meshes to Blender ones.

    Args:
        obj (Object): The Blender object to apply transforms to.
        is_point (bool): When enabled, only the object position is affected.

    Returns:
        None.
    """

    # Get scale
    scale: float = 0.00625 # RoomMesh meter -> Blender meter conversion
    scale_matrix: mathutils.Matrix = mathutils.Matrix.Diagonal(mathutils.Vector((scale, scale, scale, 1.0)))

    # Update location
    obj.location = (obj.location[0]*scale, obj.location[1]*scale, obj.location[2]*scale)

    # Check for points
    if is_point or obj.type != "MESH":
        # Return after location update
        return

    # Apply scale
    obj.data.transform(scale_matrix)

    # Apply transformations
    obj.data.update()

# Define collection functions
def create_collection(name: str,
                        parent: bpy.types.Collection | None = None,
                        scene: bpy.types.Scene | None = None) -> bpy.types.Collection | None:
    """
    Creates a new collection in a given scene. If the collection already exists, the existing
    collection is returned.
    
    Args:
        name (str): The name of the collection.
        parent (Collection): The collection to add the new collection to.
        scene (Scene): The scene to add the collection to.
    
    Returns:
        Collection | None: The collection created or retrieved, if any.
    """

    # Get scene if parent isn't provided
    if parent is None:
        # Get valid scene
        scene = scene or bpy.context.scene
        
        # Ensure scene is available
        if scene is None:
            # Report error message
            report("Unable to find parent collection.", title="No Parent Collection", icon="ERROR")

            # Return None
            return None
            
        # Set parent to scene collection
        parent = scene.collection
    
    # Check if collection name exists in parent collection
    existing_collection: bpy.types.Collection | None = parent.children.get(name)
    
    # Check if collection exists
    if existing_collection is not None:
        # Return existing collection
        return existing_collection
    
    # Create new collection if none exists
    collection = bpy.data.collections.new(name)

    # Attempt to link
    try:
        # Link collection to parent
        parent.children.link(collection)
    except RuntimeError:
        # Report error
        report("Unable to link collection.", "Link Failure", "ERROR")

        # Return None
        return None
    
    # Return collection
    return collection

# Define material functions
def load_texture(texture: roommesh.Texture,
                 folder_path: str | Path) -> bpy.types.Image | None:
    """
    Loads a texture image. If the image already exists, no new image is created and the existing one is
    returned.

    Args:
        texture (Texture): The texture to load.
        folder_path (str | Path): The path to where the imported RoomMesh is located.

    Returns:
        Image | None: The image loaded, if found.
    """

    # Early out on empty textures
    if not texture.filename or texture.layer_ID == 0:
        # Print error
        report("Attempted to load empty texture.", "Empty Texture", "ERROR")

        # Return None
        return None

    # Get path
    texture_path: Path = (Path(folder_path) / Path(texture.filename)).resolve()

    # Ensure path exists
    if not texture_path.is_file():
        # Print error message
        report(f"Unable to find image {texture_path}.", "Invalid Path", "ERROR")

        # Return None
        return None

    # Get image
    try:
        # Load image
        image = bpy.data.images.load(filepath=str(texture_path), check_existing=True)
    except RuntimeError:
        # Print error
        report(f"Unable to load image {texture_path}", "Image Failure", "ERROR")

        # Return None
        return None

    # Return new image
    return image

def create_material(name: str) -> bpy.types.Material | None:
    """
    Creates a new material of a given name. If one by that name already exists, the existing material is returned.

    Args:
        name (str): The name of the material.

    Returns:
        Material | None: The material created/loaded.
    """

    # Attempt to get existing material
    material: bpy.types.Material | None = bpy.data.materials.get(name)

    # Check if material exists
    exists: bool = material is not None

    # If no material exists, create a new one
    if not exists:
        # Create new material
        material = bpy.data.materials.new(name)

    # Ensure material was created properly
    if not material:
        # Report error
        report("Unable to create material.", "Material Failure", "ERROR")

    # Ensure nodes are enabled
    if not material.use_nodes:
        # Enable nodes
        material.use_nodes = True

    # Return material
    return material

def give_material(obj: bpy.types.Object,
                  new_material: bpy.types.Material) -> None:
    """
    Gives a material to an object. If the object is unable to have materials, an error is reported. If the object
    already has the material, that material is made active.

    Args:
        obj (bpy Object): The object appending a material to.
        new_material (Material): The material to append.

    Returns:
        None.
    """

    # Ensure object can have materials
    if obj.data is None or not hasattr(obj.data, "materials"):
        # Report error
        report("Object doesn't support materials", "Invalid object", "ERROR")

        # Return
        return

    # Ensure object does not already contain the materials
    for index, existing_material in enumerate(obj.data.materials):
        # Check if material exists
        if new_material is existing_material:
            # Set active material
            obj.active_material_index = index

            # Return
            return

    # Append new material
    obj.data.materials.append(new_material)

    # Set active material
    obj.active_material = new_material

def generate_material(obj: roommesh.Object,
                      name: str,
                      folder_path: str | Path) -> bpy.types.Material | None:
    """
    Creates a material for the RoomMesh object based on its texture data, then returns the generated material.

    Args:
        obj (roommesh Object): The object to generate the material from.
        name (str): The name of the material.
        folder_path (str | Path): The path to the folder containing the RoomMesh file.

    Returns:
        Material: The material generated.
    """

    # Get filename
    diffuse_texture: roommesh.Texture | None = next((texture for texture in obj.textures if
                                                     texture.layer_ID == 1 and texture.filename), None)
    lightmap_texture: roommesh.Texture | None = next((texture for texture in obj.textures if
                                                     texture.layer_ID == 2 and texture.filename), None)
    alpha_texture: roommesh.Texture | None = next((texture for texture in obj.textures if
                                                     texture.layer_ID == 3 and texture.filename), None)

    # Get or create material
    material: bpy.types.Material | None = create_material(name)

    # Ensure material loaded
    if not material:
        # Report error
        report("Unable to create material.", "Material Failure", "ERROR")

        # Return None
        return None

    # Get material data
    tree: bpy.types.NodeTree = material.node_tree
    nodes: bpy.types.Nodes = tree.nodes
    links: bpy.types.NodeLinks = tree.links

    # Clear nodes
    nodes.clear()

    # Create output node
    output: bpy.types.Node = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    # Create BSDF
    principled: bpy.types.Node = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (350, 0)

    # Create links
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # Create image nodes
    diffuse_node: bpy.types.Node | None = None
    lightmap_node: bpy.types.Node | None = None
    alpha_node: bpy.types.Node | None = None

    # Get textures
    if diffuse_texture:
        # Attempt to load image
        image: bpy.types.Image | None = load_texture(diffuse_texture, folder_path)

        # Ensure image loaded
        if image:
            # Generate diffuse node
            diffuse_node = nodes.new("ShaderNodeTexImage")
            diffuse_node.image = image
            diffuse_node.location = (-600, 100)
            diffuse_node.image.colorspace_settings.name = "sRGB"

    if lightmap_texture:
        # Attempt to load image
        image: bpy.types.Image | None = load_texture(lightmap_texture, folder_path)

        # Ensure image loaded
        if image:
            # Generate diffuse node
            lightmap_node = nodes.new("ShaderNodeTexImage")
            lightmap_node.image = image
            lightmap_node.location = (-600, 300)
            lightmap_node.image.colorspace_settings.name = "Non-Color"

    if alpha_texture:
        # Attempt to load image
        image: bpy.types.Image | None = load_texture(alpha_texture, folder_path)

        # Ensure image loaded
        if image:
            # Generate diffuse node
            alpha_node = nodes.new("ShaderNodeTexImage")
            alpha_node.image = image
            alpha_node.location = (-600, 500)
            alpha_node.image.colorspace_settings.name = "Non-Color"

    # Ensure diffuse node loaded
    if diffuse_node:
        # Set diffuse as base color
        links.new(diffuse_node.outputs["Color"], principled.inputs["Base Color"])

    if alpha_node:
        # Set diffuse as base color
        links.new(alpha_node.outputs["Alpha"], principled.inputs["Alpha"])

    # Return new material
    return material

# Mesh functions
def build_mesh(vertex_positions: list[tuple[float, float, float]],
               triangle_indices: list[tuple[int, int, int]],
               name: str) -> bpy.types.Mesh:
    """
    Builds a Blender Mesh using vertex positions and triangle data.

    Args:
        vertex_positions (list[tuple[float, float, float]]): A list of vertex positions.
        triangle_indices (list[tuple[int, int, int]]): A list of vertex indices making up triangles.
        name (str): The name of the mesh.

    Returns:
        Mesh: The new Blender Mesh.
    """

    # Create new mesh
    mesh: bpy.types.Mesh = bpy.data.meshes.new(name)

    # Reverse triangle order to fix inverted face normals
    reversed_indices = [(tri[2], tri[1], tri[0]) for tri in triangle_indices]

    # Build mesh from data
    mesh.from_pydata(vertex_positions, [], reversed_indices)

    # Ensure mesh data is valid
    mesh.validate(clean_customdata=False)

    # Apply mesh transforms
    mesh.update()

    # Return mesh
    return mesh

def build_object(room_obj: roommesh.Object,
                 name: str) -> bpy.types.Object:
    """
    Creates the mesh for a RoomMesh Object and converts it to a Blender Object.

    Args:
        room_obj (Object): The RoomMesh Object data.
        name (str): The name of the new object.

    Returns:
        Object: The new Blender Object.
    """

    # Get object data
    vertex_positions: list[tuple[float, float, float]] = [vertex.pos.pos for vertex in room_obj.vertices]
    triangle_indices: list[tuple[int, int, int]] = [triangle.indices for triangle in room_obj.triangles]

    # Create mesh
    mesh = build_mesh(vertex_positions, triangle_indices, name)

    # Create UV maps
    diffuse_uv: bpy.types.MeshUVLoopLayer = mesh.uv_layers.new(name="DiffuseUVMap")

    # Loop through faces
    for poly in mesh.polygons:
        # Loop through vertex loops
        for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
            # Get vertex index
            vertex_index: int = mesh.loops[loop_index].vertex_index

            # Get UV data
            u, v = room_obj.vertices[vertex_index].uv_1.pos

            # Write UV data
            diffuse_uv.data[loop_index].uv = (u, 1-v)

    # Set active UV layer
    mesh.uv_layers.active = diffuse_uv

    # Create vertex colors
    vertex_colors: bpy.types.FloatColorAttribute = mesh.color_attributes.new(
        name="LightmapColor",
        type="FLOAT_COLOR",
        domain="POINT"
    )

    # Loop through vertices
    for vertex_index, vertex in enumerate(room_obj.vertices):
        # Set vertex color
        vertex_colors.data[vertex_index].color = normalize_color(room_obj.vertices[vertex_index].color)

    # Create new Blender Object
    blend_obj: bpy.types.Object = bpy.data.objects.new(name, mesh)

    # Set object location
    blend_obj.location = (0.0, 0.0, 0.0)

    # Apply transforms
    transform_mesh(blend_obj)

    # Return object
    return blend_obj

# Collision functions
def build_collision(collision: roommesh.Collision,
                    name: str,
                    is_trigger: bool = False,
                    trigger_name: str = '') -> bpy.types.Object:
    """
    Creates the mesh for a RoomMesh collision object and converts it into a Blender object.

    Args:
        collision (Collision): The collision data.
        name (str): The name of the new collision.
        is_trigger (bool): Determines if this collision object is a trigger.
        trigger_name (str): The name of the trigger, if enabled.

    Returns:
        bpy Object: The new Blender Object.
    """

    # Get collision data
    vertex_positions: list[tuple[float, float, float]] = [vertex.pos for vertex in collision.vertices]
    triangle_indices: list[tuple[int, int, int]] = [triangle.indices for triangle in collision.triangles]

    # Create new mesh
    mesh = build_mesh(vertex_positions, triangle_indices, name)

    # Create new object
    new_obj: bpy.types.Object = bpy.data.objects.new(name, mesh)
    new_obj.location = (0.0, 0.0, 0.0)

    # Set collision properties
    new_obj.roommesh.is_collision = True

    # Check if it is a trigger
    if is_trigger:
        # Set trigger toggle
        new_obj.roommesh.is_trigger = True

        # Set trigger name
        new_obj.roommesh.trigger_name = trigger_name

    # Apply transforms
    transform_mesh(new_obj)

    # Return object
    return new_obj

# Define point functions
def build_screen(screen: roommesh.Screen,
                name: str,
                filepath: Path) -> bpy.types.Object:
    """
    Creates an empty image for a screen and returns the new Blender Object.

    Args:
        screen (Screen): The screen data.
        name (str): The name of the new screen.
        filepath (Path): Path of the RoomMesh folder. Used for getting image data.

    Returns:
        Object: The new Blender Object.
    """

    # Create new screen
    screen_empty: bpy.types.Object = bpy.data.objects.new(name, None)

    # Set display type
    screen_empty.empty_display_type = 'IMAGE'

    # Set location
    screen_empty.location = screen.pos.pos

    # Update point UI
    screen_empty.roommesh.role = "SCREEN"

    # Apply transforms
    transform_mesh(screen_empty, True)

    # Attempt to get screen image
    try:
        # Load screen image
        screen_empty.data = bpy.data.images.load(str(filepath.parent / Path(f"screens/{screen.path}")), check_existing=True)
    except RuntimeError:
        # Report error message
        report("Unable to load screen image.", "Screen failure", "ERROR")

    # Return screen
    return screen_empty

def build_waypoint(waypoint: roommesh.Waypoint,
                name: str) -> bpy.types.Object:
    """
    Creates an empty axes for a waypoint and returns the new Blender Object.

    Args:
        waypoint (Waypoint): The waypoint data.
        name (str): The name of the new waypoint.

    Returns:
        Object: The new Blender Object.
    """

    # Create waypoint
    waypoint_empty: bpy.types.Object = bpy.data.objects.new(name, None)

    # Set display
    waypoint_empty.empty_display_type = 'PLAIN_AXES'

    # Set transforms
    waypoint_empty.location = waypoint.pos.pos

    # Set UI
    waypoint_empty.roommesh.role = "WAYPOINT"

    # Apply transforms
    transform_mesh(waypoint_empty, True)

    # Return waypoint
    return waypoint_empty

def build_light(light: roommesh.Light,
                name: str) -> bpy.types.Object:
    """
    Creates a point light and returns the new Blender Object.

    Args:
        light (Light): The light data.
        name (str): The name of the new light.

    Returns:
        Object: The new Blender Object.
    """

    # Create light
    point_light: bpy.types.Light = bpy.data.lights.new(name=name, type="POINT")

    # Set light properties
    point_light.color = normalize_color(light.color, use_alpha=False)
    point_light.energy = light.intensity * 50
    point_light.use_custom_distance = True
    point_light.cutoff_distance = light.range

    # Create light object
    light_obj: bpy.types.Object = bpy.data.objects.new(name, point_light)

    # Set light transforms
    light_obj.location = light.pos.pos

    # Apply transforms
    transform_mesh(light_obj, True)

    # Return light
    return light_obj

def build_spotlight(spotlight: roommesh.Spotlight,
                name: str) -> bpy.types.Object:
    """
    Creates a spotlight and returns the new Blender Object.

    Args:
        spotlight (Spotlight): The spotlight data.
        name (str): The name of the new spotlight.

    Returns:
        Object: The new Blender Object.
    """

    # Create new spotlight
    point_spotlight: bpy.types.Light = bpy.data.lights.new(name=name, type="SPOT")

    # Set light properties
    point_spotlight.color = normalize_color(spotlight.color, use_alpha=False)
    point_spotlight.energy = spotlight.intensity * 50
    point_spotlight.use_custom_distance = True
    point_spotlight.cutoff_distance = spotlight.range

    # Get spotlight data
    outer_deg: float = max(1.0, min(180.0, spotlight.outer_angle))
    inner_deg: float = max(1.0, min(180.0, spotlight.inner_angle))
    ratio = inner_deg / outer_deg if outer_deg > 0.0 else 1.0

    # Set spotlight properties
    point_spotlight.spot_size = math.radians(outer_deg)
    point_spotlight.spot_blend = max(0.0, min(1.0, 1.0 - ratio))

    # Create new object
    spotlight_obj: bpy.types.Object = bpy.data.objects.new(name, point_spotlight)

    # Set position
    spotlight_obj.location = spotlight.pos.pos

    # Set rotation
    spotlight_obj.rotation_euler = (
        math.radians(spotlight.angle.pitch),
        math.radians(spotlight.angle.roll),
        math.radians(spotlight.angle.yaw)
    )

    # Apply transforms
    transform_mesh(spotlight_obj, True)

    # Return spotlight
    return spotlight_obj

def build_soundemitter(sound_emitter: roommesh.SoundEmitter,
                name: str) -> bpy.types.Object:
    """
    Creates a speaker and returns the new Blender Object.

    Args:
        sound_emitter (SoundEmitter): The speaker data.
        name (str): The name of the new speaker.

    Returns:
        Object: The new Blender Object.
    """

    # Create new speaker
    speaker = bpy.data.speakers.new(name)

    # Set speaker properties
    speaker.distance_max = sound_emitter.range

    # Create new object
    speaker_obj = bpy.data.objects.new(name, speaker)

    # Set speaker ui
    speaker_obj.roommesh.sound_ID = sound_emitter.sound

    # Apply transforms
    speaker_obj.location = sound_emitter.pos.pos

    # Transform object
    transform_mesh(speaker_obj, True)

    # Return speaker
    return speaker_obj

def build_playerstart(player_start: roommesh.PlayerStart,
                name: str) -> bpy.types.Object:
    """
    Creates an empty sphere for a player start and returns the new Blender Object.

    Args:
        player_start (SoundEmitter): The player start data.
        name (str): The name of the new object.

    Returns:
        Object: The new Blender Object.
    """

    # Create new start
    start_empty: bpy.types.Object = bpy.data.objects.new(name, None)

    # Set display type
    start_empty.empty_display_type = 'SPHERE'

    # Set location
    start_empty.location = player_start.pos.pos

    # Set rotation
    start_empty.rotation_euler = (
        math.radians(player_start.angle.pitch),
        math.radians(player_start.angle.roll),
        math.radians(player_start.angle.yaw)
    )

    # Set UI
    start_empty.roommesh.role = "PLAYERSTART"

    # Apply transforms
    transform_mesh(start_empty, True)

    # Return start
    return start_empty

def build_model(folder: Path | str,
                filename: Path | str) -> bpy.types.Object | None:
    """
    Attempts to import a .x model using the BVE Import/Export plugin.

    Args:
        folder (Path | str): Path to the folder containing the RoomMesh.
        filename (Path | str): Full name of the .x file.

    Returns:
        Object | None: The object, if converted successfully, otherwise None.
    """

    # Create prop path
    filepath: Path = Path(folder) / Path("props") / Path(filename)

    # Create importer
    importer = direct_x.ImportDirectXXFile()

    # Import object
    model = importer.execute(str(filepath))

    # Ensure object loaded
    if not model:
        # Report error message
        report(f"Unable to load {filename} model.", "Model failure", "ERROR")

        # Return None
        return None

    # Set model property
    model.roommesh.is_model = True
    model.roommesh.model_name = filepath.name

    # Return model
    return model

def import_roommesh(filepath: Path) -> roommesh.RoomMesh | None:
    """
    Imports all objects and data within a RoomMesh file.
    
    Args:
        filepath (Path): The path to the RoomMesh being imported.
    
    Returns:
        RoomMesh: The RoomMesh object created.
    """
    
    # Create path
    filepath: Path = Path(filepath)
    
    # Ensure path exists
    if not filepath.is_file():
        # Report error
        report(f"Unable to find file {filepath}", "Invalid Room", "ERROR")

        # Return None
        return None
    
    # Create RoomMesh
    room: roommesh.RoomMesh = roommesh.RoomMesh()
    
    # Open RoomMesh file
    with filepath.open("rb") as rmesh:
        # Generate data
        room.parse(rmesh)
    
    # Create collections
    room_collection: bpy.types.Collection = create_collection(filepath.stem)
    object_collection: bpy.types.Collection = create_collection("Objects", parent=room_collection)
    collision_collection: bpy.types.Collection = create_collection("Collisions", parent=room_collection)
    trigger_collection: bpy.types.Collection = create_collection("Triggers", parent=room_collection)
    point_collection: bpy.types.Collection = create_collection("Points", parent=room_collection)
    screen_collection: bpy.types.Collection = create_collection("Screens", parent=point_collection)
    waypoint_collection: bpy.types.Collection = create_collection("Waypoints", parent=point_collection)
    light_collection: bpy.types.Collection = create_collection("Lights", parent=point_collection)
    spotlight_collection: bpy.types.Collection = create_collection("Spotlights", parent=point_collection)
    soundemitter_collection: bpy.types.Collection = create_collection("Sound Emitters", parent=point_collection)
    playerstart_collection: bpy.types.Collection = create_collection("Player Starts", parent=point_collection)
    model_collection: bpy.types.Collection = create_collection("Models", parent=point_collection)

    # Save object count
    object_index: int = 0

    # Loop through objects
    for obj in room.objects:
        # Generate materials
        obj_material: bpy.types.Material = (generate_material(
            obj, f"obj_{object_index}_material", filepath.parent))

        # Generate mesh
        obj_mesh: bpy.types.Object = build_object(obj, f"obj_{object_index}")

        # Apply materials
        give_material(obj_mesh, obj_material)

        # Add object to collection
        object_collection.objects.link(obj_mesh)

        # Increment object count
        object_index += 1

    # Save collision count
    collision_index: int = 0

    # Loop through collisions
    for collision in room.collisions:
        # Generate mesh
        collision_mesh: bpy.types.Object = build_collision(
            collision, f"collision_{collision_index}", False)

        # Add collision to collection
        collision_collection.objects.link(collision_mesh)

        # Increment collision count
        collision_index += 1

    # Loop through triggers
    for trigger in room.triggers:
        # Save mesh count
        mesh_index: int = 0

        # Create trigger collection
        trigger_collision_collection: bpy.types.Collection = create_collection(
            f"{trigger.name}", parent=trigger_collection)

        # Loop through trigger collisions
        for collision in trigger.collisions:
            # Generate mesh
            collision_mesh: bpy.types.Object = build_collision(
                collision, f"collision_{mesh_index}", True, f"{trigger.name}_{mesh_index}")

            # Add collision to trigger collection
            trigger_collision_collection.objects.link(collision_mesh)

            # Increment mesh count
            mesh_index += 1

    # Save point counts
    screen_index: int = 0
    waypoint_index: int = 0
    light_index: int = 0
    spotlight_index: int = 0
    soundemitter_index: int = 0
    playerstart_index: int = 0
    model_index: int = 0

    # Loop through points
    for point in room.points:
        # Create screen
        if isinstance(point, roommesh.Screen):
            # Create new screen
            screen = build_screen(point, f"screen_{screen_index}", filepath.parent)

            # Add screen to collection
            screen_collection.objects.link(screen)

            # Increment screen count
            screen_index += 1

        # Create waypoint
        if isinstance(point, roommesh.Waypoint):
            # Create new waypoint
            waypoint = build_waypoint(point, f"waypoint_{waypoint_index}")

            # Add waypoint to collection
            waypoint_collection.objects.link(waypoint)

            # Increment waypoint count
            waypoint_index += 1

        # Create light
        if isinstance(point, roommesh.Light):
            # Create new point light
            light = build_light(point, f"light_{light_index}")

            # Add light to collection
            light_collection.objects.link(light)

            # Increment light count
            light_index += 1

        # Create spotlight
        if isinstance(point, roommesh.Spotlight):
            # Create new spotlight
            spotlight = build_spotlight(point, f"spotlight_{spotlight_index}")

            # Add spotlight to collection
            spotlight_collection.objects.link(spotlight)

            # Increment spotlight index
            spotlight_index += 1

        # Create sound emitter
        if isinstance(point, roommesh.SoundEmitter):
            # Create new sound emitter
            sound_emitter = build_soundemitter(point, f"soundemitter_{soundemitter_index}")

            # Add sound emitter to collection
            soundemitter_collection.objects.link(sound_emitter)

            # Increment sound emitter count
            soundemitter_index += 1

        # Create player start
        if isinstance(point, roommesh.PlayerStart):
            # Create new player start
            start = build_playerstart(point, f"playerstart_{playerstart_index}")

            # Add player start to collection
            playerstart_collection.objects.link(start)

            # Increment sound emitter count
            playerstart_index += 1

        # Import models
        if isinstance(point, roommesh.Model):
            # Import model object
            model = build_model(filepath.parent, point.path)

            # Set model location
            model.location = point.pos.pos

            # Set model rotation
            model.rotation_euler = (
                math.radians(point.angle.pitch),
                math.radians(point.angle.roll),
                math.radians(point.angle.yaw)
            )

            # Apply point scale
            model.matrix_basis @= mathutils.Matrix.Diagonal(mathutils.Vector((*point.scale.scale, 1.0)))

            # Apply transforms
            transform_mesh(model)

            # Add model to collection
            model_collection.objects.link(model)

            # Increment model count
            model_index += 1

    # Return RoomMesh data
    return room
