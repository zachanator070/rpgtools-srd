from pathlib import Path

import requests
import re
import json
from os import path
import csv
import env

ALL_THINGS_FILENAME = 'all_mz4250_things.json'
THINGIVESE_TOKEN = env['THINGIVESE_TOKEN']

def api_get(url):
    response = requests.get(url, headers={"Authorization": f"token {THINGIVESE_TOKEN}"})
    return response.json()


def fetch_all_things():
    if path.exists(ALL_THINGS_FILENAME):
        with open(ALL_THINGS_FILENAME, 'r') as all_things:
            return json.loads(all_things.read())
    next_link = 'https://api.thingiverse.com/users/mz4250/things'
    things = []
    while next_link:
        print(f'fetching {next_link}')
        page_results = api_get(next_link)
        new_things = []
        for result in page_results:
            thing = api_get(result['url'])
            files = api_get(thing['files_url'])
            thing['files'] = files
            new_things.append(thing)

        things.extend(new_things)
        link_headers = response.headers['link'].split(',')
        link_header = None
        for header in link_headers:
            if 'rel="next"' in header:
                match = re.search('<(.*)>', header)
                link_header = header
                if match:
                    next_link = match.group(1)
                break
        if not link_header:
            next_link = None
    with open(ALL_THINGS_FILENAME, 'w') as all_things:
        all_things.write(json.dumps(things))
    return all_things


REQUESTED_MODELS_FILENAME = 'requested_models.txt'


def filter_stl_files(thing):
    return list(filter(lambda thing_file: '.stl' in thing_file['name'], thing['files']))


def match_model_to_thing(requested_models: list, all_things: list, animals: dict, current_things: list):
    matched_things = []
    animal_files = list(filter(lambda file: '.stl' in file['name'], animals['files']))
    animal_names = list(map(lambda thing: thing['name'].replace('.stl', '').replace('_', ' '), animal_files))

    for requested_model in requested_models:

        is_animal = False
        for animal_name in animal_names:
            if requested_model.lower() in animal_name.lower():
                is_animal = True
                break

        dragon_color = re.search('((Black)|(Blue)|(Brass)|(Bronze)|(Copper)|(Gold)|(Green)|(Red)|(Silver)|(White))',
                                 requested_model)
        if 'Dragon' in requested_model and dragon_color:
            requested_model = dragon_color.group(1) + ' Dragon'
        thing_to_use = None
        thing_to_use_score = 0
        if is_animal:
            thing_to_use = animals
        else:
            for thing in all_things:
                this_thing_score = get_name_score(thing['name'], requested_model)
                if this_thing_score > thing_to_use_score:
                    thing_to_use_score = this_thing_score
                    thing_to_use = thing
                for file in filter_stl_files(thing):
                    file_score = get_name_score(file['name'].replace('.stl', ''), requested_model)
                    if file_score > thing_to_use_score:
                        thing_to_use_score = file_score
                        thing_to_use = thing

        matched_things.append(thing_to_use)
    print(f'Matched {len(list(filter(lambda thing: thing is not None, matched_things)))}/{len(requested_models)}')

    things_to_return = []

    if len(matched_things) == len(current_things):
        for index in range(0, len(matched_things)):
            matched_thing = matched_things[index]
            current_thing = current_things[index]
            if matched_thing and not current_thing:
                things_to_return.append(matched_thing)
            elif current_thing and not matched_thing:
                things_to_return.append(current_thing)
            elif not matched_thing and not current_thing:
                things_to_return.append(None)
            else:
                new_thing = matched_thing.copy()
                new_thing.update(current_thing)
                things_to_return.append(new_thing)
    else:
        things_to_return = matched_things
    return things_to_return


def get_requested_models():
    with open(REQUESTED_MODELS_FILENAME, 'r') as requested_models_file:
        raw_lines = requested_models_file.readlines()
        models = []
        for line in raw_lines:
            models.append(line.strip())
        return models


def find_animals(all_things):
    animals = None
    for thing in all_things:
        if thing['name'] == 'Animals for Tabletop Gaming!':
            animals = thing
            break
    return animals


def get_name_score(search_name, target_name):
    target_name = target_name.replace('_', ' ').lower()
    search_name = search_name.replace('_', ' ').lower()

    score = 0
    name_contains_all_parts = True
    name_parts = target_name.split(' ')
    for part in name_parts:
        if part not in search_name:
            name_contains_all_parts = False
            break

    filename_contains_name = target_name in search_name

    filename_exact_match = target_name == search_name.replace(' updated', '')

    filename_has_updated = 'updated' in search_name

    if filename_contains_name:
        score += 1
    elif name_contains_all_parts:
        score += 1

    if filename_exact_match:
        score += 1

    if score > 0 and filename_has_updated:
        if 'dragon' in search_name:
            score -= 2
        else:
            score += 1

    return score


def pick_stl_files(requested_models, manifest_things):
    all_files = []
    for index in range(0, len(requested_models)):
        requested_model = requested_models[index]
        thing = manifest_things[index]
        file_to_use = None
        if thing:
            file_score = 0
            for file in filter_stl_files(thing):
                this_file_score = get_name_score(file['name'], requested_model)
                if this_file_score > file_score:
                    file_to_use = file
                    file_score = this_file_score
        all_files.append(file_to_use)
    return all_files


def get_manifest_things(manifest):

    with open(ALL_THINGS_FILENAME, 'r') as all_things_file:
        all_things = json.loads(all_things_file.read())
        things = []
        for model in manifest:
            thing_chosen = None
            if model['api']:
                for thing in all_things:
                    if thing['url'] == model['api']:
                        thing_chosen = thing
                        break
            things.append(thing_chosen)
        return things


def load_manifest():
    rows = []
    manifest_file_path = Path(MANIFEST_FILE)
    if manifest_file_path.exists():
        with open(MANIFEST_FILE, 'r') as manifest_file:
            reader = csv.DictReader(manifest_file, fieldnames=MANIFEST_FIELD_NAMES)
            header_read = False
            for row in reader:
                if not header_read:
                    header_read = True
                    continue
                rows.append(row)
    return rows


MANIFEST_FILE = 'manifest.csv'
MANIFEST_FIELD_NAMES = ['model', 'thing_name', 'api', 'url', 'stl_file', 'all_stl_files', 'depth', 'width', 'height']


def write_manifest(requested_models: list, things: list, files: list):
    with open(MANIFEST_FILE, 'w') as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=MANIFEST_FIELD_NAMES)

        writer.writeheader()
        for index in range(0, len(requested_models)):
            row = {'model': requested_models[index]}

            thing = things[index]
            if thing:
                row['thing_name'] = thing['name']
                row['api'] = thing['url']
                row['url'] = thing['public_url']
                row['all_stl_files'] = list(map(lambda file: file['name'], filter_stl_files(thing)))
            file = files[index]
            if file:
                row['stl_file'] = file['name']

            writer.writerow(row)


def main():
    requested_models = get_requested_models()
    all_things = fetch_all_things()
    animals = find_animals(all_things)
    manifest = load_manifest()
    current_things = get_manifest_things(manifest)
    things = match_model_to_thing(requested_models, all_things, animals, current_things)
    manifest_files = pick_stl_files(requested_models, things)
    write_manifest(requested_models, things, manifest_files)


if __name__ == '__main__':
    main()
