===== RoomMeshImportExport =====

The RoomMesh file format from SCP: Containment Breach is not supported by most applications. This Blender plugin allows the format to be imported and exported. It also adds
some features in the object properties tab to specify how objects are exported, such as:

Features:
- Set a mesh to be an invisible collision mesh
- Set a collision mesh to be a trigger
- Set empties to be a point (waypoints, screens, etc.)
- The image set to screen empties is used as the screen image in the file
- set speakers to be sound emitters with sound data

Features that are currently not supported, but are planned:
- Textures will not be exported automatically. Object textures are determined by an image node connected to the base color of the active material's BSDF.
- Lightmap data and textures are not supported currently. To be used, they have to be created manually and the file data will have to be edited.
- Normal maps will not be added to the materials.ini file automatically.
- Sounds that are not in the rooms.ini file by default will not be added automatically.
- Model files (.x) from rooms will not be exported as models, but as normal parts of the mesh.
