import json
import re
import subprocess

import requests

from make_manifest import load_manifest

API_URL = 'http://localhost:3000/api'


cookies = None
worldId = "5f9f85c2f555c5005d1a58a8"


def api_query(query, variables=None, file=None):
    global cookies
    payload = {"query": query}
    if variables:
        payload['variables'] = variables
    if file:
        files_data = [
            ("operations", (None, json.dumps({"query": query, "variables": variables}), None)),
            ('map', (None, json.dumps({"nfile": ['variables.' + file[0]]}), None)),
            ('nfile', file[1])
        ]
        response = requests.post(API_URL, files=files_data, cookies=cookies)
    else:
        response = requests.post(API_URL, json=payload, cookies=cookies)
    if response.cookies:
        cookies = response.cookies
    response_json = response.json()
    if 'errors' in response_json:
        errors = response_json['errors']
        raise ValueError(f'Api Error: {errors}')
    data = response_json['data']

    return data


def paginated_api_query(query, variables=None):
    data = api_query(query, variables)
    query_name = None
    for key in data.keys():
        query_name = key
    query_result = data[query_name]
    docs = query_result['docs']
    for doc in docs:
        yield doc
    while 'nextPage' in query_result and query_result['nextPage']:
        variables.update({"page": query_result['nextPage']})
        data = api_query(query, variables)
        query_result = data[query_name]
        docs = query_result['docs']
        for doc in docs:
            yield doc


def login():
    query = """
        mutation login{
            login(username: "zach", password: "zach"){
                _id
            }
        }
    """
    api_query(query)


def get_all_wikis():
    print('Getting all wikis')
    query = """
        query wikis($worldId: ID!, $page: Int){
            wikis(worldId: $worldId, page: $page){
                page
                totalPages
                nextPage
                docs{
                    _id
                    name
                }
            }
        }
    """
    return paginated_api_query(query, variables={"worldId": worldId, "page": 1})


def get_wiki_ids(manifest, all_wikis):
    ids = []
    for model in manifest:
        for wiki in all_wikis:
            if model['model'] == wiki['name']:
                ids.append(wiki['_id'])
                break
    return ids


def upload_models(manifest):
    ids = []
    for index in range(0, len(manifest)):
        model = manifest[index]
        model_name = model['model']
        print(f'uploading {model_name}')
        filename = 'workspace/' + model['stl_file'].replace('..', '.').replace('.stl', '.glb')
        with open(filename, 'rb') as glb_file:
            query = """
                mutation createModel($name: String!, $file: Upload!, $worldId: ID!, $depth: Float!, $width: Float!, $height: Float!, $notes: String!){
                    createModel(name: $name, file: $file, worldId: $worldId, depth: $depth, width: $width, height: $height, notes: $notes){
                        _id
                    }
                }
            """
            source = model['url']
            variables = {
                "name": model['model'],
                "file": None,
                "worldId": worldId,
                "depth": float(model['depth']),
                "width": float(model['width']),
                "height": float(model['height']),
                "notes": f"Author: mz4250\nSource: {source}\nLicense: Creative Commons - Attribution\nLicense Link: https://creativecommons.org/licenses/by/4.0/"
            }
            data = api_query(query, variables=variables, file=("file", glb_file))
            ids.append(data['createModel']['_id'])
    return ids


def update_wikis(ids, model_ids):
    for index in range(0, len(ids)):
        _id = ids[index]
        print(f'updating wiki {_id}')
        model_id = model_ids[index]
        query = """
            mutation($wikiId: ID!){
                updateWiki(wikiId: $wikiId, type: "Monster"){
                    _id
                }
            } 
        """
        api_query(query, variables={'wikiId': _id})
        query = """
            mutation($wikiId: ID!, $modelId: ID! ){
                updateModeledWiki(wikiId: $wikiId, model: $modelId){
                    _id
                }
            } 
        """
        api_query(query, variables={'wikiId': _id, 'modelId': model_id})


def main():
    login()
    manifest = load_manifest()
    model_ids = upload_models(manifest)
    all_wikis = get_all_wikis()
    ids = get_wiki_ids(manifest, all_wikis)
    update_wikis(ids, model_ids)


if __name__ == '__main__':
    main()

