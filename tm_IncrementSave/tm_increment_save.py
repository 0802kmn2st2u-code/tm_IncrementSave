# -*- coding: utf_8 -*-

"""
202601425_v000
RyoToyama
TM Increment Save + Hotkey Tool
"""

import re
import os
import sys
import shutil
import importlib.util
import maya.cmds as cmds


WINDOW_NAME = "tm_IncrementSave"
BASE_SET = "Maya_Default"
CUSTOM_SET = "TM_CustomHotkeys"
TARGET_FUNCTION = "save_backup"

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

TOOL_PATH = f"{tool_dir}/tm_increment_save.py"


# =====================================================
# 共通設定
# =====================================================
def get_scene_path():
    return cmds.file(q=True, sceneName=True)


def get_scene_dir():
    scene_path = get_scene_path()
    if not scene_path:
        return ""
    return os.path.dirname(scene_path)


def get_default_backup_folder():
    scene_dir = get_scene_dir()
    if not scene_dir:
        return ""
    return os.path.join(scene_dir, "_backup")


def get_backup_folder():
    """
    基本はデフォルト値。
    UIが存在する場合のみUI値で上書き。
    """
    backup_dir = get_default_backup_folder()

    try:
        if cmds.textField("backupFolderField", exists=True):
            ui_value = cmds.textField(
                "backupFolderField",
                q=True,
                text=True
            )

            if ui_value:
                backup_dir = ui_value
    except:
        pass

    return backup_dir


# =====================================================
# バックアップ保存
# =====================================================
def save_backup():

    scene_path = get_scene_path()

    if not scene_path:
        cmds.warning(u"シーンが保存されていません。")
        return

    cmds.file(save=True)

    scene_name = os.path.basename(scene_path)
    file_name, ext = os.path.splitext(scene_name)

    backup_dir = get_backup_folder()

    if not backup_dir:
        cmds.warning(u"バックアップフォルダ未設定")
        return

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    pattern = re.compile(
        r"^{}_backup(\d{{4}}){}$".format(
            re.escape(file_name),
            re.escape(ext)
        )
    )

    max_num = 0

    for backup_file in os.listdir(backup_dir):
        match = pattern.match(backup_file)

        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    next_num = max_num + 1

    backup_name = "{}_backup{:04d}{}".format(
        file_name,
        next_num,
        ext
    )

    backup_path = os.path.join(
        backup_dir,
        backup_name
    )

    shutil.copy2(
        scene_path,
        backup_path
    )

    print(f"元ファイル保存: {scene_path}")
    print(f"バックアップ保存: {backup_path}")
    cmds.inViewMessage(
        msg=f"元ファイル保存: {scene_path}\nバックアップ保存: {backup_path}",
        pos="midCenterTop",
        fade=True
    )


# =====================================================
# 整理版保存
# =====================================================
def save_clean_version():

    scene_path = get_scene_path()

    if not scene_path:
        cmds.warning(u"シーンが保存されていません。")
        return

    cmds.file(save=True)

    scene_dir = os.path.dirname(scene_path)
    scene_name = os.path.basename(scene_path)
    file_name, ext = os.path.splitext(scene_name)

    clean_name = re.sub(
        r"(_v\d+|_ver\d+)",
        "",
        file_name,
        flags=re.IGNORECASE
    )

    clean_scene_path = os.path.join(
        scene_dir,
        clean_name + ext
    )

    file_type = cmds.file(
        q=True,
        type=True
    )

    file_type = file_type[0] if file_type else "mayaBinary"

    cmds.file(rename=clean_scene_path)
    cmds.file(save=True, type=file_type)

    print(u"整理版保存: {}".format(clean_scene_path))

    cmds.file(rename=scene_path)

    refresh_ui_info()


# =====================================================
# Hotkey Utility
# =====================================================
def hotkey_set_exists(name):
    sets = cmds.hotkeySet(
        q=True,
        hotkeySetArray=True
    ) or []

    return name in sets


def get_current_hotkey_set():
    return cmds.hotkeySet(
        q=True,
        current=True
    )


def create_custom_hotkey_set():

    if hotkey_set_exists(CUSTOM_SET):
        return

    if not hotkey_set_exists(BASE_SET):
        raise RuntimeError(
            "Base hotkey set not found"
        )

    cmds.hotkeySet(
        CUSTOM_SET,
        source=BASE_SET,
        current=True
    )


def apply_custom_hotkeys():

    command_code = r'''
import maya.cmds as cmds
import os
import sys
import importlib.util

tool_path = r"{tool_path}"
function_name = "{function_name}"

if os.path.exists(tool_path):

    tool_dir = os.path.dirname(tool_path)

    if tool_dir not in sys.path:
        sys.path.insert(0, tool_dir)

    module_name = os.path.splitext(
        os.path.basename(tool_path)
    )[0]

    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(
        module_name,
        tool_path
    )

    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module

    spec.loader.exec_module(module)

    if hasattr(module, function_name):
        getattr(module, function_name)()
'''.format(
        tool_path=TOOL_PATH.replace("\\", "/"),
        function_name=TARGET_FUNCTION
    )

    runtime_name = "TM_RunSpecificFunction"
    name_command = "TM_RunSpecificFunctionNameCommand"

    try:
        cmds.runTimeCommand(
            runtime_name,
            edit=True,
            delete=True
        )
    except:
        pass

    cmds.runTimeCommand(
        runtime_name,
        category="User",
        commandLanguage="python",
        command=command_code
    )

    try:
        cmds.nameCommand(
            name_command,
            edit=True,
            delete=True
        )
    except:
        pass

    cmds.nameCommand(
        name_command,
        annotation="TM Increment Save",
        command=runtime_name
    )

    cmds.hotkey(
        k='s',
        ctl=True,
        alt=True,
        name=name_command
    )

    cmds.savePrefs(hotkeys=True)


def remove_custom_hotkeys():

    cmds.hotkey(
        k='s',
        ctl=True,
        alt=True,
        name=""
    )

    cmds.savePrefs(hotkeys=True)


def toggle_tm_hotkeys(*args):

    current = get_current_hotkey_set()

    if current != CUSTOM_SET:

        if not hotkey_set_exists(CUSTOM_SET):
            create_custom_hotkey_set()

        cmds.hotkeySet(
            CUSTOM_SET,
            edit=True,
            current=True
        )

        apply_custom_hotkeys()

        print("TM Custom Hotkeys ENABLED")

    else:

        remove_custom_hotkeys()

        if hotkey_set_exists(BASE_SET):
            cmds.hotkeySet(
                BASE_SET,
                edit=True,
                current=True
            )

        print("TM Custom Hotkeys DISABLED")

    refresh_ui_info()


# =====================================================
# UI Utility
# =====================================================
def get_scene_name():

    scene_path = get_scene_path()

    if not scene_path:
        return u"未保存シーン"

    return os.path.basename(scene_path)


def get_hotkey_status():

    return (
        "ON"
        if get_current_hotkey_set() == CUSTOM_SET
        else "OFF"
    )


def browse_backup_folder(*args):

    folder = cmds.fileDialog2(
        dialogStyle=2,
        fileMode=3,
        caption=u"バックアップフォルダ選択"
    )

    if folder:
        cmds.textField(
            "backupFolderField",
            e=True,
            text=folder[0]
        )


def refresh_ui_info(*args):

    try:

        if cmds.textField(
            "sceneNameField",
            exists=True
        ):
            cmds.textField(
                "sceneNameField",
                e=True,
                text=get_scene_name()
            )

        if cmds.textField(
            "backupFolderField",
            exists=True
        ):
            current_text = cmds.textField(
                "backupFolderField",
                q=True,
                text=True
            )

            if not current_text:
                cmds.textField(
                    "backupFolderField",
                    e=True,
                    text=get_default_backup_folder()
                )

        if cmds.textField(
            "hotkeyStatusField",
            exists=True
        ):
            cmds.textField(
                "hotkeyStatusField",
                e=True,
                text=get_hotkey_status()
            )

    except:
        pass


# =====================================================
# UI構築
# =====================================================
def ui_run():

    if cmds.window(
        WINDOW_NAME,
        exists=True
    ):
        cmds.deleteUI(WINDOW_NAME)

    cmds.window(
        WINDOW_NAME,
        title=u"TM Increment Save Tool",
        widthHeight=(800, 300),
        sizeable=True
    )

    main_layout = cmds.columnLayout(
        adjustableColumn=True
    )

    cmds.separator(
        height=10,
        style='none'
    )

    cmds.text(
        label=u"現在のシーン名",
        align='left'
    )

    cmds.textField(
        "sceneNameField",
        text=get_scene_name(),
        editable=False
    )

    cmds.separator(
        height=10,
        style='none'
    )

    cmds.text(
        label=u"save_backup対象フォルダ",
        align='left'
    )

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[
            (1, 'both', 0),
            (2, 'both', 5)
        ]
    )

    cmds.textField(
        "backupFolderField",
        text=get_default_backup_folder(),
        editable=True
    )

    cmds.button(
        label=u"参照",
        width=80,
        command=browse_backup_folder
    )

    cmds.setParent(main_layout)

    cmds.separator(
        height=10,
        style='none'
    )

    cmds.text(
        label=u"キーコンフィグ状態 (Ctrl+Alt+S)",
        align='left'
    )

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[
            (1, 'both', 0),
            (2, 'both', 5)
        ]
    )

    cmds.textField(
        "hotkeyStatusField",
        text=get_hotkey_status(),
        editable=False
    )

    cmds.button(
        label=u"切替",
        width=80,
        command=toggle_tm_hotkeys
    )

    cmds.setParent(main_layout)

    cmds.separator(
        height=15,
        style='in'
    )

    cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAttach=[
            (1, 'both', 5),
            (2, 'both', 5)
        ]
    )

    cmds.button(
        label=u"save_backup 実行",
        height=50,
        command=lambda x: save_backup()
    )

    cmds.button(
        label=u"save_clean_version 実行",
        height=50,
        command=lambda x: save_clean_version()
    )

    cmds.setParent(main_layout)

    cmds.separator(
        height=10,
        style='none'
    )

    cmds.showWindow(WINDOW_NAME)

    refresh_ui_info()


# =====================================================
# 実行
# =====================================================
# ui_run()
