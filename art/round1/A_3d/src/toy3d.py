"""A 방향: 3D 장난감(소프트 비닐/클레이) 렌더. Blender 3.0 헤드리스, Cycles CPU.
사용: blender -b -P toy3d.py -- <hamster|penguin|rocket> <출력 png> [해상도=480] [샘플=48] [살각도=-30]
좌표: 벡터 시안(108 격자)과 같은 구도를 쓰려고 2D 좌표(u,v)를 x=(u-54)/10, z=(54-v)/10 으로 옮긴다.
카메라는 정사영(ortho_scale 10.8) 정면. 배경은 투명.
"""
import bpy, sys, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
NAME, OUT = argv[0], argv[1]
RES = int(argv[2]) if len(argv) > 2 else 480
SAMPLES = int(argv[3]) if len(argv) > 3 else 48
SPOKE0 = float(argv[4]) if len(argv) > 4 else -30.0

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def X(u): return (u - 54) / 10.0
def Z(v): return (54 - v) / 10.0


def hexcol(h, a=1.0):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    # sRGB → 선형
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return (*c, a)


MATS = {}


def mat(name, col, rough=0.5, sss=0.0, spec=0.35, emit=0.0, coat=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = hexcol(col)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular"].default_value = spec
    b.inputs["Clearcoat"].default_value = coat
    if sss and False:
        b.inputs["Subsurface"].default_value = sss
        b.inputs["Subsurface Color"].default_value = hexcol(col)
        b.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.1)
    if emit:
        b.inputs["Emission"].default_value = hexcol(col)
        b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m
    return m


def smooth(obj, sub=2):
    for p in obj.data.polygons:
        p.use_smooth = True
    if sub:
        md = obj.modifiers.new("sub", "SUBSURF")
        md.levels = sub
        md.render_levels = sub


def sphere(loc, scale, m, rot=(0, 0, 0), sub=1):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    o.data.materials.append(m)
    smooth(o, sub)
    return o


def surface_y(cx, cz, rx, ry, rz, x, z, cy=0.0):
    """정면에서 본 타원체 표면의 y(카메라 쪽, 음수)"""
    t = 1 - ((x - cx) / rx) ** 2 - ((z - cz) / rz) ** 2
    return cy - ry * math.sqrt(max(t, 0.0))


def eye(x, z, y, r, m_eye, m_hi):
    # 눈: 광택 검은 반구 + 칠한 듯한 하이라이트 2개(작은 크기에서 반사만으로는 점이 사라져서 직접 박음)
    sphere((x, y + r * 0.35, z), (r * 0.92, r * 0.6, r), m_eye)
    sphere((x - r * 0.36, y - r * 0.22, z + r * 0.4), (r * 0.36, r * 0.2, r * 0.36), m_hi, sub=0)
    sphere((x + r * 0.34, y - r * 0.18, z - r * 0.38), (r * 0.15, r * 0.1, r * 0.15), m_hi, sub=0)


def metaball(elems, m, res=0.06):
    mb = bpy.data.metaballs.new("blob")
    mb.resolution = res
    mb.render_resolution = res * 0.6
    mb.threshold = 0.6
    ob = bpy.data.objects.new("blob", mb)
    scn.collection.objects.link(ob)
    for (loc, r, sc) in elems:
        e = mb.elements.new()
        e.co = loc
        e.radius = r
        e.type = "ELLIPSOID"
        e.size_x, e.size_y, e.size_z = sc
        e.stiffness = 2.2
    mb.materials.append(m)
    return ob


# ---------- 재질 (팔레트는 벡터 시안과 같음) ----------
EYE = mat("eye", "#2B1E16", rough=0.12, spec=0.6, coat=0.6)
HI = mat("hi", "#FFFFFF", rough=0.5, emit=2.5)
BLUSH = mat("blush", "#FF8FA3", rough=0.7, sss=0.1)
PINK = mat("pink", "#FF9EAA", rough=0.55, sss=0.15)


def build_hamster():
    fur = mat("fur", "#FFC27A", rough=0.62, sss=0.2)
    cream = mat("cream", "#FFF1DC", rough=0.6, sss=0.2)
    ear = mat("ear", "#FFB066", rough=0.6, sss=0.2)
    ring = mat("ring", "#7BE0C3", rough=0.35, spec=0.5, coat=0.3)
    spoke = mat("spoke", "#BFEFE0", rough=0.4)
    hub = mat("hub", "#FFF1DC", rough=0.4)
    # 쳇바퀴(뒤)
    bpy.ops.mesh.primitive_torus_add(major_radius=3.75, minor_radius=0.27, major_segments=96, minor_segments=24,
                                     location=(X(54), 2.2, Z(54)), rotation=(math.pi / 2, 0, 0))
    t = bpy.context.object; t.data.materials.append(ring); smooth(t, 1)
    for k in range(3):
        a = math.radians(SPOKE0 + 120 * k)
        # 2D 의 v 는 아래로 증가 → z 는 부호 반대
        dx, dz = math.cos(a), -math.sin(a)
        L = 3.45
        bpy.ops.mesh.primitive_cylinder_add(radius=0.13, depth=L, vertices=24,
                                            location=(X(54) + dx * L / 2, 2.2, Z(54) + dz * L / 2))
        c = bpy.context.object
        c.rotation_euler = (0, -math.atan2(dz, dx) + math.pi / 2, 0)
        c.data.materials.append(spoke); smooth(c, 0)
        sphere((X(54) + dx * 3.45, 2.0, Z(54) + dz * 3.45), (0.2, 0.2, 0.2), hub, sub=0)
    sphere((X(54), 2.0, Z(54)), (0.42, 0.3, 0.42), hub)
    # 몸: 머리 구 + 몸통 타원체(소프트 비닐 장난감처럼 부품을 맞붙인 구조)
    head_c = (X(63), -0.6, Z(64)); hr = 2.0
    sphere((X(45), 0.4, Z(72.5)), (2.3, 1.9, 1.7), fur)
    sphere(head_c, (hr, hr * 0.95, hr), fur)

    def on_head(u, v, lift=0.0):
        x, z = X(u), Z(v)
        return surface_y(head_c[0], head_c[2], hr + lift, hr * 0.95 + lift, hr + lift, x, z, head_c[1])

    # 귀: 머리 뒤쪽 윗부분에 꽂힌 납작한 원판
    for (u, v) in ((49, 47.5), (74, 45.5)):
        sphere((X(u), -0.2, Z(v)), (0.72, 0.3, 0.72), ear)
        sphere((X(u) + (0.05 if u < 60 else -0.05), -0.45, Z(v + 1)), (0.38, 0.12, 0.38), PINK)
    # 얼굴 크림 무늬: 눈 아래 볼·주둥이에 얇게 붙인 조각
    sphere((X(63.5), on_head(63.5, 76) + 0.18, Z(76)), (1.35, 0.32, 0.72), cream)
    for u in (55.5, 71.5):
        eye(X(u), Z(67), on_head(u, 67) - 0.12, 0.45, EYE, HI)
    for u in (49.5, 77.5):
        sphere((X(u), on_head(u, 74) + 0.06, Z(74)), (0.4, 0.1, 0.25), BLUSH, sub=0)
    sphere((X(63.5), on_head(63.5, 71.8) - 0.05, Z(71.8)), (0.2, 0.12, 0.15), mat("nose", "#FF7A90", rough=0.3))
    # 앞발·뒷발
    for u in (58, 69):
        sphere((X(u), on_head(u, 81) - 0.05, Z(82.5)), (0.36, 0.26, 0.27), cream)
    for u in (41, 60):
        sphere((X(u), -0.9, Z(88.4)), (0.5, 0.45, 0.3), PINK)


def build_penguin():
    back = mat("pback", "#6E7FA8", rough=0.5, sss=0.05, coat=0.2)
    belly = mat("pbelly", "#FFFFFF", rough=0.55, sss=0.1)
    beak = mat("beak", "#FFA94D", rough=0.4, sss=0.1)
    scarf = mat("scarf", "#7BE0C3", rough=0.75, sss=0.05)
    cx, cz = X(54), Z(57)
    rx, ry, rz = 2.7, 2.3, 3.3
    sphere((cx, 0, cz), (rx, ry, rz), back)
    # 배·얼굴: 앞으로 살짝 튀어나온 흰 타원체(정면에서 보면 둥근 얼굴판)
    sphere((cx, -0.75, Z(60)), (2.05, 1.8, 2.55), belly)
    # 머리 위 깃털
    o = sphere((X(55), 0, Z(21)), (0.3, 0.3, 0.55), back, rot=(0, math.radians(-30), 0))
    # 날개
    sphere((X(29), 0.2, Z(69)), (0.42, 0.8, 1.15), back, rot=(0, math.radians(-28), 0))
    sphere((X(79), 0.2, Z(69)), (0.42, 0.8, 1.15), back, rot=(0, math.radians(28), 0))
    # 발
    for u in (44, 65):
        sphere((X(u), -1.0, Z(89.5)), (0.78, 0.7, 0.32), beak)
    # 목도리: 납작한 고리
    # 정면 정사영에서 고리가 막대로 보이지 않게 앞쪽을 아래로 기울임
    bpy.ops.mesh.primitive_torus_add(major_radius=2.62, minor_radius=0.42, major_segments=64, minor_segments=16,
                                     location=(cx, 0, Z(65.5)), rotation=(math.radians(14), 0, 0))
    tt = bpy.context.object; tt.scale = (1.0, 0.86, 1.0); tt.data.materials.append(scarf); smooth(tt, 1)
    sphere((X(65), -2.25, Z(75)), (0.48, 0.22, 0.85), scarf, rot=(0, math.radians(-10), 0))
    # 얼굴
    bel = (cx, -0.75, Z(60), 2.05, 1.8, 2.55)
    for u in (46, 62):
        y = surface_y(bel[0], bel[2], bel[3], bel[4], bel[5], X(u), Z(52.5), bel[1])
        eye(X(u), Z(52.5), y, 0.42, EYE, HI)
    for u in (40, 68):
        y = surface_y(bel[0], bel[2], bel[3], bel[4], bel[5], X(u), Z(59), bel[1])
        sphere((X(u), y + 0.05, Z(59)), (0.36, 0.12, 0.22), BLUSH, sub=0)
    yb = surface_y(bel[0], bel[2], bel[3], bel[4], bel[5], X(54), Z(57.5), bel[1])
    sphere((X(54), yb - 0.1, Z(57.6)), (0.42, 0.4, 0.3), beak)


def build_rocket():
    body = mat("rbody", "#F7F3FF", rough=0.3, spec=0.5, coat=0.4)
    nose = mat("rnose", "#FF8FB1", rough=0.3, spec=0.5, coat=0.4)
    fin = mat("rfin", "#7BE0C3", rough=0.35, coat=0.3)
    flame = mat("flame", "#FF9F0A", rough=0.5, emit=0.9)
    flame_in = mat("flame_in", "#FFD66B", rough=0.5, emit=1.2)

    def lathe(profile, m, name):
        me = bpy.data.meshes.new(name)
        verts = [(x, 0, r) for (x, r) in profile]
        edges = [(i, i + 1) for i in range(len(verts) - 1)]
        me.from_pydata(verts, edges, [])
        ob = bpy.data.objects.new(name, me)
        scn.collection.objects.link(ob)
        sc = ob.modifiers.new("screw", "SCREW")
        sc.axis = "X"; sc.steps = 64; sc.render_steps = 64; sc.use_merge_vertices = True
        sc.use_normal_calculate = True
        ob.data.materials.append(m)
        ob.location = (0, 0, Z(54))
        sub = ob.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 2
        ob.data.polygons.foreach_set("use_smooth", [True] * len(ob.data.polygons))
        return ob

    lathe([(X(28), 0.0), (X(28), 1.0), (X(28.6), 1.45), (X(31), 1.6), (X(66), 1.6), (X(76), 1.45),
           (X(77), 1.3)], body, "body")
    o = lathe([(X(76.6), 0.0), (X(76.6), 1.47), (X(84), 1.2), (X(90), 0.85), (X(94.5), 0.45), (X(96.5), 0.15), (X(97), 0.0)], nose, "nose")
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    # 날개: 위·아래 + 카메라 쪽 하나
    for sgn in (1, -1):
        sphere((X(34), 0.3, Z(54) + sgn * 1.75), (1.05, 0.18, 0.85), fin, rot=(0, math.radians(sgn * 35), 0))
    # 불꽃: 납작한 눈물 모양(발광)
    sphere((X(18), 0.0, Z(54)), (1.45, 0.55, 0.78), flame)
    sphere((X(21), -0.3, Z(54)), (0.85, 0.36, 0.45), flame_in)
    # 얼굴
    for u in (50, 64):
        y = -math.sqrt(max(1.6 ** 2 - (Z(54) - Z(54)) ** 2, 0)) - 0.0
        eye(X(u), Z(54), -1.58, 0.41, EYE, HI)
    for u in (44.5, 69.5):
        sphere((X(u), -1.48, Z(60.5)), (0.34, 0.12, 0.21), BLUSH, sub=0)
    # 입: 짧은 원호(토러스 일부 대신 납작 타원 두 개로 미소)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    cu = bpy.context.object
    sp = cu.data.splines[0]
    p0, p1 = sp.bezier_points
    p0.co = (X(54.5), -1.6, Z(60)); p0.handle_left = p0.co; p0.handle_right = (X(55.5), -1.6, Z(62.6))
    p1.co = (X(59.5), -1.6, Z(60)); p1.handle_right = p1.co; p1.handle_left = (X(58.5), -1.6, Z(62.6))
    cu.data.bevel_depth = 0.07
    cu.data.materials.append(EYE)


{"hamster": build_hamster, "penguin": build_penguin, "rocket": build_rocket}[NAME]()

# ---------- 카메라·조명 ----------
cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"; cam_d.ortho_scale = 10.8
cam = bpy.data.objects.new("cam", cam_d); scn.collection.objects.link(cam)
cam.location = (0, -30, 0); cam.rotation_euler = (math.pi / 2, 0, 0)
scn.camera = cam


def area(name, loc, energy, size, col=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.energy = energy; l.size = size; l.color = col
    o = bpy.data.objects.new(name, l); scn.collection.objects.link(o)
    o.location = loc
    d = Vector((0, 0, 0)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


area("key", (-6, -9, 8), 1600, 6, (1.0, 0.97, 0.92))      # 왼쪽 위 앞: 주광(따뜻하게)
area("fill", (8, -10, -1), 420, 8, (0.9, 0.95, 1.0))     # 오른쪽: 약한 보조광
area("rim", (5, 9, 6), 1100, 4, (1.0, 1.0, 1.0))         # 뒤 오른쪽 위: 검정 바탕에서 윤곽을 살리는 테두리광
area("rim2", (-7, 8, -2), 500, 4, (1.0, 0.95, 0.9))

world = bpy.data.worlds.new("w"); scn.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.35, 0.38, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6

scn.render.engine = "CYCLES"
scn.cycles.device = "CPU"
scn.cycles.samples = SAMPLES
# 이 서버의 Blender 3.0.1(데비안 패키지)은 OpenImageDenoise 를 켜면 결과가 통째로 0(투명)이 된다 → 끄고 샘플을 늘림
scn.cycles.use_denoising = False
scn.cycles.sample_clamp_indirect = 2.0
scn.cycles.max_bounces = 6
scn.render.film_transparent = True
scn.render.resolution_x = RES; scn.render.resolution_y = RES
scn.render.image_settings.file_format = "PNG"
scn.render.image_settings.color_mode = "RGBA"
scn.view_settings.view_transform = "Standard"
scn.view_settings.look = "None"
scn.view_settings.exposure = 0.35
scn.render.filepath = OUT
bpy.ops.render.render(write_still=True)
