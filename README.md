# rpgtools-srd

This repo contains the Dungeons and Dragons SRD that can be imported into rpgtools.

## Usage

1) Download a zip from the release section in this repo
2) Open RPG tools and navigate to the Wiki section in a world you have access to
3) Right click a destination folder and select the 'Import' option
4) Select the zip that downloaded in step 1 and click the 'Import' button

## Requirements
If you want to regenerate this data, you will need the following requirements:
- python3
- blender
- local installation of rpgtools

## Generation
How was this data created?

1) run make_manifiest.py
2) make manual edits to manifest.csv concerning which thingiverse things to use
3) run process_manifest.py
4) make manual edits to manifest.csv concerning which stl files to use
5) check the .png images created in the workspace directory to find models that were rerendered incorrectly
6) delete .png and .glb files to rerender
7) return to step 3 as needed
8) make sure rpgtools is running locally with the srd wiki pages already imported
9) run upload.py
10) right click on 5e folder and click export

## Credit
Credit goes to mz4520 for creating the monster models and providing them for free under the Creative Commons license.
Please check out his work and support him at https://www.thingiverse.com/mz4250/designs