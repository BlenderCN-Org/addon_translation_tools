#!/bin/sh

for f in `find . -name "*.py"`
do
    python -m py_compile $f
done
rm *.pyc
rm -fr ~/.config/blender/2.79/scripts/addons/bpy_translation_tools
cp -r ../bpy_translation_tools ~/.config/blender/2.79/scripts/addons/
