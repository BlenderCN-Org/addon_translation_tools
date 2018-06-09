# bpy_translation_tools

`bpy_translation_tools`はBlenderアドオンを翻訳するための補助ツールです。

## Blenderアドオンのソースコードから翻訳ファイルを生成する

`make_translation_file.py`は翻訳ファイルをアドオンのソースコードから自動で生成します。

```shell
$ blender -b -P make_translation_file.py -- -i <addon dir>
```
`{basename}.{locale}.txt`が生成されます。`-o`オプションで出力ファイルパス、`--locale`オプションで対象ロケールを指定できます。`--locale`が指定されない場合は、Blenderユーザー設定の言語が使われます。

生成されたらファイルを翻訳します。ファイルは以下のフォーマットになっています。
```
"ラベル","翻訳テキスト","context","comment"
```

出力例を見てください [examples/blender_mmd_lip_tools.ja_JP.txt](examples/blender_mmd_lip_tools.ja_JP.txt)。

## 翻訳ファイルから翻訳モジュールを生成する

`make_translation_module.py`は、翻訳をBlenderに登録するためのPythonモジュールを生成します。出力例を見てください[examples/blender_mmd_lip_tools_translation.py](examples/blender_mmd_lip_tools_translation.py).

```shell
$ python make_translation_module.py -i <translated file> -o <output module filename>
```
ファイル名は、`{addon_name}.{locale}.txt`の形式でなければならないことに注意してください。

複数のロケールに対する翻訳ファイルがある場合は、`-i file1.txt -i file2.txt -i file3.txt`のように複数の入力オプションを指定できます。

生成されたPythonモジュールは、あなたのBlenderアドオンで使用できます。
```python
from . import translation_module

def register():
    translation_module.register()
    # ...

def unregister():
    # ...
    translation_module.unregister()
```
