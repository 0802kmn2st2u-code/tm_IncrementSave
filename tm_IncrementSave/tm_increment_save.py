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


import re
import os
import maya.cmds as cmds
import shutil


WINDOW_NAME = "tm_IncrementSave"


# メイン処理
def save_backup():
    """
    現在のMayaシーンを上書き保存後、
    指定バックアップフォルダへ連番保存
    """

    scene_path = cmds.file(q=True, sceneName=True)

    if not scene_path:
        cmds.warning(u"シーンが保存されていません。先に保存してください。")
        return

    cmds.file(save=True)

    scene_name = os.path.basename(scene_path)
    file_name, ext = os.path.splitext(scene_name)

    # UIからバックアップ先取得
    backup_dir = cmds.textField(
        "backupFolderField",
        q=True,
        text=True
    )

    if not backup_dir:
        cmds.warning(u"バックアップフォルダが指定されていません。")
        return

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    pattern = re.compile(
        r"^{}_backup(\d{{3}}){}$".format(
            re.escape(file_name),
            re.escape(ext)
        )
    )

    max_num = 0

    for backup_file in os.listdir(backup_dir):
        match = pattern.match(backup_file)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    next_num = max_num + 1

    backup_name = "{}_backup{:04d}{}".format(
        file_name,
        next_num,
        ext
    )

    backup_path = os.path.join(backup_dir, backup_name)

    shutil.copy2(scene_path, backup_path)

    print(u"元ファイルを保存しました: {}".format(scene_path))
    print(u"バックアップ保存完了: {}".format(backup_path))


def save_clean_version():
    scene_path = cmds.file(q=True, sceneName=True)

    if not scene_path:
        cmds.warning(u"シーンが保存されていません。先に保存してください。")
        return

    cmds.file(save=True)

    scene_dir = os.path.dirname(scene_path)
    scene_name = os.path.basename(scene_path)
    file_name, ext = os.path.splitext(scene_name)

    clean_name = re.sub(
        r'(_v_\d+|_ver_\d+)',
        '_',
        file_name,
        flags=re.IGNORECASE
    )

    clean_scene_path = os.path.join(scene_dir, clean_name + ext)

    file_type = cmds.file(q=True, type=True)
    file_type = file_type[0] if file_type else "mayaBinary"

    cmds.file(rename=clean_scene_path)
    cmds.file(save=True, type=file_type)

    print(u"整理版ファイル保存完了: {}".format(clean_scene_path))

    cmds.file(rename=scene_path)
    refresh_ui_info()


# UI用の処理関数
def get_scene_name():
    scene_path = cmds.file(q=True, sceneName=True)
    if not scene_path:
        return u"未保存シーン"
    return os.path.basename(scene_path)


def get_default_backup_folder():
    scene_path = cmds.file(q=True, sceneName=True)
    if not scene_path:
        return ""

    scene_dir = os.path.dirname(scene_path)
    return os.path.join(scene_dir, "_backup")


def browse_backup_folder(*args):
    folder = cmds.fileDialog2(
        dialogStyle=2,
        fileMode=3,
        caption=u"バックアップフォルダを選択"
    )

    if folder:
        cmds.textField(
            "backupFolderField",
            e=True,
            text=folder[0]
        )


def refresh_ui_info(*args):
    if cmds.textField("sceneNameField", exists=True):
        cmds.textField(
            "sceneNameField",
            e=True,
            text=get_scene_name()
        )

    if cmds.textField("backupFolderField", exists=True):
        current_text = cmds.textField(
            "backupFolderField", q=True, text=True)
        if not current_text:
            cmds.textField(
                "backupFolderField",
                e=True,
                text=get_default_backup_folder()
            )


# UI構築
def ui_run():

    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    cmds.window(
        WINDOW_NAME,
        title=u"TM Backup Tool",
        widthHeight=(700, 200),
        sizeable=True
    )

    main_layout = cmds.columnLayout(adjustableColumn=True)

    cmds.separator(height=10, style='none')

    # 現在シーン名
    cmds.text(label=u"現在のシーン名", align='left')
    cmds.textField(
        "sceneNameField",
        text=get_scene_name(),
        editable=False
    )

    cmds.separator(height=10, style='none')

    # バックアップフォルダ
    cmds.text(label=u"save_backup対象フォルダ", align='left')

    backup_row = cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnAlign=(1, 'left'),
        columnAttach=[(1, 'both', 0), (2, 'both', 5)]
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

    cmds.separator(height=15, style='in')

    # ボタン横並び
    button_row = cmds.rowLayout(
        numberOfColumns=2,
        adjustableColumn=1,
        columnWidth2=(350, 350),
        columnAttach=[(1, 'both', 5), (2, 'both', 5)]
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

    cmds.separator(height=10, style='none')

    cmds.showWindow(WINDOW_NAME)

    refresh_ui_info()


# 実行
# build_backup_ui()
