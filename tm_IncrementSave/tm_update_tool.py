# -*- coding: utf-8 -*-

"""
20260212_v004
© Ryo Toyama
tm_update_tool.py
"""

import os
import maya.cmds as cmds
import maya.mel as mel


class tmUpdateTool():

    @staticmethod
    def run():

        # ベースディレクトリ
        user_docs_dir = os.path.expanduser("~/Documents")

        base_dir = os.path.join(
            user_docs_dir,
            "maya",
            "scripts",
            "tm_script"
        ).replace("\\", "/")

        icons_dir = os.path.join(
            base_dir,
            "00_icons"
        ).replace("\\", "/")

        update_script_path = os.path.join(
            base_dir,
            "tm_UpdateTool",
            "tm_run.py"
        ).replace("\\", "/")

        # Updateアイコン設定
        update_icon_path = os.path.join(
            icons_dir,
            "tm_update_tool.png"
        ).replace("\\", "/")

        if not os.path.exists(update_icon_path):
            update_icon_path = "refresh.png"

        # ベース確認
        if not os.path.exists(base_dir):
            cmds.error(
                f"tm_script Not found:\n{base_dir}"
            )
            return

        # シェルフ作成
        shelf_name = "tm_script"
        gShelfTopLevel = mel.eval(
            "$tmp = $gShelfTopLevel"
        )

        # 既存削除
        if cmds.shelfLayout(shelf_name, exists=True):
            cmds.deleteUI(shelf_name)

        cmds.shelfLayout(
            shelf_name,
            parent=gShelfTopLevel
        )

        cmds.tabLayout(
            gShelfTopLevel,
            edit=True,
            selectTab=shelf_name
        )

        # -------------------------------------------------
        # 共通：安全な tm_run.py 丸ごと実行コマンド生成
        # -------------------------------------------------
        def build_safe_exec_command(tm_run_path):

            command_str = f'''
import maya.cmds as cmds
import traceback

def _tm_safe_exec():
    try:
        tm_file = r"{tm_run_path}"

        with open(tm_file, "r", encoding="utf-8") as f:
            code = f.read()

        exec_globals = {{
            "__file__": tm_file,
            "__name__": "__main__",
        }}

        exec(compile(code, tm_file, "exec"), exec_globals)

    except Exception:
        print(traceback.format_exc())

cmds.evalDeferred(_tm_safe_exec)
'''
            return command_str

        # -------------------------------------------------
        # Updateボタン（先頭）
        # -------------------------------------------------
        if os.path.exists(update_script_path):

            update_command = build_safe_exec_command(
                update_script_path
            )

            cmds.shelfButton(
                parent=shelf_name,
                label="Update",
                annotation="Rebuild tm_script shelf",
                command=update_command,
                sourceType="python",
                image1=update_icon_path
            )

        # -------------------------------------------------
        # ツールフォルダ検索
        # -------------------------------------------------
        folder_list = sorted(os.listdir(base_dir))

        for folder_name in folder_list:

            # tm_フォルダのみ対象
            if not folder_name.startswith("tm_"):
                continue

            # Updateツール除外（先頭登録済み）
            if folder_name == "tm_UpdateTool":
                continue

            folder_path = os.path.join(
                base_dir,
                folder_name
            ).replace("\\", "/")

            if not os.path.isdir(folder_path):
                continue

            tm_run_path = os.path.join(
                folder_path,
                "tm_run.py"
            ).replace("\\", "/")

            if not os.path.exists(tm_run_path):
                continue

            # -------------------------------------------------
            # アイコン検出
            # -------------------------------------------------
            icon_path = os.path.join(
                icons_dir,
                f"{folder_name}.png"
            ).replace("\\", "/")

            default_icon = os.path.join(
                icons_dir,
                "icon_notfound.png"
            ).replace("\\", "/")

            if os.path.exists(icon_path):
                final_icon = icon_path
            elif os.path.exists(default_icon):
                final_icon = default_icon
            else:
                final_icon = "commandButton.png"

            # -------------------------------------------------
            # 安全execコマンド生成
            # -------------------------------------------------
            command_str = build_safe_exec_command(
                tm_run_path
            )

            # -------------------------------------------------
            # シェルフボタン作成
            # -------------------------------------------------
            cmds.shelfButton(
                parent=shelf_name,
                label=folder_name.replace("tm_", ""),
                annotation=f"{folder_name} Tool",
                command=command_str,
                sourceType="python",
                image1=final_icon
            )

            print(f"Registered: {folder_name}")

        print("tm_script shelf created successfully.")
