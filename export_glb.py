from sys import argv

import bpy
import re
import os
from pathlib import Path

print('Starting export script')

stl_file = argv[len(argv) - 1]
destination_dir = './workspace'

bpy.ops.object.select_all(action='DESELECT')

default_cube = bpy.data.objects.get('Cube')
if default_cube:
    default_cube.select_set(True)
    bpy.ops.object.delete()

if bpy.data.filepath == '':
    bpy.ops.import_mesh.stl(filepath=f'{destination_dir}/{stl_file}')

mat = bpy.data.materials.get("Material")
if mat is None:
    mat = bpy.data.materials.new(name="Material")

for key, collection in bpy.data.collections.items():
    for obj in collection.objects:
        if obj.type == 'MESH':
            if len(obj.material_slots) == 0:
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)

project_name = re.match(r'.*?([\w-]+)\.', stl_file).group(1)
base_filename = destination_dir + '/' + project_name
glb_filename = base_filename + '.glb'


def export() -> int:
    print(f'Exporting to {glb_filename}...')
    bpy.ops.export_scene.gltf(export_format='GLB', filepath=glb_filename, export_apply=True, check_existing=False)
    return os.path.getsize(glb_filename)


def add_decimate(obj, ratio):
    decimate_mod = obj.modifiers.get('Decimate')
    if not decimate_mod:
        obj.modifiers.new('Decimate', 'DECIMATE')
        decimate_mod = obj.modifiers.get('Decimate')
    decimate_mod.ratio = ratio


size = export()
attempt = 1
ratio_step = .1
ratio = 1
while size > 5242880:
    print(f'Model too big! {size} bytes')
    if ratio < ratio_step + ratio_step / 2:
        ratio_step /= 2
    ratio -= ratio_step
    print(f'Trying ratio {ratio}')
    for key, collection in bpy.data.collections.items():
        for obj in collection.objects:
            if obj.type == 'MESH':
                add_decimate(obj, ratio)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            add_decimate(obj, ratio)
    print(f'Attempting again, try #{attempt}')
    size = export()
    attempt += 1

print(f'finished export, size is {size} bytes')

camera = None
for key, collection in bpy.data.collections.items():
    for obj in collection.objects:
        if obj.type == 'CAMERA':
            camera = obj
            break
for key, obj in bpy.context.scene.objects.items():
    if obj.type == 'CAMERA':
        camera = obj
        break
if not camera:
    cam1 = bpy.data.cameras.new("Camera 1")
    cam1.lens = 18
    camera = bpy.data.objects.new("Camera 1", cam1)
    bpy.context.scene.collection.objects.link(camera)

bpy.context.scene.camera = camera

camx = 8.63 * 12
camy = -5.63 * 12
camz = 4.22 * 12
camera.location = (camx, camy, camz)
camera.rotation_euler = (1.291513976, 0, 0.9271799852)
camera.data.clip_end = 240

light_name = 'camera light'
light = bpy.context.scene.objects.get(light_name)
if not light:
    light_data = bpy.data.lights.new(light_name, 'POINT')
    light = bpy.data.objects.new(light_name, light_data)
    bpy.context.scene.collection.objects.link(light)

light.location = (camx, camy, camz)
print(light)
light.data.energy = 124000

bpy.context.scene.render.filepath = base_filename
output_image = Path(base_filename + '.png')
bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=base_filename + '.blend')

bpy.ops.wm.quit_blender()
