# bpy_translation_tools

`bpy_translation_tools` is a helper tool for translating Blender Addon.

`bpy_translation_tools`はBlenderアドオンを翻訳するための補助ツールです。

[日本語README](README.ja.md)

## Generating translation file from Blender Addon source codes

`make_translation_file.py` automatically generates the translation file from python source codes of Blender Addon.

```shell
$ blender -b -P make_translation_file.py -- -i <addon dir>
```

`{basename}.{locale}.txt` will be created. You can specify `-o` option for the output file path and `--locale` options for the target locale. When `--locale` is not specified, Language setting on UserPreference is used.

Then, translate the file. The file is formatted as:
```
"label text","translated text","context","comment"
```

See outpu example [examples/blender_mmd_lip_tools.ja_JP.txt](examples/blender_mmd_lip_tools.ja_JP.txt)

## Generating translation module from translated file

`make_translation_module.py` generates the python module for registering translations to Blender from the translated file. See output example [examples/blender_mmd_lip_tools_translation.py](examples/blender_mmd_lip_tools_translation.py).

```shell
$ python make_translation_module.py -i <translated file> -o <output module filename>
```
Note that the input filename must be formatted as `{addon_name}.{locale}.txt`. 

If you have translation files for multiple locales, you can specify multiple input option like `-i file1.txt -i file2.txt -i file3.txt`

The generated python module can be used in your Blender addon.
```python
from . import translation_module

def register():
    translation_module.register()
    # ...

def unregister():
    # ...
    translation_module.unregister()
```
