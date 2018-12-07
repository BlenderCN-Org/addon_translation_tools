# -*- coding: utf-8 -*-
import bpy
from bpy.props import *
import importlib

try:
    importlib.reload(translation_tools_panel)
    importlib.reload(translation_tools_operator)
    importlib.reload(translation_tools_translation_ja)
except:
    from . import translation_tools_panel
    from . import translation_tools_operator
    from . import translation_tools_translation_ja

bl_info = {
    "name": "Addon Translation Tools",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "author": "nagadomi@nurs.or.jp",
    "category": "User Interface",
    "location": "Text Editor > Tools Panel > Addon Translation .+",
}

classes = (
    translation_tools_panel.ItemProperty,
    translation_tools_panel.PanelProperty,
    translation_tools_panel.TextTranslationProperty,
    translation_tools_operator.TemplateGenerateOperator,
    translation_tools_operator.ModuleGenerateOperator,
    translation_tools_panel.ItemUL,
    translation_tools_panel.TemplateGeneratorPanel,
    translation_tools_panel.ItemPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Text.translation_tools = PointerProperty(type=translation_tools_panel.TextTranslationProperty)
    bpy.types.Scene.translation_tools = PointerProperty(type=translation_tools_panel.PanelProperty)
    translation_tools_translation_ja.register(__package__)

def unregister():
    del bpy.types.Scene.translation_tools
    del bpy.types.Text.translation_tools
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    translation_tools_translation_ja.unregister(__package__)
