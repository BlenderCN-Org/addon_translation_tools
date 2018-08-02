#!/bin/sh

for f in `find . -name "*.py"`
do
    python -m py_compile $f
done
pwd=`pwd`
name=`basename $pwd`
rm *.pyc
rm -fr ~/.config/blender/2.79/scripts/addons/${name}
cp -r ../${name} ~/.config/blender/2.79/scripts/addons/
