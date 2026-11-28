import bpy, sys, math
eng = sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
gpd = bpy.data.grease_pencils.new("gp")
ob = bpy.data.objects.new("gp", gpd); sc.collection.objects.link(ob)
mat = bpy.data.materials.new("ink"); bpy.data.materials.create_gpencil_data(mat)
mat.grease_pencil.color = (0.4,0.15,0.1,1); gpd.materials.append(mat)
l = gpd.layers.new("ink"); f = l.frames.new(1)
s = f.strokes.new(); s.line_width = 80; s.display_mode='3DSPACE'
n=40; s.points.add(n)
for i,p in enumerate(s.points):
    t=i/(n-1); p.co=(t*4-2, 0, math.sin(t*6)*0.8); p.pressure=math.sin(t*math.pi)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("c")); sc.collection.objects.link(cam)
cam.location=(0,-8,0); cam.rotation_euler=(math.pi/2,0,0); sc.camera=cam
sc.render.engine=eng; sc.render.resolution_x=300; sc.render.resolution_y=200
sc.render.filepath="//gp_"+eng+".png"; bpy.ops.render.render(write_still=True)
print("DONE", eng)
