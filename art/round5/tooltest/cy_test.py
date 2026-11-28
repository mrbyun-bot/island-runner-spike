import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
bpy.ops.mesh.primitive_uv_sphere_add(); bpy.ops.object.camera_add(location=(0,-6,0),rotation=(1.5708,0,0)); sc.camera=bpy.context.object
sc.render.engine='CYCLES'; sc.cycles.samples=4; sc.render.resolution_x=64; sc.render.resolution_y=64
sc.render.filepath="//cy_test.png"; bpy.ops.render.render(write_still=True); print("DONE")
