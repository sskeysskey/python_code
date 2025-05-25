import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QFileDialog,
    QSizePolicy, QDialog, QMessageBox, QCheckBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextDocument, QTextCursor, QKeySequence

# --- 自定义查找/替换对话框 ---
class SearchReplaceDialog(QDialog):
    def __init__(self, target_text_edit, parent=None):
        super().__init__(parent)
        self.target_text_edit = target_text_edit
        self.setWindowTitle("查找/替换")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # 查找
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("查找:"))
        self.find_input = QLineEdit()
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)

        # 替换
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("替换:"))
        self.replace_input = QLineEdit()
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)

        # 选项
        options_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("区分大小写")
        options_layout.addWidget(self.case_sensitive_cb)
        self.whole_words_cb = QCheckBox("全字匹配") # 暂未实现逻辑，可后续添加
        options_layout.addWidget(self.whole_words_cb)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        # 按钮
        self.find_next_button = QPushButton("查找下一个")
        self.replace_button = QPushButton("替换")
        self.replace_all_button = QPushButton("全部替换")
        self.close_button = QPushButton("关闭")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.find_next_button)
        button_layout.addWidget(self.replace_button)
        button_layout.addWidget(self.replace_all_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        # 连接信号
        self.find_next_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_current)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.close_button.clicked.connect(self.close)
        self.find_input.textChanged.connect(self._update_button_states)
        
        self._update_button_states()


    def _update_button_states(self):
        has_find_text = bool(self.find_input.text())
        self.find_next_button.setEnabled(has_find_text)
        self.replace_button.setEnabled(has_find_text and self.target_text_edit.textCursor().hasSelection())
        self.replace_all_button.setEnabled(has_find_text)

    def set_search_focus(self):
        self.find_input.setFocus()
        self.find_input.selectAll()

    def _get_find_flags(self):
        flags = QTextDocument.FindFlags()
        if self.case_sensitive_cb.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        # if self.whole_words_cb.isChecked(): # 实现全字匹配需要更复杂的逻辑或正则表达式
        #     flags |= QTextDocument.FindWholeWords
        return flags

    def find_next(self, search_backward=False):
        if not self.target_text_edit:
            return
        query = self.find_input.text()
        if not query:
            return

        flags = self._get_find_flags()
        if search_backward:
            flags |= QTextDocument.FindBackward

        found = self.target_text_edit.find(query, flags)
        if not found:
            # 尝试从头/尾开始搜索（实现环绕搜索）
            cursor = self.target_text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start if not search_backward else QTextCursor.End)
            self.target_text_edit.setTextCursor(cursor)
            found = self.target_text_edit.find(query, flags)
        
        self._update_button_states()
        return found

    def replace_current(self):
        if not self.target_text_edit or not self.target_text_edit.textCursor().hasSelection():
            return
        replace_text = self.replace_input.text()
        self.target_text_edit.textCursor().insertText(replace_text)
        self.find_next() # 查找下一个匹配项
        self._update_button_states()

    def replace_all(self):
        if not self.target_text_edit:
            return
        query = self.find_input.text()
        replace_text = self.replace_input.text()
        if not query:
            return

        flags = self._get_find_flags()
        count = 0
        # 先将光标移到文档开头
        cursor = self.target_text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.target_text_edit.setTextCursor(cursor)

        while self.target_text_edit.find(query, flags):
            self.target_text_edit.textCursor().insertText(replace_text)
            count += 1
        
        if count > 0:
            QMessageBox.information(self, "全部替换", f"已替换 {count} 处。")
        else:
            QMessageBox.information(self, "全部替换", f"未找到 '{query}'。")
        self._update_button_states()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

# --- 自定义文本编辑器，支持查找快捷键 ---
class FileContentTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_dialog = None
        self.setAcceptRichText(False) # 通常代码文件是纯文本

    def keyPressEvent(self, event):
        # Command+F (macOS) or Ctrl+F (Windows/Linux)
        if event.matches(QKeySequence.Find):
            self.show_search_dialog()
            event.accept() # 阻止事件进一步传播
        else:
            super().keyPressEvent(event) # 其他按键正常处理

    def show_search_dialog(self):
        if not self.search_dialog:
            self.search_dialog = SearchReplaceDialog(self, self.window())

        current_selection = self.textCursor().selectedText()
        if current_selection:
            self.search_dialog.find_input.setText(current_selection)
        
        self.search_dialog.show()
        self.search_dialog.activateWindow() # 确保对话框在最前
        self.search_dialog.set_search_focus()

    def focusInEvent(self, event):
        if self.search_dialog:
            self.search_dialog._update_button_states()
        super().focusInEvent(event)

    def cursorPositionChanged(self):
        if self.search_dialog:
            self.search_dialog._update_button_states()
        super().cursorPositionChanged()


# --- 单个文件块控件 ---
class FileBlockWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.original_content = "" 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5) 

        path_layout = QHBoxLayout()
        self.path_button = QPushButton("选择文件")
        self.path_button.clicked.connect(self.select_file)
        self.path_label = QLabel("未选择文件")
        self.path_label.setWordWrap(True) 
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.path_label.setToolTip("文件路径") 

        path_layout.addWidget(self.path_button)
        path_layout.addWidget(self.path_label, 1) 
        layout.addLayout(path_layout)

        self.content_edit = FileContentTextEdit() 
        self.content_edit.setPlaceholderText("文件内容将在此显示和编辑...")
        self.content_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.content_edit)

        self.setMinimumWidth(200) 
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)


    def select_file(self):
        supported_formats = "*.swift *.py *.html *.css *.js *.scpt *.txt *.json *.csv"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "", 
            f"支持的文件 ({supported_formats});;所有文件 (*)"
        )
        if file_path:
            self.file_path = file_path
            display_path = f"...{os.sep}{os.path.basename(file_path)}"
            if len(file_path) < 50 : 
                 display_path = file_path
            self.path_label.setText(display_path)
            self.path_label.setToolTip(file_path) 

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.original_content = f.read()
                self.content_edit.setPlainText(self.original_content) 
            except Exception as e:
                QMessageBox.warning(self, "读取文件错误", f"无法读取文件 {file_path}:\n{e}")
                self.file_path = None
                self.path_label.setText("未选择文件")
                self.path_label.setToolTip("")
                self.content_edit.clear()

    def get_file_info(self):
        if not self.file_path:
            return None, None, None
        filename = os.path.basename(self.file_path)
        edited_content = self.content_edit.toPlainText()
        return self.file_path, filename, edited_content

# --- 输出对话框 ---
class OutputDialog(QDialog):
    def __init__(self, text_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("生成结果")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text_content)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        # --- FIX START ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok) # Standard OK button
        self.button_box.button(QDialogButtonBox.Ok).setText("确定")
        self.button_box.accepted.connect(self.accept) # OK button will trigger this

        # Create and add the "Copy to Clipboard" button
        self.copy_button_instance = QPushButton("复制到剪贴板")
        self.button_box.addButton(self.copy_button_instance, QDialogButtonBox.ActionRole) # Add as an action button
        self.copy_button_instance.clicked.connect(self.copy_to_clipboard) # Connect its click signal

        layout.addWidget(self.button_box)
        # --- FIX END ---

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "已复制", "内容已复制到剪贴板。")


# --- 主窗口 ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.file_blocks = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("代码与Prompt整合工具")
        self.setGeometry(100, 100, 1200, 800) 

        main_layout = QVBoxLayout(self)

        top_section_layout = QHBoxLayout()

        project_name_group = QVBoxLayout()
        project_name_group.addWidget(QLabel("项目名称:"))
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("例如：Finance")
        project_name_group.addWidget(self.project_name_input)
        top_section_layout.addLayout(project_name_group, 1) 

        project_desc_group = QVBoxLayout()
        project_desc_group.addWidget(QLabel("项目介绍:"))
        self.project_desc_input = QTextEdit()
        self.project_desc_input.setPlaceholderText("例如：我有一个Xcode开发的iPhone手机应用程序...")
        self.project_desc_input.setFixedHeight(80) 
        project_desc_group.addWidget(self.project_desc_input)
        top_section_layout.addLayout(project_desc_group, 2) 

        main_layout.addLayout(top_section_layout)

        self.file_blocks_container_widget = QWidget() 
        self.file_blocks_layout = QHBoxLayout(self.file_blocks_container_widget)
        self.file_blocks_layout.setContentsMargins(0,0,0,0) 
        self.file_blocks_layout.setSpacing(5) 

        second_section_wrapper_layout = QHBoxLayout()
        second_section_wrapper_layout.addWidget(self.file_blocks_container_widget, 1) 

        self.add_file_block_button = QPushButton("+")
        self.add_file_block_button.setToolTip("增加文件引入块")
        self.add_file_block_button.setFixedSize(30, 30) 
        self.add_file_block_button.clicked.connect(self._add_file_block_widget)
        
        add_button_layout = QVBoxLayout()
        add_button_layout.addWidget(self.add_file_block_button)
        add_button_layout.addStretch() 
        second_section_wrapper_layout.addLayout(add_button_layout)

        main_layout.addLayout(second_section_wrapper_layout)

        for _ in range(3):
            self._add_file_block_widget(add_to_list=True)

        bottom_section_layout = QVBoxLayout()
        bottom_section_layout.addWidget(QLabel("最终Prompt指令:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("例如：我现在需要制作底部tab里的“资产”页面...")
        self.prompt_input.setMinimumHeight(100) 
        self.prompt_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bottom_section_layout.addWidget(self.prompt_input)

        self.generate_button = QPushButton("生成最终文本")
        self.generate_button.setFixedHeight(40)
        self.generate_button.clicked.connect(self.generate_output_text)
        
        generate_button_wrapper = QHBoxLayout()
        generate_button_wrapper.addStretch()
        generate_button_wrapper.addWidget(self.generate_button)
        bottom_section_layout.addLayout(generate_button_wrapper)

        main_layout.addLayout(bottom_section_layout)

        main_layout.setStretchFactor(top_section_layout, 0) 
        main_layout.setStretchFactor(second_section_wrapper_layout, 1) 
        main_layout.setStretchFactor(bottom_section_layout, 0) 


    def _add_file_block_widget(self, add_to_list=True): 
        file_block = FileBlockWidget()
        self.file_blocks_layout.addWidget(file_block) 
        if add_to_list:
            self.file_blocks.append(file_block)
        
    def generate_output_text(self):
        project_name = self.project_name_input.text().strip()
        project_desc = self.project_desc_input.toPlainText().strip()
        final_prompt = self.prompt_input.toPlainText().strip()

        if not project_desc:
            QMessageBox.warning(self, "信息不完整", "请输入项目介绍。")
            return
        if not project_name:
            QMessageBox.warning(self, "信息不完整", "请输入项目名称。")
            return

        output_parts = []
        file_tree_lines = []
        valid_file_infos = []

        for block in self.file_blocks: 
            path, filename, content = block.get_file_info()
            if path and filename and content is not None: 
                file_tree_lines.append(f"  ├── {filename}")
                valid_file_infos.append({"path": path, "content": content})
        
        final_builder = []
        final_builder.append(project_desc)
        
        tree_string = ""
        if file_tree_lines:
            tree_string = "\n".join(file_tree_lines)
        
        final_builder.append(f'\n"{project_name}"' + (f'\n{tree_string}' if tree_string else ""))

        for info in valid_file_infos:
            final_builder.append(f'\n\n{info["path"]}\n“{info["content"]}”；')
        
        if final_prompt:
            final_builder.append(f'\n\n{final_prompt}')

        final_text = "".join(final_builder)

        output_dialog = OutputDialog(final_text, self)
        output_dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())