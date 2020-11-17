import bpy
from sys import argv

for object in bpy.data.objects:
    bpy.data.objects.remove(object)

glb_file = argv[len(argv) - 1]

bpy.ops.import_scene.gltf(filepath=glb_file)

bpy.ops.object.select_all(action='DESELECT')

selected_object = None
all_meshes = []
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.select_set(True)
        all_meshes.append(obj)

bpy.context.view_layer.objects.active = all_meshes[0]

bpy.ops.object.join()

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        if selected_object:
            print('WARNING! glb has more than one mesh!')
        else:
            selected_object = obj

if not selected_object:
    print(f'WARNING! Could not find object!')
else:
    x = selected_object.dimensions[0]
    y = selected_object.dimensions[1]
    z = selected_object.dimensions[2]

    print(f'x {x}')
    print(f'y {y}')
    print(f'z {z}')
