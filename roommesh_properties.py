# Import modules
import bpy

# Object Properties
def update_is_collision(self: bpy.types.PropertyGroup,
                        context: bpy.types.Context) -> None:
    """
    Updates the properties of an object when is_collision is toggled. Runs when the UI checkbox changes.

    Args:
        self (PropertyGroup): The property group handling is_collision.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Get object
    obj: bpy.types.Object | None = self.id_data

    # Ensure object was loaded
    if not obj:
        return

    # Update is_collision property
    self.id_data["is_collision"] = bool(self.is_collision)

    # Check if collision is enabled
    if self.is_collision:
        # Update object properties
        self.id_data.display_type = "WIRE"
        self.id_data.show_in_front = True
        self.id_data.hide_render = True

        # Check if model is on
        if self.is_model:
            # Turn off model
            self.is_model = False
    else:
        # Update object properties
        self.id_data.display_type = "SOLID"
        self.id_data.show_in_front = False
        self.id_data.hide_render = False

        # Check if trigger is on
        if self.is_trigger:
            # Turn off trigger
            self.is_trigger = False

def update_is_trigger(self: bpy.types.PropertyGroup,
                        context: bpy.types.Context) -> None:
    """
    Updates the properties of an object when is_trigger is toggled. Runs when the UI checkbox changes.

    Args:
        self (PropertyGroup): The property group handling is_trigger.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Get object
    obj: bpy.types.Object | None = self.id_data

    # Ensure object was loaded
    if not obj:
        return

    # Update is_trigger property
    self.id_data["is_trigger"] = bool(self.is_trigger)

    # Check if trigger is on:
    if self.is_trigger:
        # Check if collision is off
        if not self.is_collision:
            # Turn trigger off
            self.is_trigger = False

def update_is_model(self: bpy.types.PropertyGroup,
                        context: bpy.types.Context) -> None:
    """
    Updates the properties of an object when is_model is toggled. Runs when the UI checkbox changes.

    Args:
        self (PropertyGroup): The property group handling is_model.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Get object
    obj: bpy.types.Object | None = self.id_data

    # Ensure object was loaded
    if not obj:
        return

    # Update is_model property
    self.id_data["is_model"] = bool(self.is_model)

    # Check if model is enabled
    if self.is_model:
        # Check if collision is on
        if self.is_collision:
            # Turn collision/trigger off
            self.is_collision = False

def update_point(self: bpy.types.PropertyGroup,
                        context: bpy.types.Context) -> None:
    """
    Updates the properties of an empty when a point type is selected.

    Args:
        self (PropertyGroup): The property group handling role.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Get object
    obj: bpy.types.Object | None = self.id_data

    # Ensure object was loaded
    if not obj:
        return

    # Update point properties
    self.id_data["is_screen"] = bool(self.role == "SCREEN")
    self.id_data["is_waypoint"] = bool(self.role == "WAYPOINT")
    self.id_data["is_playerstart"] = bool(self.role == "PLAYERSTART")

    # Set empty display type
    if self.role == "SCREEN":
        self.id_data.empty_display_type = "IMAGE"
    elif self.role == "WAYPOINT":
        self.id_data.empty_display_type = "SINGLE_ARROW"
    elif self.role == "PLAYERSTART":
        self.id_data.empty_display_type = "SPHERE"
    elif self.role == "NONE":
        self.id_data.empty_display_type = "PLAIN_AXES"

def update_sound(self: bpy.types.PropertyGroup,
                        context: bpy.types.Context) -> None:
    """
    Updates the properties of a speaker when a sound ID is selected.

    Args:
        self (PropertyGroup): The property group handling sound_ID.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Get object
    obj: bpy.types.Object | None = self.id_data

    # Ensure object was loaded
    if not obj:
        return

    # Update sound properties
    self.id_data["sound_ID"] = self.sound_ID

# RoomMesh properties class
class RoomMeshObjectProperties(bpy.types.PropertyGroup):
    """
    Adds and handles new object properties.
    """

    # Set collision property
    is_collision: bpy.props.BoolProperty(
        name="Collision",
        description="Marks this object as a hidden collision mesh.",
        default=False,
        update=update_is_collision
    )

    # Set trigger property
    is_trigger: bpy.props.BoolProperty(
        name="Trigger",
        description="Marks this object as a trigger box.",
        default=False,
        update=update_is_trigger
    )

    # Set trigger name property
    trigger_name: bpy.props.StringProperty(
        name="Trigger Name",
        description="The unique name of this trigger.",
        default=''
    )

    # Set model property
    is_model: bpy.props.BoolProperty(
        name="Model",
        description="Marks this object as a model.",
        default=False,
        update=update_is_model
    )

    # Set model name property
    model_name: bpy.props.StringProperty(
        name="Model Name",
        description="The name of the X model.",
        default='',
    )

    # Set point type property
    role: bpy.props.EnumProperty(
        name="Point Type",
        items=[
            ('NONE', "None", "No type"),
            ('SCREEN', "Screen", "Save screen image"),
            ('WAYPOINT', "Waypoint", "NPC path point"),
            ('PLAYERSTART', "Player Start", "Player spawn position")
        ],
        default='NONE',
        update=update_point
    )

    # Set sound ID property
    sound_ID: bpy.props.IntProperty(
        name="Sound ID",
        description="ID of the sound sample to use from rooms.ini",
        default=0,
        min=0,
        step=1,
        update=update_sound
    )

class ROOMMESH_PT_object(bpy.types.Panel):
    """
    Creates UI for custom properties in the properties tab.
    """

    # Set panel information
    bl_label = "RoomMesh"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """
        Determines if an object is selected.

        Args:
            context (Context): The current state of Blender.

        Returns:
            None.
        """

        # Check if object is selected
        return context.object is not None

    def draw(self, context: bpy.types.Context) -> None:
        """
        Draws the panel in the object properties tab.

        Args:
            context (Context): The current state of Blender.

        Returns:
            none.
        """

        # Get panel layout
        layout = self.layout

        # Set panel properties
        layout.use_property_split = False
        layout.use_property_decorate = False

        # Get custom properties
        props = context.object.roommesh

        # Mesh properties
        if context.object.type == 'MESH':
            # Add collision property
            collision_row = layout.row()
            collision_row.enabled = not props.is_model
            collision_row.prop(props, "is_collision", text="Collision")

            # Add trigger property
            trigger_row = layout.row()
            trigger_row.enabled = props.is_collision
            trigger_row.prop(props, "is_trigger", text="Trigger")

            # Add trigger name property
            trigger_name_row = layout.row()
            trigger_name_row.enabled = props.is_trigger
            trigger_name_row.prop(props, "trigger_name", text="Trigger Name")

            # Add model property
            model_row = layout.row()
            model_row.enabled = not props.is_collision
            model_row.prop(props, "is_model", text="Model")

            # Add model name property
            model_name_row = layout.row()
            model_name_row.enabled = props.is_model
            model_name_row.prop(props, "model_name", text="Model Name")

        # Empty properties
        if context.object.type == 'EMPTY':
            # Add point property
            point_row = layout.row()
            point_row.prop_enum(props, 'role', "NONE")
            point_row.prop_enum(props, 'role', "SCREEN")
            point_row.prop_enum(props, 'role', "WAYPOINT")
            point_row.prop_enum(props, 'role', "PLAYERSTART")

        # Speaker properties
        if context.object.type == 'SPEAKER':
            # Add sound ID property
            sound_row = layout.row()
            sound_row.prop(props, 'sound_ID', text="Sound ID")

# Registration functions
def register_pointers() -> None:
    """
    Attaches custom property groups to Blender data blocks.

    Returns:
        None.
    """

    # Check if property doesn't exist
    if not hasattr(bpy.types.Object, 'roommesh'):
        # Add property
        bpy.types.Object.roommesh = bpy.props.PointerProperty(type=RoomMeshObjectProperties)

def unregister_pointers() -> None:
    """
    Removes custom property groups from Blender data blocks.

    Returns:
        None.
    """

    # Check if property exists
    if hasattr(bpy.types.Object, 'roommesh'):
        # Remove property
        delattr(bpy.types.Object, 'roommesh')

# Define classes for registration
classes: tuple = (
    RoomMeshObjectProperties,
    ROOMMESH_PT_object
)

def register() -> None:
    """
    Registers all properties and property classes.

    Returns:
        None.
    """

    # Loop through classes
    for cls in classes:
        # Register class
        bpy.utils.register_class(cls)

    # Register properties
    register_pointers()

def unregister() -> None:
    """
    Unregisters all properties and property classes.

    Returns:
        None.
    """

    # Unregister properties
    unregister_pointers()

    # Loop through classes reversed
    for cls in reversed(classes):
        # Unregister class
        bpy.utils.unregister_class(cls)