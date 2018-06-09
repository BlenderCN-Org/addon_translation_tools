import sys
import os
import csv
import argparse

MODULE_TEMPLATE = """import bpy

translation_dict = ${TRANSLATION_DICT}

def register():
    if __package__:
        bpy.app.translations.register(__package__, translation_dict)
    else:
        bpy.bpy.app.translations.register(__name__, translation_dict)
def unregister():
    if __package__:
        bpy.app.translations.unregister(__package__)
    else:
        bpy.app.translations.unregister(__name__)
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="make translation module from translation.csv")
    parser.add_argument("--input", "-i", action="append", required=True, type=str,
                        help="Specify the input translated csv paths.")
    parser.add_argument("--output", "-o", default="translation.py", type=str,
                        help="Specify the Output file path.")
    args = parser.parse_args()
    
    translation_dict = "{\n"
    for filename in args.input:
        basename = os.path.basename(filename)
        addon_name, locale, ext = basename.split(".")
        if not (addon_name and locale and ext):
            sys.stderr.write("The filename must be `{addon_name}.{locale}.csv` format\n")
            sys.exit(-1)
        with open(filename, "r") as f:
            translation_dict += r'    "{}": '.format(locale) + "{\n"
            reader = csv.reader(f)
            for row in reader:
                key, translated_str, ctx, comment = row
                comment = str(comment)
                key = key.replace(r'"', r'\"')
                translated_str = translated_str.replace(r'"', r'\"')
                comment = comment.replace(r'"', r'\"')
                if key and translated_str:
                    translation_dict += r'        ("{}", "{}"): "{}",'.format(ctx, key, translated_str) + "\n"

            translation_dict += "    },\n"
    translation_dict += "}"

    with open(args.output, "w") as f:
        f.write(MODULE_TEMPLATE.replace("${TRANSLATION_DICT}", translation_dict) + "\n")
