import sys
import argparse
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard, QFont, QTextCursor, QTextBlockFormat
from PyQt5.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout, QLabel

def on_enter_key():
    text = text_edit.toPlainText()
    # label.setText(f"输入的文本是：{text}")

    # 将输入框内容复制到剪贴板
    clipboard = QApplication.clipboard()
    clipboard.setText(text)

    window.close()

def on_esc_key():
    # 清空剪贴板
    clipboard = QApplication.clipboard()
    clipboard.clear()
    window.close()

# 设置 QTextEdit 的段落格式以调整行距
def set_line_height(text_edit, height_factor):
    # 创建一个文本光标对象，用于编辑文本格式
    cursor = QTextCursor(text_edit.document())
    # 移动光标到文档开始
    cursor.movePosition(QTextCursor.Start)
    # 创建一个文本块格式对象
    block_format = QTextBlockFormat()
    # 设置行距类型为固定高度
    block_format.setLineHeight(height_factor, QTextBlockFormat.FixedHeight)
    # 遍历文档中的所有段落，并应用新的行距
    while True:
        cursor.setBlockFormat(block_format)
        if cursor.atEnd():
            break
        cursor.movePosition(QTextCursor.NextBlock)

class MyWindow(QWidget):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            on_enter_key()
        elif event.key() == Qt.Key_Escape:
            on_esc_key()

class MyTextEdit(QTextEdit):
    def keyPressEvent(self, event):
        if event.modifiers() & Qt.AltModifier and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # 如果按下了option（Alt）+ 回车，则在文本框中插入换行
            self.insertPlainText('\n')
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # 如果只按下了回车键，不包括option（Alt），则调用on_enter_key函数
            on_enter_key()
        else:
            # 其他键按照默认行为处理
            super().keyPressEvent(event)
            
    def insertFromMimeData(self, source):
        # 只获取纯文本内容
        text = source.text()
        # 调用父类方法插入纯文本
        super().insertPlainText(text)

# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument("--select_all", help="选择是否全选文本", action="store_true")
args = parser.parse_args()

# 应用初始化
app = QApplication(sys.argv)

# 主窗口window和布局layout
window = MyWindow()
window.setWindowTitle('请输入要查询的内容')
layout = QVBoxLayout()

# 设置输入框字体大小
input_font = QFont()
input_font.setPointSize(22)  # 设置字体大小
# input_font.setBold(True)  # 设置字体大小

# 标签字体设置
# label_font = QFont()
# label_font.setPointSize(20)  # 设定标签字体大小
# label_font.setBold(True)  # 设定标签字体加粗

# 创建标签并应用字体设置
# label = QLabel('请输入要查询的内容：')
# label.setFont(label_font)  # 应用字体设置
# layout.addWidget(label)

# 设置输入框QTextEdit的背景色为黑色，设置QTextEdit的光标颜色为白色，并调整宽度为2
text_edit = MyTextEdit()
set_line_height(text_edit, 35)
text_edit.setStyleSheet("QTextEdit { color: gold; background-color: black; caret-color: white; }")
text_edit.setCursorWidth(2)
text_edit.setFont(input_font)
text_edit.setMinimumHeight(300)
layout.addWidget(text_edit)

# 设置窗口大小
original_width = 450  # 原始宽度
original_height = 500  # 原始高度
window.resize(original_width * 2, original_height)

# 获取屏幕尺寸
screen = app.primaryScreen()
rect = screen.availableGeometry()

# 屏幕中心点坐标
center_x = rect.width() / 2
center_y = rect.height() / 2

# 窗口尺寸
window_width = original_width * 2
window_height = original_height

# 计算新的窗口位置坐标
new_x = center_x - window_width / 2
new_y = center_y - window_height / 2  # 往上偏移100像素

# 设置窗口新位置
window.move(int(new_x), int(new_y))

# 粘贴剪贴板内容
text_edit.paste()

# 根据参数决定是否全选文本
if args.select_all:
    text_edit.selectAll()

# 将布局应用到主窗口并显示
window.setLayout(layout)
window.show()

# 启动事件循环
sys.exit(app.exec_())
