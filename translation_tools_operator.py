import bpy
from bpy.types import Operator
import addon_utils
import sys
import os
import ast
import glob
import csv
import argparse
import bpy

class BPYPropInfo():
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

class BPYPropExtractor(ast.NodeVisitor):
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
        super(BPYPropExtractor, self).__init__()
        self.prop_list = []
        self.prop_error_list = []

    def add_result(self, function_name, keyword, text, lineno):
        self.prop_list.append(BPYPropInfo(
            function_name=function_name, keyword=keyword, text=text,
            lineno=lineno))
    
    def add_error(self, function_name, keyword, dump, lineno):
        self.prop_error_list.append(BPYPropInfo(
            function_name=function_name, keyword=keyword, text=dump, lineno=lineno))

    def get_results(self):
        return self.prop_list, self.prop_error_list
    
    def visit_Call(self, node):
        func_name = None
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        if func_name and (func_name in BPYPropExtractor.TARGET_LIST):
            targets = self.TARGET_LIST[func_name]
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

def set_translation_item(item, prop, input_dir, is_error):
    item.msgid = prop.text
    item.function = prop.function_name
    item.keyword = prop.keyword
    item.file_full_path = prop.filename
    item.lineno = prop.lineno
    if input_dir:
        item.file_rel_path = os.path.relpath(prop.filename, input_dir)
    else:
        item.file_rel_path = os.path.basename(prop.filename)
    if prop.function_name == "operator" or prop.function_name == "operator_menu_enum":
        item.ctx = "Operator"
    else:
        item.ctx = "*"
    if not is_error:
        msgstr = bpy.app.translations.pgettext(item.msgid, item.ctx)
        if msgstr == item.msgid:
            item.msgstr = ""
        else:
            item.msgstr = msgstr

def build_tralsnation_items(mod, locale, bpy_text):
    use_international_fonts = bpy.context.user_preferences.system.use_international_fonts
    bpy.context.user_preferences.system.use_international_fonts = True
    locale_backup = bpy.context.user_preferences.system.language
    bpy.context.user_preferences.system.language = locale
    try:
        bpy_text.translation_tools.updatable = False
        bpy_text.translation_tools.items.clear()
        bpy_text.translation_tools.error_items.clear()

        basename = os.path.basename(mod.__file__)
        if basename == "__init__.py":
            input_dir = os.path.dirname(mod.__file__)
            scripts = glob.iglob(os.path.join(input_dir, "**", "*.py"), recursive=True)
        else:
            input_dir = None
            scripts = [mod.__file__]
        found = set()
        for filename in scripts:
            with open(filename, "r") as ifp:
                root = ast.parse(ifp.read())
                hook = BPYPropExtractor()
                hook.visit(root)
                props, errors = hook.get_results()
                for prop in props:
                    if (not prop.text) or (prop.text in found):
                        continue
                    found.add(prop.text)
                    prop.filename = filename
                    item = bpy_text.translation_tools.items.add()
                    set_translation_item(item, prop, input_dir=input_dir, is_error=False)
                for err in errors:
                    prop.filename = filename                
                    item = bpy_text.translation_tools.error_items.add()
                    set_translation_item(item, prop, input_dir=input_dir, is_error=True)
    finally:
        bpy.context.user_preferences.system.language = locale_backup
        bpy.context.user_preferences.system.use_international_fonts = use_international_fonts
        bpy_text.translation_tools.updatable = True

class TemplateGenerateOperator(Operator):
    bl_idname = "addon_translation_tools.generate_template"
    bl_label = "Parse addon and Generate translation items"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    @staticmethod
    def __make_text_name(mod, locale):
        return "{}_translation_{}.py".format(mod.__name__, locale)

    @staticmethod
    def __find_module(addon_file):
        for mod in addon_utils.modules():
            if mod.__file__ == addon_file:
                return mod
        return None

    @classmethod
    def poll(cls, context):
        return context.space_data.type == "TEXT_EDITOR"

    def execute(self, context):
        props = context.user_preferences.addons[__package__].preferences.panel_prop
        if not (props.addon and props.locale):
            self.report({"ERROR"}, "addon and locale not selected")
            return {"CANCELED"}
        mod = self.__find_module(props.addon)
        if mod is None:
            self.report({"ERROR"}, "Could not find addon")
            return {"CANCELED"}
        locale = props.locale
        name = self.__make_text_name(mod, locale)
        if name in bpy.data.texts:
            text = bpy.data.texts[name]
        else:
            text = bpy.data.texts.new(name=name)
        text.use_fake_user = True
        text.translation_tools.addon_path = props.addon
        text.translation_tools.locale = props.locale
        build_tralsnation_items(mod, locale, text)
        context.space_data.text = text

        return {"FINISHED"}


MODULE_TEMPLATE = """# -*- coding: utf-8 -*-
# This code is generated by addon_translation_tools.

import bpy

translation_dict = ${TRANSLATION_DICT}

def register():
    if __package__:
        bpy.app.translations.register(__package__, translation_dict)
    elif __name__ != "__main__":
        bpy.bpy.app.translations.register(__name__, translation_dict)
    else:
        bpy.app.translations.register(__file__, translation_dict)

def unregister():
    if __package__:
        bpy.app.translations.unregister(__package__)
    elif __name__ != "__main__":
        bpy.app.translations.unregister(__name__)
    else:
        bpy.app.translations.unregister(__file__)

if __name__ == "__main__":
    unregister()
    # If you want to unregister the translation,
    # comment out the following line and run the script.
    register()
"""

class ModuleGenerateOperator(Operator):
    bl_idname = "translation_tools.generate_module"
    bl_label = "Generate the translation module from items"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (context.space_data.type == "TEXT_EDITOR" and
                    context.space_data.text and
                    len(context.space_data.text.translation_tools.items) > 0)
    def execute(self, context):
        bpy_text = context.space_data.text
        prop = bpy_text.translation_tools
        translation_dict = "{\n"
        translation_dict += r'    "{}": '.format(prop.locale) + "{\n"
        for item in prop.items:
            if not item.msgid or not item.msgstr:
                continue
            msgid = item.msgid.replace(r'"', r'\"')
            msgstr = item.msgstr.replace(r'"', r'\"')
            if msgid and msgstr:
                translation_dict += r'        ("{}", "{}"): "{}",'.format(
                    item.ctx, msgid, msgstr) + "\n"

        translation_dict += "    }\n"
        translation_dict += "}"
        bpy_text.clear()
        bpy_text.write(MODULE_TEMPLATE.replace("${TRANSLATION_DICT}", translation_dict))

        context.space_data.show_line_numbers = True
        context.space_data.show_syntax_highlight = True
        
        return {"FINISHED"}
