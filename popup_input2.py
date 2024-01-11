from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard, QFont
import sys

def on_enter_key():
    text = line_edit.text()
    label.setText(f"输入的文本是：{text}")

    # 将输入框内容复制到剪贴板
    clipboard = QApplication.clipboard()
    clipboard.setText(text)

    window.close()

def on_esc_key():
    # 清空剪贴板
    clipboard = QApplication.clipboard()
    clipboard.clear()
    window.close()

class MyWindow(QWidget):
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            on_enter_key()
        elif event.key() == Qt.Key_Escape:
            on_esc_key()

app = QApplication(sys.argv)

window = MyWindow()
window.setWindowTitle('自定义输入框')

layout = QVBoxLayout()

label = QLabel('请输入要查询的内容：')
layout.addWidget(label)

line_edit = QLineEdit()

# 设置输入框字体大小
font = QFont()
font.setPointSize(22)  # 设置字体大小
line_edit.setFont(font)

line_edit.setMinimumHeight(35)  # 设置最小高度
line_edit.setMaximumHeight(50)  # 设置最大高度
layout.addWidget(line_edit)

# 设置窗口大小
original_width = 250  # 原始宽度
original_height = 50  # 原始高度
window.resize(original_width * 2, original_height)

# 设置窗口位置
window.move(500, 250)

# 粘贴剪贴板内容
line_edit.paste()

# 全选文本
#line_edit.selectAll()

window.setLayout(layout)

window.show()
sys.exit(app.exec_())
