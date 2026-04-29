# -*- coding: utf_8 -*-

"""
202601425_v000
RyoToyama
tm_IncrementSave
"""

# 説明
"""
差分バックアップを取る。
プロジェクトフォルダ分けが正確だと整理しやすくなる。

例としては、上書き保存時に
①元のシーン.ma（上書き保存）
②差分シーン_sv0001.ma(上書き保存時に別名保存)
というファイルの保存がされる。
"""


import os
import json
import re
import maya.api.OpenMaya as om  # 外部モジュール
import maya.cmds as cmds  # 外部モジュール

# 設定ファイル
FOLDER = "~/Documents/maya/scripts/tm_script/tm_IncrementSave"
CONFIG_FILE = "tm_increment_save.json"
JSON_FOLDER = os.path.expanduser(
    f"{FOLDER}/json_folder"
)

if not os.path.exists(JSON_FOLDER):
    os.makedirs(JSON_FOLDER)

DEFAULT_CONFIG = {
    "enable": True,
    "limit": 20,
    "use_subfolder": True,
    "subfolder_name": "backup"
}


WINDOW_NAME = "IncrementalSaveUI"


# 設定IO
def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)


# インクリメント保存処理
SUFFIX = "_sv"
DIGITS = 4


def get_scene_path():
    return cmds.file(q=True, sn=True)


def split_path(path):
    d = os.path.dirname(path)
    f = os.path.basename(path)
    name, ext = os.path.splitext(f)
    return d, name, ext


def get_backup_dir(base_dir, cfg):
    if not cfg["use_subfolder"]:
        return base_dir

    backup_dir = os.path.join(base_dir, cfg["subfolder_name"])

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    return backup_dir


def find_next_version(directory, base_name, ext):
    pattern = re.compile(
        rf"^{re.escape(base_name)}{SUFFIX}(\d+){re.escape(ext)}$")
    max_num = 0

    for f in os.listdir(directory):
        m = pattern.match(f)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num

    return max_num + 1


def cleanup_old_files(directory, base_name, ext, limit):
    pattern = re.compile(
        rf"^{re.escape(base_name)}{SUFFIX}(\d+){re.escape(ext)}$")

    files = []
    for f in os.listdir(directory):
        m = pattern.match(f)
        if m:
            num = int(m.group(1))
            full = os.path.join(directory, f)
            files.append((num, full))

    files.sort()

    if len(files) <= limit:
        return

    delete_count = len(files) - limit

    for i in range(delete_count):
        try:
            os.remove(files[i][1])
            print("Deleted old backup:", files[i][1])
        except Exception as e:
            print("Delete error:", e)


def incremental_save():
    cfg = load_config()

    if not cfg["enable"]:
        return

    scene_path = get_scene_path()

    if not scene_path:
        return

    base_dir, name, ext = split_path(scene_path)
    backup_dir = get_backup_dir(base_dir, cfg)

    next_num = find_next_version(backup_dir, name, ext)
    num_str = str(next_num).zfill(DIGITS)

    new_path = os.path.join(
        backup_dir,
        f"{name}{SUFFIX}{num_str}{ext}"
    )

    try:
        cmds.file(rename=new_path)
        cmds.file(save=True, type='mayaAscii' if ext ==
                  '.ma' else 'mayaBinary')
        cmds.file(rename=scene_path)

        cleanup_old_files(backup_dir, name, ext, cfg["limit"])

        print("Incremental Save:", new_path)

    except Exception as e:
        print("Incremental Save Error:", e)


# コールバック
def register_callback():
    global CALLBACK_ID

    try:
        cmds.scriptJob(kill=CALLBACK_ID, force=True)
    except:
        pass

    CALLBACK_ID = cmds.scriptJob(
        event=["SceneSaved", incremental_save],
        protected=True
    )

    print("Callback Registered")


# UI
def build_ui():
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    cfg = load_config()

    win = cmds.window(
        WINDOW_NAME,
        title="Incremental Save Tool",
        widthHeight=(300, 200)
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

    # ON/OFF
    enable_cb = cmds.checkBox(
        label="Enable Incremental Save",
        value=cfg["enable"]
    )

    # 保存数
    cmds.text(label="Max Backup Count")
    limit_if = cmds.intField(value=cfg["limit"], minValue=1)

    # フォルダ分離
    sub_cb = cmds.checkBox(
        label="Use Subfolder",
        value=cfg["use_subfolder"]
    )

    cmds.text(label="Subfolder Name")
    sub_name_tf = cmds.textField(text=cfg["subfolder_name"])

    def apply_settings(*args):
        new_cfg = {
            "enable": cmds.checkBox(enable_cb, q=True, v=True),
            "limit": cmds.intField(limit_if, q=True, v=True),
            "use_subfolder": cmds.checkBox(sub_cb, q=True, v=True),
            "subfolder_name": cmds.textField(sub_name_tf, q=True, text=True)
        }

        save_config(new_cfg)
        print("Settings Saved:", new_cfg)

    cmds.button(label="Save Settings", command=apply_settings)
    cmds.separator(height=10)
    cmds.button(
        label="Register Callback",
        command=lambda x: register_callback()
    )

    cmds.showWindow(win)


# 起動
build_ui()
