from tm_script.tm_UpdateTool import tm_update_tool
import importlib

if __name__ == "__main__":
    try:
        importlib.reload(tm_update_tool)
        tm_update_tool.tmUpdateTool.run()
    except:
        print("更新できなかったよ。")
