===== RoomMeshImportExport =====

The RoomMesh file format from SCP: Containment Breach is not supported by most applications. This Blender plugin allows the format to be imported and exported. It also adds
some features in the object properties tab to specify how objects are exported, such as:

Features:
- Set a mesh to be an invisible collision mesh
- Set a collision mesh to be a trigger
- Set empties to be a point (waypoints, screens, etc.)
- Set speakers to be sound emitters with sound data


Features that are currently not supported, but are planned:
- Textures will not be exported automatically. Object textures are determined by an image node connected to the base color of the active material's BSDF.
- Lightmap data and textures are not supported currently. To be used, they have to be created manually and the file data will have to be edited.
- Normal maps will not be added to the materials.ini file automatically.
- Sounds that are not in the rooms.ini file by default will not be added automatically.
- Any non-standard version of the RoomMesh file format are not supported, namely the version used in CB: Ultimate Edition Reborn


Important notes:
- If an image empty is set to be a screen, the image attached is the texture used for the screen in-game.
- Model files (.x) from vanilla rooms will not be exported as models, but as normal parts of the mesh. The model option in object properties does not change how it is exported.
- If a standard mesh object does not have a material, a warning will be raised. The object will have no texture attached to it in-game.
- Due to the way Blitz3D and Blender handle lighting differently, is no way to directly translate light data between Blender and the RoomMesh. The current conversion is an
estimate, and some inconsistencies will occur.
- The parser for this plugin was written based on the Converter.bb in the game files.

Credit:
- The code for importing, exporting, and converting RoomMesh data is written by me, other than the importing of model data.
- All credit for the model (.x) importing goes to Kusaanko, who developed the BVE Import/Export plugin for importing .x files. It has been slightly modified to fit the workflow of this plugin and is in the BVE folder and therefore does not need to be installed separately.
