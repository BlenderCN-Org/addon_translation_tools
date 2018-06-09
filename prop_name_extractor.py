# $ blender -b -P prop_name_extractor.py -- -i <input dir> --locale <locale> -o <output path>
import sys
import os
import ast
import glob
import csv
import argparse
import bpy

class BlenderPropInfo():
    def __init__(self, filename=None, lineno=None, type_name=None, keyword=None, text=None):
        self.filename = filename
        self.lineno = lineno
        self.type_name = type_name
        self.keyword = keyword
        self.text = text

    def __str__(self):
        return "{}({}):{}({}={})".format(self.filename, self.lineno,
                                        self.type_name, self.keyword, self.text)
    def __repr__(self):
        return self.__str__()

class BlenderPropExtractor(ast.NodeVisitor):
    PROPS = [
        "FloatProperty", "IntProperty", "StringProperty", "EnumProperty", "BoolProperty",
        "FloatVectorProperty", "IntVectorProperty", "BoolVectorProperty", 
        "CollectionProperty","PointerProperty"]
    
    def __init__(self):
        super(BlenderPropExtractor, self).__init__()
        self.prop_list = []
        self.prop_error_list = []

    def add_result(self, type_name, keyword, text, lineno):
        self.prop_list.append(BlenderPropInfo(
            type_name=type_name, keyword=keyword, text=text,
            lineno=lineno))
    
    def add_error(self, type_name, keyword, dump, lineno):
        self.prop_error_list.append(BlenderPropInfo(
            type_name=type_name, keyword=keyword, text=dump, lineno=lineno))
    def get_results(self):
        return self.prop_list, self.prop_error_list
    
    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        if func_name and func_name in BlenderPropExtractor.PROPS:
            detected = False
            if len(node.args) > 0:
                if isinstance(node.args[0], ast.Str):
                    self.add_result(func_name, "name", node.args[0].s, node.lineno)
                else:
                    self.add_error(func_name, "name", ast.dump(node.args[0]), node.lineno)
            for keyword in node.keywords:
                if keyword.arg == "name":
                    if isinstance(keyword.value, ast.Str):
                        self.add_result(func_name, "name", keyword.value.s, node.lineno)
                    else:
                        self.add_error(func_name, "name", ast.dump(keyword.value), node.lineno)
                if keyword.arg == "description":
                    if isinstance(keyword.value, ast.Str):
                        self.add_result(func_name, "description", keyword.value.s, node.lineno)
                    else:
                        self.add_error(func_name, "description", ast.dump(keyword.value), node.lineno)

if __name__ == "__main__":
    print("\n-------------- begin prop_name_extractor.py --------------\n")
    
    my_argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser(prog="blender -b -P prop_name_extractor.py -- ", description="bpy.props.* extractor for translation")
    parser.add_argument("--input_dir", "-i", required=True, type=str,
                        help="Specify the input directory path.")
    parser.add_argument("--locale", "-l", type=str,
                        help="Specify the locale. {}".format(",".join(bpy.app.translations.locales)))
    parser.add_argument("--output", "-o", default=None, type=str,
                        help="Specify the Output file path.")
    parser.add_argument("--without_description", "-n", default=False, action="store_true",
                        help="Extract only `name` keyword.")
    parser.add_argument("--copy_original_text", "-c", default=False, action="store_true",
                        help="Copy original text to translated text column when no translation.")
    args = parser.parse_args(my_argv)

    bpy.context.user_preferences.system.use_international_fonts = True
    if args.locale:
        bpy.context.user_preferences.system.language = args.locale

    if args.output is None:
        basename = os.path.basename(args.input_dir)
        if basename:
            args.output = "{}.{}.csv".format(basename, bpy.app.translations.locale)
        else:
            args.output = "{}.{}.csv".format("addon_name", bpy.app.translations.locale)

    scripts = glob.iglob(os.path.join(args.input_dir, "**", "*.py"), recursive=True)
    
    found = {}
    with open(args.output, "w") as ofp:
        writer = csv.writer(ofp, delimiter=",", quoting=csv.QUOTE_ALL)
        for filename in scripts:
            with open(filename, "r") as ifp:
                root = ast.parse(ifp.read())
                hook = BlenderPropExtractor()
                hook.visit(root)
                props, errors = hook.get_results()
                for prop in props:
                    if (not prop.text) or (prop.text in found):
                        continue
                    found[prop.text] = True
                    prop.filename = os.path.relpath(filename, args.input_dir)
                    translation = bpy.app.translations.pgettext(prop.text)
                    if translation == prop.text and (not args.copy_original_text):
                        translation = ""
                    if (not args.without_description or prop.type_name == "name"):
                        # msgid, translation, comment
                        writer.writerow([prop.text, translation, "{}({}):{}({})".format(prop.filename, prop.lineno, prop.type_name, prop.keyword)])
                for err in errors:
                    err.filename = os.path.relpath(filename, args.input_dir)
                    sys.stderr.write("{}({}):{}({}): Warning: Failed to detect msgid, skipped.\n\t{}\n".format(err.filename, err.lineno, err.type_name, err.keyword, err.text))
    print("\n-------------- end   prop_name_extractor.py --------------\n")
