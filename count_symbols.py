import sys

def count_non_alphanumeric_characters(file_path):
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 计算不是英文字母（a-z，A-Z）、数字（0-9）或空格的字符数量
        count = sum(not ch.isalnum() and not ch.isspace() for ch in content)
        
        return count
    except FileNotFoundError:
        print("File not found.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/clipboardContent.txt"
    non_alphanumeric_count = count_non_alphanumeric_characters(file_path)
    print(non_alphanumeric_count)
