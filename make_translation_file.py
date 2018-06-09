# $ blender -b -P make_translation_file.py -- -i <input dir> --locale <locale> -o <output path>
import sys
import os
import ast
import glob
import csv
import argparse
import bpy

class BlenderPropInfo():
    def __init__(self, filename=None, lineno=None, function_name=None, keyword=None, text=None):
        self.filename = filename
        self.lineno = lineno
        self.function_name = function_name
        self.keyword = keyword
        self.text = text

    def __str__(self):
        return "{}({}):{}({}={})".format(self.filename, self.lineno,
                                        self.function_name, self.keyword, self.text)
    def __repr__(self):
        return self.__str__()

class BlenderPropExtractor(ast.NodeVisitor):
    TARGET_LIST = {
        # prop
        "IntProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "FloatProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "StringProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "EnumProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "BoolProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "IntVectorProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "FloatVectorProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "BoolVectorProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "CollectionProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        "PointerProperty": [{"keyword": "name", "index": 0}, {"keyword": "description", "index": 1}],
        # layout
        "template_any_ID": {"keyword": "text", "index": 3},
        "template_path_builder": {"keyword": "text", "index": 3},
        "prop": {"keyword": "text", "index": 2},
        "prop_menu_enum": {"keyword": "text", "index": 2},
        "prop_enum": {"keyword": "text", "index": 3},
        "prop_search": {"keyword": "text", "index": 4},
        "operator": {"keyword": "text", "index": 1},
        "operator_menu_enum": {"keyword": "text", "index": 2},
        "label": {"keyword": "text", "index": 0},
        "menu": {"keyword": "text", "index": 1},
    }

    def __init__(self):
        super(BlenderPropExtractor, self).__init__()
        self.prop_list = []
        self.prop_error_list = []

    def add_result(self, function_name, keyword, text, lineno):
        self.prop_list.append(BlenderPropInfo(
            function_name=function_name, keyword=keyword, text=text,
            lineno=lineno))
    
    def add_error(self, function_name, keyword, dump, lineno):
        self.prop_error_list.append(BlenderPropInfo(
            function_name=function_name, keyword=keyword, text=dump, lineno=lineno))
    def get_results(self):
        return self.prop_list, self.prop_error_list
    
    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        if func_name and (func_name in BlenderPropExtractor.TARGET_LIST):
            targets = BlenderPropExtractor.TARGET_LIST[func_name]
            if isinstance(targets, dict):
                targets = [targets]
            for target in targets:
                if len(node.args) > target["index"]:
                    if isinstance(node.args[target["index"]], ast.Str):
                        self.add_result(func_name, target["keyword"], node.args[target["index"]].s, node.lineno)
                    else:
                        self.add_error(func_name, target["keyword"], ast.dump(node.args[target["index"]]), node.lineno)
                for keyword in node.keywords:
                    if keyword.arg == target["keyword"]:
                        if isinstance(keyword.value, ast.Str):
                            self.add_result(func_name, target["keyword"], keyword.value.s, node.lineno)
                        else:
                            self.add_error(func_name, target["keyword"], ast.dump(keyword.value), node.lineno)
        else:
            pass

if __name__ == "__main__":
    print("\n-------------- begin make_translation_file.py --------------\n")
    
    my_argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser(prog="blender -b -P make_translation_file.py -- ", description="bpy.props.* extractor for translation")
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
                    if prop.function_name == "operator":
                        ctx = "Operator"
                    else:
                        ctx = "*"
                    translation = bpy.app.translations.pgettext(prop.text, ctx)
                    if translation == prop.text and (not args.copy_original_text):
                        translation = ""
                    if (not args.without_description or prop.function_name == "name"):
                        # msgid, translation, comment
                        writer.writerow([prop.text, translation, ctx, "{}({}):{}({})".format(prop.filename, prop.lineno, prop.function_name, prop.keyword)])
                for err in errors:
                    err.filename = os.path.relpath(filename, args.input_dir)
                    sys.stderr.write("{}({}):{}({}): Warning: Failed to detect msgid, skipped.\n\t{}\n".format(err.filename, err.lineno, err.function_name, err.keyword, err.text))
    print("\n-------------- end   make_translation_file.py --------------\n")
