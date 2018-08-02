#!/bin/sh
tag=`git describe --abbrev=0 --tags`
git archive ${tag} --format=zip --prefix=addon_translation_tools/ --output=addon_translation_tools_${tag}.zip
