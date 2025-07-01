import os
import json
import shutil
import re
from collections import defaultdict

# --- 配置区 ---
# 请根据您的实际情况修改下面的路径
# 注意：Windows 系统下路径可能需要写成 'C:\\Users\\yanzhang\\Documents\\News\\done' 的形式
JSON_DIR = '/Users/yanzhang/Documents/News/done'
IMAGE_BACKUP_DIR = '/Users/yanzhang/Downloads/backup'

# --- 主功能函数 ---

def find_latest_sources(directory, prefix, suffix, count):
    """
    在指定目录中查找最新的N个源文件或目录。

    Args:
        directory (str): 要搜索的目录路径。
        prefix (str): 文件或目录名的前缀 (例如 'onews_' 或 'news_images_')。
        suffix (str): 文件或目录名的后缀 (例如 '.json' 或 '')。
        count (int): 需要查找的数量。

    Returns:
        list: 按日期从新到旧排序的源的完整路径列表。如果找不到足够数量的源，则返回的列表长度可能小于count。
    """
    # 正则表达式用于匹配 '前缀' + '6位日期' + '后缀' 格式
    # 例如: onews_250630.json
    pattern = re.compile(f"^{re.escape(prefix)}(\\d{{6}}){re.escape(suffix)}$")
    
    sources = []
    try:
        for name in os.listdir(directory):
            match = pattern.match(name)
            if match:
                date_str = match.group(1) # 提取日期部分，例如 '250630'
                full_path = os.path.join(directory, name)
                sources.append((date_str, full_path))
    except FileNotFoundError:
        print(f"错误：找不到目录 '{directory}'。请检查路径是否正确。")
        return []

    # 按日期字符串降序排序（'250630' > '250629'）
    sources.sort(key=lambda x: x[0], reverse=True)
    
    # 返回前 count 个源的完整路径
    return [path for date_str, path in sources[:count]]

def merge_json_files(source_files, target_file):
    """
    合并多个JSON文件的内容并写入目标文件。

    Args:
        source_files (list): 源JSON文件的路径列表。
        target_file (str): 合并后要写入的目标JSON文件路径。
    """
    # 使用 defaultdict 可以简化代码，当一个键第一次被访问时，会自动创建一个空列表
    merged_data = defaultdict(list)
    
    # 从最旧的文件开始合并，以保持一定的逻辑顺序（虽然对于列表追加来说顺序不影响最终结果）
    for file_path in reversed(source_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category, articles in data.items():
                    # 将当前文件的文章列表追加到合并后数据的对应分类下
                    merged_data[category].extend(articles)
        except json.JSONDecodeError:
            print(f"警告：文件 '{file_path}' 不是有效的JSON格式，已跳过。")
        except FileNotFoundError:
            print(f"警告：找不到文件 '{file_path}'，已跳过。")

    # 将合并后的数据写入目标文件，覆盖原有内容
    try:
        with open(target_file, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 保证中文字符能正确写入
            # indent=4 使JSON文件格式化，易于阅读
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
        print(f"JSON文件合并成功！结果已写入: {target_file}")
    except IOError as e:
        print(f"错误：无法写入目标文件 '{target_file}'。原因: {e}")


def merge_image_dirs(source_dirs, target_dir):
    """
    合并多个图片目录的内容到目标目录。

    Args:
        source_dirs (list): 源图片目录的路径列表。
        target_dir (str): 合并后要写入的目标目录路径。
    """
    # 1. 确保目标目录存在，如果不存在则创建
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"开始合并图片到目标目录: {target_dir}")
    copied_count = 0
    
    # 2. 遍历所有源目录
    for dir_path in reversed(source_dirs): # 从最旧的开始，让新的覆盖旧的
        try:
            # 3. 遍历源目录中的所有文件
            for filename in os.listdir(dir_path):
                source_file = os.path.join(dir_path, filename)
                target_file = os.path.join(target_dir, filename)
                
                # 确保我们只复制文件，不复制子目录（如果有的话）
                if os.path.isfile(source_file):
                    # 4. 复制文件到目标目录，如果目标文件已存在，则会覆盖它
                    shutil.copy2(source_file, target_file)
                    copied_count += 1
        except FileNotFoundError:
            print(f"警告：找不到源目录 '{dir_path}'，已跳过。")

    print(f"图片目录合并完成！共处理了 {len(source_dirs)} 个源目录。")


def main():
    """
    主函数，处理用户交互和调用合并功能。
    """
    print("--- 新闻与图片合并工具 ---")
    print("1: 退出程序")
    print("2: 合并最新的 2 份新闻和图片")
    print("3: 合并最新的 3 份新闻和图片")
    
    choice = input("请输入您的选择 (1, 2, or 3): ")
    
    if choice == '1':
        print("已选择退出，程序结束。")
        return
        
    elif choice in ['2', '3']:
        num_to_merge = int(choice)
        print(f"\n您已选择合并最新的 {num_to_merge} 份内容。")
        
        # --- 步骤 1: 处理 JSON 文件 ---
        print("\n--- 正在处理JSON文件... ---")
        json_sources = find_latest_sources(JSON_DIR, 'onews_', '.json', num_to_merge)
        
        if len(json_sources) < num_to_merge:
            print(f"警告：只找到了 {len(json_sources)} 个带时间戳的JSON文件，少于您希望合并的 {num_to_merge} 个。")
        
        if not json_sources:
            print("错误：在目录下未找到任何匹配的 'onews_YYMMDD.json' 文件。")
        else:
            print(f"找到以下 {len(json_sources)} 个最新的JSON文件进行合并:")
            for src in json_sources:
                print(f"  - {os.path.basename(src)}")
            target_json_file = os.path.join(JSON_DIR, 'onews.json')
            merge_json_files(json_sources, target_json_file)

        # --- 步骤 2: 处理图片目录 ---
        print("\n--- 正在处理图片目录... ---")
        # 图片目录没有后缀，所以 suffix 参数传空字符串 ''
        image_sources = find_latest_sources(IMAGE_BACKUP_DIR, 'news_images_', '', num_to_merge)

        if len(image_sources) < num_to_merge:
            print(f"警告：只找到了 {len(image_sources)} 个带时间戳的图片目录，少于您希望合并的 {num_to_merge} 个。")

        if not image_sources:
            print("错误：在目录下未找到任何匹配的 'news_images_YYMMDD' 目录。")
        else:
            print(f"找到以下 {len(image_sources)} 个最新的图片目录进行合并:")
            for src in image_sources:
                print(f"  - {os.path.basename(src)}")
            target_image_dir = os.path.join(IMAGE_BACKUP_DIR, 'news_images')
            merge_image_dirs(image_sources, target_image_dir)
            
        print("\n所有操作已完成。")

    else:
        print("无效输入。请输入 1, 2, 或 3。")

# --- 程序入口 ---
if __name__ == "__main__":
    main()