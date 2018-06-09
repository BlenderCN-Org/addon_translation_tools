import bpy

translation_dict = {
    "ja_JP": {
        ("*", "Speed"): "速度",
        ("*", "Phase 1"): "フェーズ1",
        ("*", "Phase 2"): "フェーズ2",
        ("*", "Phase 3"): "フェーズ3",
        ("*", "Phase 4"): "フェーズ4",
        ("*", "Base"): "ベース",
        ("*", "Value"): "値",
        ("*", "Start"): "開始",
        ("*", "End"): "終了",
        ("*", "Frequency"): "頻度",
        ("*", "Seed"): "シード",
        ("*", "Scale"): "拡大縮小",
        ("*", "Strength"): "強さ",
        ("Operator", "Insert"): "挿入",
        ("*", "Batch Mode"): "バッチモード",
        ("*", "Noise"): "ノイズ",
        ("Operator", "Remove Modifier"): "モディファイアーを除去",
        ("Operator", "Add Modifier"): "追加",
        ("*", "Text"): "テキスト",
        ("*", "Text in hiragana or romaji"): "ひらがな/ローマ字のテキスト",
        ("*", "Maximum value of shape key"): "シェイプキーの最大値",
        ("*", "Blend In"): "ブレンドイン",
        ("*", "Blend Out"): "ブレンドアウト",
        ("*", "Open"): "開く",
        ("*", "Overlap"): "オーバーラップ",
        ("*", "Weights"): "ウェイト",
        ("*", "a"): "あ",
        ("*", "i"): "い",
        ("*", "u"): "う",
        ("*", "e"): "え",
        ("*", "o"): "お",
        ("Operator", "Update"): "更新",
    },
}

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
