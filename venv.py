import os
import subprocess

def check_virtualenv(path):
    if os.path.exists(path) and os.path.isdir(path):
        if os.path.exists(os.path.join(path, 'bin', 'activate')):
            print(f"{path} 是一个Python虚拟环境。")
            subprocess.run(["source", os.path.join(path, "bin", "activate")], shell=True)
            subprocess.run(["pip", "list"])
        else:
            print(f"{path} 不是一个Python虚拟环境。")
    else:
        print(f"路径 {path} 不存在。")

check_virtualenv("/Users/yanzhang/my_venv")
check_virtualenv("/Users/yanzhang/venv")
