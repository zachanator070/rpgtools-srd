import csv
import re
import subprocess

from make_manifest import load_manifest, get_manifest_things, MANIFEST_FILE, MANIFEST_FIELD_NAMES
from pathlib import Path
import requests


def download_stl_files(manifest, manifest_things):
    workspace = Path('workspace')
    if not workspace.exists():
        workspace.mkdir()
    for index in range(0, len(manifest)):
        model = manifest[index]
        if not model['stl_file']:
            continue
        file_picked = None
        for file in manifest_things[index]['files']:
            if file['name'] == model['stl_file']:
                file_picked = file
                break
        if not file_picked:
            model_file = model['stl_file']
            print(f'WARNING: Could not find file {model_file}')
            continue
        filename = file_picked['name']
        file_path = Path(f'workspace/{filename}')
        if not file_path.exists():
            url = file_picked['public_url']
            print(f'Downloading {filename} {url}')
            download_request = requests.get(url)
            with open(str(file_path), 'wb') as destination_file:
                destination_file.write(download_request.content)


def render(manifest):
    for model in manifest:
        if not model['stl_file']:
            continue
        model_name = model['model'].replace('/', '_')
        stl_filename = model['stl_file']
        workspace = 'workspace'
        base_filename = workspace + '/' + re.match(r'.*?([\w-]+)\.', stl_filename).group(1)
        if not Path(base_filename + '.glb').exists() or not Path(base_filename + '.png').exists():
            print(f'\nrendering {model_name}')
            command_args = ['blender', '-b', '-P', 'export_glb.py', '--', stl_filename]
            blender_filename = base_filename + '.blend'
            if Path(blender_filename).exists():
                command_args.insert(1, blender_filename)
            blender_process = subprocess.run(command_args, capture_output=True)
            print(blender_process.stdout.decode())
            print(blender_process.stderr.decode())


def cleanup(manifest):
    workspace = Path('workspace')
    for file in [x for x in workspace.iterdir() if x.is_file()]:
        used = False
        for model in manifest:
            if Path(model['stl_file']).stem.replace('.', '') == file.stem.replace('.', ''):
                used = True
                break
        if not used:
            file.unlink()


def get_dimensions(manifest):
    manifest_needs_update = False
    for model in manifest:
        if model['depth'] and model['width'] and model['height']:
            continue
        model_name = model['model']
        print(f'getting dimensions for {model_name}')
        glb_file = model['stl_file'].replace('..', '.').replace('.stl', '.glb')
        command_args = ['blender', '-b', '-P', 'get_dimensions.py', '--', 'workspace/' + glb_file]
        blender_process = subprocess.run(command_args, capture_output=True)
        stdout = blender_process.stdout.decode()
        stderr = blender_process.stderr.decode()
        if stderr:
            print(glb_file)
            print(stderr)
        elif 'WARNING' in stdout:
            print(glb_file)
            print(stdout)
        else:
            x = float(re.search('x (\d+\.\d+)', stdout).group(1))
            y = float(re.search('z (\d+\.\d+)', stdout).group(1))
            z = float(re.search('y (\d+\.\d+)', stdout).group(1))

            smallest = min(x, z)
            x_ratio = x / smallest
            y_ratio = y / smallest
            z_ratio = z / smallest

            model_size = 5

            if 'adult' in model['model'].lower():
                model_size = 15
            elif 'ancient' in model['model'].lower():
                model_size = 20
            elif 'young' in model['model'].lower():
                model_size = 10

            x = x_ratio * model_size
            y = y_ratio * model_size
            z = z_ratio * model_size

            if x == 0 or y == 0 or z == 0:
                print(f'WARNING {glb_file} has 0 length dimension: {x} {y} {z}')

            model['depth'] = z
            model['width'] = x
            model['height'] = y

            manifest_needs_update = True

    return manifest_needs_update


def update_manifest(manifest):
    with open(MANIFEST_FILE, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=MANIFEST_FIELD_NAMES)

        writer.writeheader()
        writer.writerows(manifest)


def main():
    manifest = load_manifest()
    manifest_things = get_manifest_things(manifest)
    download_stl_files(manifest, manifest_things)
    render(manifest)
    manifest_needs_update = get_dimensions(manifest)
    if manifest_needs_update:
        update_manifest(manifest)
    cleanup(manifest)


if __name__ == '__main__':
    main()
