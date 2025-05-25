import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QFileDialog,
    QSizePolicy, QDialog, QMessageBox, QSpacerItem,
    QCheckBox, QDialogButtonBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QTextDocument, QTextCursor, QKeySequence

HISTORY_FILE = "/Users/yanzhang/Documents/python_code/Modules/Prompt_history.json"

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
        self.setAcceptRichText(False)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Find):
            self.show_search_dialog()
            event.accept()
        else:
            super().keyPressEvent(event)

    def show_search_dialog(self):
        if not self.search_dialog:
            self.search_dialog = SearchReplaceDialog(self, self.window())

        current_selection = self.textCursor().selectedText()
        if current_selection:
            self.search_dialog.find_input.setText(current_selection)

        self.search_dialog.show()
        self.search_dialog.activateWindow()
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
        self.file_path = None # 存储加载时的文件路径，或用户选择的路径
        self.original_content_on_load = "" # 用于存储从历史记录加载时的内容

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
            self.file_path = file_path # 更新文件路径
            display_path = f"...{os.sep}{os.path.basename(file_path)}"
            if len(file_path) < 50 :
                 display_path = file_path
            self.path_label.setText(display_path)
            self.path_label.setToolTip(file_path)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.content_edit.setPlainText(content)
                # self.original_content_on_load = content # 如果选择新文件，更新这个没有太大意义
            except Exception as e:
                QMessageBox.warning(self, "读取文件错误", f"无法读取文件 {file_path}:\n{e}")
                # self.file_path = None # 保留路径，即使用户选择的文件读取失败
                # self.path_label.setText("读取失败，保留原路径")
                self.content_edit.clear()

    def get_file_info(self):
        # file_path 可能是用户选择的，也可能是从历史记录加载的
        # filename 应该总是从 self.file_path (如果存在) 或 self.path_label (作为备用)派生
        filename = "未知文件"
        current_path_text = self.path_label.text()

        if self.file_path: # 优先使用 self.file_path
            filename = os.path.basename(self.file_path)
        elif current_path_text != "未选择文件" and current_path_text != "路径未记录":
            # 尝试从显示的路径文本中获取文件名（这是一种后备）
            filename = os.path.basename(current_path_text)


        edited_content = self.content_edit.toPlainText()
        # 返回的路径是当前 FileBlockWidget 认为的路径
        return self.file_path if self.file_path else current_path_text, filename, edited_content

    def load_data(self, path_text, content_text):
        """用于从历史记录加载数据到这个文件块"""
        self.file_path = path_text # 存储从历史记录加载的路径
        self.path_label.setText(path_text if path_text else "路径未记录")
        self.path_label.setToolTip(path_text if path_text else "")
        self.content_edit.setPlainText(content_text)
        self.original_content_on_load = content_text # 保存加载时的内容


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
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        self.button_box.button(QDialogButtonBox.Ok).setText("确定")
        self.button_box.accepted.connect(self.accept)
        self.copy_button_instance = QPushButton("复制到剪贴板")
        self.button_box.addButton(self.copy_button_instance, QDialogButtonBox.ActionRole)
        self.copy_button_instance.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.button_box)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "已复制", "内容已复制到剪贴板。")


# --- 历史记录选择对话框 ---
class HistoryDialog(QDialog):
    # pyqtSignal(dict) 表示这个信号会传递一个字典对象
    record_selected = pyqtSignal(dict)

    def __init__(self, history_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录")
        self.setMinimumSize(500, 300)
        self.history_data = history_data # 存储完整的历史数据列表

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        # 倒序显示，最新的在最上面
        for i, record in enumerate(reversed(self.history_data)):
            # 使用时间戳和项目名称作为列表项的文本
            timestamp_str = record.get("id", f"记录 {len(self.history_data) - i}")
            project_name = record.get("project_name", "未命名项目")
            list_item_text = f"{timestamp_str} - {project_name}"
            item = QListWidgetItem(list_item_text)
            # 将原始记录的索引（在倒序前的列表中的索引）存储在item中，方便后续查找
            item.setData(Qt.UserRole, len(self.history_data) - 1 - i)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self.load_selected_record)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("加载选中记录")
        buttons.accepted.connect(self.load_selected_record)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_selected_record(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            # 获取存储在item中的原始记录的索引
            original_index = current_item.data(Qt.UserRole)
            selected_record_data = self.history_data[original_index]
            self.record_selected.emit(selected_record_data) # 发射信号
            self.accept() # 关闭对话框


# --- 主窗口 ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.file_blocks = []
        self.init_ui()
        self._ensure_history_file_exists()

    def _ensure_history_file_exists(self):
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f) # 创建一个空的JSON数组

    def _load_history_from_file(self):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return history if isinstance(history, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_record_to_file(self, record_data):
        history = self._load_history_from_file()
        history.append(record_data)
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "已保存", "当前记录已保存到历史。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存历史记录: {e}")


    def init_ui(self):
        self.setWindowTitle("代码与Prompt整合工具")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QVBoxLayout(self)

        # --- 顶部操作按钮 ---
        top_buttons_layout = QHBoxLayout()
        self.load_history_button = QPushButton("加载历史记录")
        self.load_history_button.clicked.connect(self.show_history_dialog)
        top_buttons_layout.addWidget(self.load_history_button)
        top_buttons_layout.addStretch() # 将按钮推到左边
        main_layout.addLayout(top_buttons_layout)


        # --- 第一部分：项目名称和介绍 ---
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

        # --- 第二部分：文件选择块 ---
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

        for _ in range(3): # 默认创建3个
            self._add_file_block_widget(add_to_list=True)

        # --- 第三部分：Prompt指令和生成按钮 ---
        bottom_section_layout = QVBoxLayout()
        bottom_section_layout.addWidget(QLabel("最终Prompt指令:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("例如：我现在需要制作底部tab里的“资产”页面...")
        self.prompt_input.setMinimumHeight(100)
        self.prompt_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bottom_section_layout.addWidget(self.prompt_input)
        self.generate_button = QPushButton("生成最终文本并保存记录") # 修改按钮文本
        self.generate_button.setFixedHeight(40)
        self.generate_button.clicked.connect(self.generate_and_save_output) # 修改连接的函数
        generate_button_wrapper = QHBoxLayout()
        generate_button_wrapper.addStretch()
        generate_button_wrapper.addWidget(self.generate_button)
        bottom_section_layout.addLayout(generate_button_wrapper)
        main_layout.addLayout(bottom_section_layout)

        main_layout.setStretchFactor(top_buttons_layout, 0)
        main_layout.setStretchFactor(top_section_layout, 0)
        main_layout.setStretchFactor(second_section_wrapper_layout, 1)
        main_layout.setStretchFactor(bottom_section_layout, 0)

    def _clear_all_file_blocks(self):
        """清除所有文件块"""
        while self.file_blocks_layout.count():
            child = self.file_blocks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.file_blocks.clear()

    def _add_file_block_widget(self, add_to_list=True, file_data=None):
        file_block = FileBlockWidget()
        if file_data: # 如果提供了文件数据（从历史记录加载时）
            file_block.load_data(file_data.get("path"), file_data.get("content"))
        self.file_blocks_layout.addWidget(file_block)
        if add_to_list: # 只有在非加载历史记录时才需要添加到 self.file_blocks
            self.file_blocks.append(file_block)
        return file_block # 返回创建的块，方便加载时使用

    def show_history_dialog(self):
        history_data = self._load_history_from_file()
        if not history_data:
            QMessageBox.information(self, "无历史记录", "目前没有已保存的历史记录。")
            return

        dialog = HistoryDialog(history_data, self)
        dialog.record_selected.connect(self.load_record_into_ui) # 连接信号
        dialog.exec_()

    def load_record_into_ui(self, record_data):
        """将选中的历史记录填充到UI"""
        self.project_name_input.setText(record_data.get("project_name", ""))
        self.project_desc_input.setPlainText(record_data.get("project_desc", ""))
        self.prompt_input.setPlainText(record_data.get("final_prompt", ""))

        self._clear_all_file_blocks() # 清除现有文件块

        loaded_files_data = record_data.get("files", [])
        if not loaded_files_data: # 如果历史记录中没有文件块，至少创建一个空的
            if not self.file_blocks: # 确保至少有一个（如果用户之前删光了）
                 self._add_file_block_widget(add_to_list=True)
        else:
            for file_info in loaded_files_data:
                # _add_file_block_widget 现在会处理 file_data
                new_block = self._add_file_block_widget(add_to_list=False, file_data=file_info)
                self.file_blocks.append(new_block) # 手动添加到列表中，因为 add_to_list=False

        # 如果加载后没有任何文件块（例如历史记录中就没有文件），确保至少有N个（比如1个或3个）
        # 这里我们简单地确保至少有一个文件块存在，如果需要固定数量，可以调整逻辑
        if not self.file_blocks:
            for _ in range(max(1, 3 - len(loaded_files_data))): # 保证至少有1个，或者补齐到3个（如果历史文件少于3）
                self._add_file_block_widget(add_to_list=True)
        elif len(self.file_blocks) < 3 and not loaded_files_data: # 如果历史记录没有文件，但界面上块少于3个
             for _ in range(3 - len(self.file_blocks)):
                  self._add_file_block_widget(add_to_list=True)


        QMessageBox.information(self, "加载完成", f"记录 '{record_data.get('id')}' 已加载。")


    def generate_and_save_output(self):
        project_name = self.project_name_input.text().strip()
        project_desc = self.project_desc_input.toPlainText().strip()
        final_prompt = self.prompt_input.toPlainText().strip()

        if not project_desc:
            QMessageBox.warning(self, "信息不完整", "请输入项目介绍。")
            return
        if not project_name:
            QMessageBox.warning(self, "信息不完整", "请输入项目名称。")
            return

        # 1. 收集数据用于保存
        current_record = {
            "id": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # 使用时间戳作为ID
            "project_name": project_name,
            "project_desc": project_desc,
            "files": [],
            "final_prompt": final_prompt
        }

        file_tree_lines = []
        valid_file_infos_for_output = [] # 用于生成输出文本

        # 从 self.file_blocks_layout.itemAt(i).widget() 获取当前界面上的文件块
        # 而不是 self.file_blocks, 因为 self.file_blocks 可能在加载历史后未完全同步
        current_ui_file_blocks = []
        for i in range(self.file_blocks_layout.count()):
            widget = self.file_blocks_layout.itemAt(i).widget()
            if isinstance(widget, FileBlockWidget):
                current_ui_file_blocks.append(widget)

        for block in current_ui_file_blocks: # 遍历当前界面上的所有文件块
            path, filename, content = block.get_file_info()
            # 只有当文件块包含实际内容时才保存和用于输出
            if content is not None and (path != "未选择文件" and path != "路径未记录" or content.strip()):
                current_record["files"].append({
                    "path": path if (path != "未选择文件" and path != "路径未记录") else "", # 保存实际路径或空
                    "filename": filename, # filename是从path派生的
                    "content": content
                })
                # 只有包含有效路径（不只是“未选择文件”）或有内容的文件才加入输出
                if path and path != "未选择文件" and path != "路径未记录":
                     file_tree_lines.append(f"  ├── {filename}")
                     valid_file_infos_for_output.append({"path": path, "content": content})
                elif content.strip() and filename != "未知文件": # 如果没有路径但有内容和文件名
                     file_tree_lines.append(f"  ├── {filename} (无路径, 仅内容)")
                     valid_file_infos_for_output.append({"path": f"{filename} (内容)", "content": content})


        # 2. 保存记录
        self._save_record_to_file(current_record)

        # 3. 生成输出文本 (与之前逻辑类似，但使用 valid_file_infos_for_output)
        final_builder = []
        final_builder.append(project_desc)
        tree_string = ""
        if file_tree_lines:
            tree_string = "\n".join(file_tree_lines)
        final_builder.append(f'\n"{project_name}"' + (f'\n{tree_string}' if tree_string else ""))

        for info in valid_file_infos_for_output:
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