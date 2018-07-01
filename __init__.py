# -*- coding: utf-8 -*-
import bpy
from bpy.props import *
from bpy.types import AddonPreferences
import importlib

try:
    importlib.reload(translation_tools_panel)
    importlib.reload(translation_tools_operator)
except:
    from . import translation_tools_panel
    from . import translation_tools_operator

bl_info = {
    "name": "Addon Translation Tools",
    "version": (0, 1, 0),
    "author": "nagadomi@nurs.or.jp",
    "category": "User Interface",
    "location": "Text Editor > Tools Panel > Addon Translation .+",
}

class AddonTranslationTools(AddonPreferences):
    bl_idname = __package__
    panel_prop = PointerProperty(type=translation_tools_panel.PanelProperty)
    def draw(self, context):
        pass

def register():
    bpy.utils.register_module(__package__)
    bpy.types.Text.translation_tools = PointerProperty(type=translation_tools_panel.TextTranslationProperty)

def unregister():
    del bpy.types.Text.translation_tools
    bpy.utils.unregister_module(__package__)

if __name__ == "__main__":
    register()