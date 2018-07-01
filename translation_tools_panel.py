import bpy
from bpy.props import *
from bpy.types import Operator, Panel, UIList, PropertyGroup
import addon_utils
import importlib

try:
    importlib.reload(translation_tools_operator)
except:
    from . import translation_tools_operator

def get_panel_prop(context):
    return context.user_preferences.addons[__package__].preferences.panel_prop

g_category_cache = None
g_addon_cache = None
g_addon_cached_category = None

def build_category_items_callback(self, context):
    global g_category_cache
    if g_category_cache is None:
        categories = set()
        for mod in addon_utils.modules():
            bl_info = addon_utils.module_bl_info(mod)
            if bl_info["category"]:
                categories.add(bl_info["category"])

        categories = ["All"] + sorted(list(categories), key=lambda x: x.upper(), reverse=True)
        items = []
        for c in categories:
            c = str(c)
            items.append((c, c, c))
        g_category_cache = tuple(items)
    return g_category_cache

def build_addon_items_callback(self, context):
    global g_addon_cache
    global g_addon_cached_category

    props = get_panel_prop(context)
    if (g_addon_cache is None or
            g_addon_cached_category is None or
            g_addon_cached_category != props.category):
        items = []
        for mod in addon_utils.modules():
            bl_info = addon_utils.module_bl_info(mod)
            if (not props.category or
                    props.category == "All" or
                    props.category == bl_info["category"]):
                items.append((mod.__file__, bl_info["name"], mod.__file__))
        g_addon_cached_category = props.category
        g_addon_cache = tuple(sorted(items, key=lambda x: x[1].upper(), reverse=True))
    return g_addon_cache

def build_locale_items():
    items = []
    for locale in bpy.app.translations.locales:
        if locale != "en_US":
            items.append((locale, locale, locale))
    return tuple(sorted(items, key=lambda x: x[0].upper()))

class PanelProperty(PropertyGroup):
    def update_addon(self, context):
        if self.addon:
            for mod in addon_utils.modules():
                if mod.__file__ == self.addon:
                    self.text_ctxt = mod.__name__
                    break
        return None
    category = EnumProperty(name="Category", items=build_category_items_callback)
    addon = EnumProperty(name="Addon", items=build_addon_items_callback, update=update_addon)
    locale = EnumProperty(name="Locale", items=build_locale_items())
    use_text_ctxt = BoolProperty(name="Use text_ctxt", default=False)
    text_ctxt = StringProperty(name="text_ctxt",
                                   description="Override automatic translation context of the given text")
    updatable = BoolProperty(name="Updatable Flag", default=True)

def update_translation_callback(self, context):
    panel_prop = get_panel_prop(context)
    if panel_prop.updatable:
        translation_prop = context.space_data.text.translation_tools
        print("update_translation_callback")
        if translation_prop.use_text_ctxt:
            panel_prop.use_text_ctxt = True
            panel_prop.text_ctxt = translation_prop.text_ctxt
        else:
            panel_prop.use_text_ctxt = False
            panel_prop.text_ctxt = ""
        bpy.ops.translation_tools.generate_module()
        bpy.ops.text.run_script()

class ItemProperty(PropertyGroup):
    msgid = StringProperty(name="Label")
    msgstr = StringProperty(name="Translation", update=update_translation_callback)
    ctx = StringProperty(name="Translation Context")

    file_rel_path = StringProperty(name="Relative Path")
    file_full_path = StringProperty(name="Full Path")
    lineno = IntProperty(name="Line Number")
    function = StringProperty(name="Function Name")
    keyword = StringProperty(name="Keyword Name")

class TextTranslationProperty(PropertyGroup):
    addon_path = StringProperty(name="Addon Path")
    locale = StringProperty(name="Locale")
    items = CollectionProperty(type=ItemProperty, name="Items")
    error_items = CollectionProperty(type=ItemProperty, name="Error Items")
    items_active_index = IntProperty(name="Items Index")
    error_items_active_index = IntProperty(name="Error Items Index")
    use_text_ctxt = BoolProperty(name="Use text_ctxt", default=False, update=update_translation_callback)
    text_ctxt = StringProperty(name="text_ctxt",
                                   description="Override automatic translation context of the given text",
                                   update=update_translation_callback)

class TemplateGeneratorPanel(Panel):
    bl_label = "Addon Translation Generator"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        props = get_panel_prop(context)
        c = self.layout.column(align=True)
        c.prop(props, 'category')
        c.prop(props, 'addon')
        c.prop(props, 'locale')
        c.prop(props, 'use_text_ctxt')
        if props.use_text_ctxt:
            c.prop(props, 'text_ctxt')

        c = self.layout.column()
        c.operator(translation_tools_operator.TemplateGenerateOperator.bl_idname, "Generate")

    @classmethod
    def poll(cls, context):
        return True

class ItemUL(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        s = row.split(percentage=0.5)
        c = s.column()
        c.alignment = "RIGHT"
        c.label(text=item.msgid, translate=False)
        s.prop(item, "msgstr", text="")

    def draw_filter(self, context, layout):
        pass

class ItemPanel(Panel):
    bl_label = "Addon Translation Items"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"

    @staticmethod
    def __chunked(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def draw(self, context):
        prop = context.space_data.text.translation_tools
        c = self.layout.column(align=True)
        c.prop(prop, "use_text_ctxt")
        if prop.use_text_ctxt:
            c.prop(prop, "text_ctxt")

        c = self.layout.column()
        c.template_list("ItemUL", "",
                            prop, "items",
                            prop, "items_active_index")
        if prop.items_active_index >= 0 and prop.items_active_index < len(prop.items):
            item = prop.items[prop.items_active_index]
            c.label(text="[{}] {}({}): {}({})".format(
                prop.items_active_index,
                item.file_rel_path,
                item.lineno,
                item.function,
                item.keyword
                ), translate=False)
            b = self.layout.box()
            c = b.column(align=True)
            chunks = list(self.__chunked(str(item.msgid).split(" "), 5))
            for s in chunks:
                c.label(text=" ".join(s), translate=False)

    @classmethod
    def poll(cls, context):
        return (context.space_data.text and
                    context.space_data.text.translation_tools and
                    len(context.space_data.text.translation_tools.items) > 0)

class ErrorItemPanel(Panel):
    bl_label = "Addon Translation Errors"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        pass

    @classmethod
    def poll(cls, context):
        return (context.space_data.text and
                    context.space_data.text.translation_tools and
                    len(context.space_data.text.translation_tools.error_items) > 0)

