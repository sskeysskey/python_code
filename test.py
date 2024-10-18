import re
import pyperclip

clipboard_content = pyperclip.paste()

processed_content = clipboard_content

# 删除类似URL格式的字段，匹配 https://*.com、https://*.com/ 和 http://*.com 等格式
url_pattern = r'https?://\S+\.com(?:/\S*)?'
processed_content = re.sub(url_pattern, '', processed_content)

# 将处理后的内容写回剪贴板
pyperclip.copy(processed_content)