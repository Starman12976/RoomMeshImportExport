# Define file info
bl_info = {
    "name": "RoomMesh Importer (.rmesh)",
    "author": "Joel Nelems",
    "version": (1, 0, 0),
    "blender": (4, 5, 1),
    "location": "File > Import",
    "description": "Import RoomMesh files (.rmesh)",
    "category": "Import-Export"
}

# Import modules
import bpy
from bpy.types import Context, OperatorFileListElement, Menu, UILayout
from bpy_extras.io_utils import ExportHelper, ImportHelper
from pathlib import Path
from .roommesh_import import import_roommesh
from .roommesh_export import export_roommesh
from . import roommesh_properties

# Define classes
class IMPORT_OT_RoomMesh(bpy.types.Operator,
                         ImportHelper):
    """
    Allows importing of the RoomMesh (.rmesh) file format.
    """
    
    # Define class information
    bl_idname = "import_scene.roommesh"
    bl_label = "Import RoomMesh"
    bl_options = {"PRESET", "UNDO"}
    
    # Set file browser behavior
    filename_ext = ".rmesh"
    filter_glob: bpy.props.StringProperty(default="*.rmesh", options={"HIDDEN"})
    files: bpy.props.CollectionProperty(type=OperatorFileListElement)
    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    
    # Define methods
    def execute(self, context: Context) -> set[str]:
        """
        Imports all files selected during the import process.
        
        Args:
            context (Context): The current state of Blender.
        
        Returns:
            set[str]: Debug message.
        """
        
        # Attempt to import selected files
        try:
            # Check if multiple files selected
            if self.files:
                # Loop through RoomMesh files
                for rmesh in self.files:
                    # Get file path
                    filepath: Path = Path(self.directory) / rmesh.name
                    
                    # Import file
                    import_roommesh(filepath)
            else:
                # Get file path
                filepath: Path = Path(self.filepath)
                
                # Import file
                import_roommesh(filepath)
            
            # Debug info
            self.report({"INFO"}, "RoomMesh import finished.")
            
            # Return successfully
            return {"FINISHED"}
        except Exception as e:
            # Print error
            self.report({"ERROR"}, f"RoomMesh import failed: {e}")
            
            # Return unsuccessfully
            return {"CANCELLED"}
        
    def draw(self, context: Context) -> None:
        """
        Draws the property info of the imported file.
        
        Args:
            context (Context): The current state of Blender.
        
        Returns:
            None.
        """
        
        # Get layout
        layout: UILayout = self.layout


class EXPORT_OT_RoomMesh(bpy.types.Operator,
                         ExportHelper):
    """
    Allows exporting of the RoomMesh (.rmesh) file format.
    """

    # Define class information
    bl_idname = "export_scene.roommesh"
    bl_label = "Export RoomMesh"
    bl_options = {"PRESET"}

    # Set file browser behavior
    filename_ext = ".rmesh"
    filter_glob: bpy.props.StringProperty(
        default="*.rmesh",
        options={'HIDDEN'}
    )

    # Define methods
    def execute(self, context: Context) -> set[str]:
        """
        Exports the RoomMesh file.

        Args:
            context (Context): The current state of Blender.

        Returns:
            set[str]: Debug message.
        """

        # Attempt to export selected files
        try:
            # Get file path
            filepath: Path = Path(self.filepath).with_suffix(self.filename_ext)

            # Export file
            export_roommesh(context, filepath)

            # Debug info
            self.report({"INFO"}, "RoomMesh export finished.")

            # Return successfully
            return {"FINISHED"}
        except Exception as e:
            # Print error
            self.report({"ERROR"}, f"RoomMesh export failed: {e}")

            # Return unsuccessfully
            return {"CANCELLED"}

    def draw(self, context: Context) -> None:
        """
        Draws the property info of the exported file.

        Args:
            context (Context): The current state of Blender.

        Returns:
            None.
        """

        # Get layout
        layout: UILayout = self.layout

def menu_function_import(self: Menu, context: Context) -> None:
    """
    Adds the RoomMesh import option in Blender's import menu.
    
    Args:
        self (Menu): The menu adding the import.
        context (Context): The current state of Blender.
    
    Returns:
        None.
    """
    
    # Add RoomMesh import option
    self.layout.operator(IMPORT_OT_RoomMesh.bl_idname, text="RoomMesh (.rmesh)")


def menu_function_export(self: Menu, context: Context) -> None:
    """
    Adds the RoomMesh export option in Blender's export menu.

    Args:
        self (Menu): The menu adding the export.
        context (Context): The current state of Blender.

    Returns:
        None.
    """

    # Add RoomMesh export option
    self.layout.operator(EXPORT_OT_RoomMesh.bl_idname, text="RoomMesh (.rmesh)")

# Create class registration
classes: tuple = (
    IMPORT_OT_RoomMesh,
    EXPORT_OT_RoomMesh,
)

# Define registration methods
def register() -> None:
    """
    Registers RoomMesh import classes.
    
    Returns:
        None.
    """
    
    # Loop through classes
    for cls in classes:
        # Register class
        bpy.utils.register_class(cls)
    
    # Add import option
    bpy.types.TOPBAR_MT_file_import.append(menu_function_import)

    # Add export option
    bpy.types.TOPBAR_MT_file_export.append(menu_function_export)

    # Add custom properties
    roommesh_properties.register()

# Define registration methods
def unregister() -> None:
    """
    Unregisters RoomMesh import classes.
    
    Returns:
        None.
    """

    # Remove custom properties
    roommesh_properties.unregister()

    # Remove export option
    bpy.types.TOPBAR_MT_file_export.remove(menu_function_export)
    
    # Remove import option
    bpy.types.TOPBAR_MT_file_import.remove(menu_function_import)
    
    # Loop through classes reversed
    for cls in reversed(classes):
        # Unregister class
        bpy.utils.unregister_class(cls)

# Ensure direct execution
if __name__ == "__main__":
    # Register RoomMesh import
    register()