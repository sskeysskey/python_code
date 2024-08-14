import os

base_path = "/Users/yanzhang/Downloads/"

# 删除以 "concatenated" 开头的 PNG 文件
for file in os.listdir(base_path):
    if file.startswith("concatenated") and file.endswith(".png"):
        os.remove(os.path.join(base_path, file))