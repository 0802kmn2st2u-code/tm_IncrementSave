# -*- coding: utf-8 -*-
"""
Maya Custom Hotkey Override Tool
------------------------------------------------
目的:
・Maya標準キー設定を複製
・Ctrl+Alt+S に特定ツール内の特定関数を割り当て
・1つの関数でON/OFF切替
・既存設定を破壊せずオーバーライド

使用方法:
1. Script Editor の Python タブへ貼り付け
2. 実行
3. toggle_tm_hotkeys() でON/OFF切替
"""

import maya.cmds as cmds
import os

# =====================================================
# 設定
# =====================================================
BASE_SET = "Maya_Default"
CUSTOM_SET = "TM_CustomHotkeys"

user_docs_dir = os.path.expanduser("~/Documents")
base_dir = os.path.join(
    user_docs_dir,
    "maya",
    "scripts",
    "tm_script"
).replace("\\", "/")

tool_dir = os.path.join(
    base_dir,
    "tm_IncrementSave"
).replace("\\", "/")

# 実行対象ツールのフルパス
TOOL_PATH = f"{tool_dir}/tm_increment_save.py"

# 実行対象関数名
TARGET_FUNCTION = "save_backup"


# =====================================================
# ユーティリティ
# =====================================================
def hotkey_set_exists(name):
    sets = cmds.hotkeySet(q=True, hotkeySetArray=True) or []
    return name in sets


def get_current_hotkey_set():
    return cmds.hotkeySet(q=True, current=True)


def runtime_command_exists(name):
    commands = cmds.runTimeCommand(q=True, userCommandArray=True) or []
    return name in commands


def name_command_exists(name):
    try:
        count = cmds.assignCommand(query=True, numElements=True) or 0
        for i in range(1, count + 1):
            cmd_name = cmds.assignCommand(i, query=True, name=True)
            if cmd_name == name:
                return True
    except:
        pass
    return False


# =====================================================
# カスタムセット作成
# =====================================================
def create_custom_hotkey_set():

    if hotkey_set_exists(CUSTOM_SET):
        return

    if not hotkey_set_exists(BASE_SET):
        raise RuntimeError("Base hotkey set not found: {}".format(BASE_SET))

    cmds.hotkeySet(
        CUSTOM_SET,
        source=BASE_SET,
        current=True
    )

    print("Created custom hotkey set:", CUSTOM_SET)


# =====================================================
# RuntimeCommand更新
# =====================================================
def create_or_update_runtime_command(runtime_name, command_code):

    # 既存削除
    if runtime_command_exists(runtime_name):
        try:
            cmds.runTimeCommand(runtime_name, edit=True, delete=True)
        except:
            pass

    # 再作成
    cmds.runTimeCommand(
        runtime_name,
        category="User",
        commandLanguage="python",
        command=command_code
    )


# =====================================================
# NameCommand更新
# =====================================================
def create_or_update_name_command(name_command, runtime_name):

    if name_command_exists(name_command):
        try:
            count = cmds.assignCommand(query=True, numElements=True) or 0
            for i in range(1, count + 1):
                cmd_name = cmds.assignCommand(i, query=True, name=True)
                if cmd_name == name_command:
                    cmds.assignCommand(i, edit=True, delete=True)
                    break
        except:
            pass

    cmds.nameCommand(
        name_command,
        annotation="TM Specific Function Tool",
        command=runtime_name
    )


# =====================================================
# ホットキー適用
# =====================================================
def apply_custom_hotkeys():

    command_code = r'''
import maya.cmds as cmds
import os
import sys
import importlib.util

tool_path = r"{tool_path}"
function_name = "{function_name}"

if not os.path.exists(tool_path):
    cmds.warning("Tool file not found: " + tool_path)

else:
    try:
        tool_dir = os.path.dirname(tool_path)

        # ツールフォルダを追加
        if tool_dir not in sys.path:
            sys.path.insert(0, tool_dir)

        module_name = os.path.splitext(os.path.basename(tool_path))[0]

        # 古いモジュール削除
        if module_name in sys.modules:
            del sys.modules[module_name]

        # 読み込み
        spec = importlib.util.spec_from_file_location(module_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # 関数実行
        if hasattr(module, function_name):
            getattr(module, function_name)()
        else:
            cmds.warning("Function '{{}}' not found.".format(function_name))

    except Exception as e:
        cmds.warning("Tool execution failed: {{}}".format(e))
'''.format(
        tool_path=TOOL_PATH.replace("\\", "/"),
        function_name=TARGET_FUNCTION
    )

    runtime_name = "TM_RunSpecificFunction"
    name_command = "TM_RunSpecificFunctionNameCommand"

    # -------------------------------------------------
    # コマンド更新
    # -------------------------------------------------
    create_or_update_runtime_command(runtime_name, command_code)
    create_or_update_name_command(name_command, runtime_name)

    # -------------------------------------------------
    # Hotkey設定（即時適用）
    # -------------------------------------------------
    cmds.hotkey(
        k='s',
        ctl=True,
        alt=True,
        name=name_command
    )

    # Mayaへ即時反映
    cmds.savePrefs(hotkeys=True)

    print("Applied Ctrl+Alt+S custom hotkey immediately.")
    print("Tool Path :", TOOL_PATH)
    print("Function  :", TARGET_FUNCTION)


# =====================================================
# OFF処理
# =====================================================
def remove_custom_hotkeys():

    cmds.hotkey(
        k='s',
        ctl=True,
        alt=True,
        name=""
    )

    cmds.savePrefs(hotkeys=True)

    print("Removed Ctrl+Alt+S custom hotkey.")


# =====================================================
# ON / OFF切替
# =====================================================
def toggle_tm_hotkeys():

    current = get_current_hotkey_set()

    # ON
    if current != CUSTOM_SET:

        if not hotkey_set_exists(CUSTOM_SET):
            create_custom_hotkey_set()

        cmds.hotkeySet(CUSTOM_SET, edit=True, current=True)

        apply_custom_hotkeys()

        print("TM Custom Hotkeys ENABLED.")

    # OFF
    else:
        remove_custom_hotkeys()

        if hotkey_set_exists(BASE_SET):
            cmds.hotkeySet(BASE_SET, edit=True, current=True)

        print("TM Custom Hotkeys DISABLED. Returned to Maya Default.")


# =====================================================
# 状態確認
# =====================================================
def print_current_hotkey_set():
    print("Current Hotkey Set:", get_current_hotkey_set())


# =====================================================
# 実行例
# =====================================================
toggle_tm_hotkeys()
print_current_hotkey_set()
