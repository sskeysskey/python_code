import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QLabel, QFileDialog,
    QSizePolicy, QDialog, QMessageBox,
    QCheckBox, QDialogButtonBox, QListWidget, QListWidgetItem,
    QSplitter, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer 
from PyQt5.QtGui import QTextDocument, QTextCursor, QKeySequence

HISTORY_FILE = "/Users/yanzhang/Documents/python_code/Modules/Prompt_history.json" # 请确保这个路径对您的系统是正确的
DEFAULT_FILE_SELECTION_PATH = "/Users/yanzhang/Documents" # 定义默认文件选择路径
# 记录上次打开的目录，初始值为默认路径
LAST_FILE_SELECTION_PATH = DEFAULT_FILE_SELECTION_PATH

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
        self.whole_words_cb = QCheckBox("全字匹配")
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
        return flags

    def find_next(self, search_backward=False):
        if not self.target_text_edit: return
        query = self.find_input.text()
        if not query: return

        flags = self._get_find_flags()
        if search_backward: flags |= QTextDocument.FindBackward

        found = self.target_text_edit.find(query, flags)
        if not found:
            cursor = self.target_text_edit.textCursor()
            cursor.movePosition(QTextCursor.Start if not search_backward else QTextCursor.End)
            self.target_text_edit.setTextCursor(cursor)
            found = self.target_text_edit.find(query, flags)
        self._update_button_states()
        return found

    def replace_current(self):
        if not self.target_text_edit or not self.target_text_edit.textCursor().hasSelection(): return
        self.target_text_edit.textCursor().insertText(self.replace_input.text())
        self.find_next()
        self._update_button_states()

    def replace_all(self):
        if not self.target_text_edit: return
        query, replace_text = self.find_input.text(), self.replace_input.text()
        if not query: return

        flags = self._get_find_flags()
        count = 0
        cursor = self.target_text_edit.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.target_text_edit.setTextCursor(cursor)

        while self.target_text_edit.find(query, flags):
            self.target_text_edit.textCursor().insertText(replace_text)
            count += 1
        QMessageBox.information(self, "全部替换", f"已替换 {count} 处。" if count > 0 else f"未找到 '{query}'。")
        self._update_button_states()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.close()
        else: super().keyPressEvent(event)

# --- 自定义文本编辑器 ---
class FileContentTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_dialog = None
        self.setAcceptRichText(False) # 默认不接受富文本，只处理纯文本

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
        if self.search_dialog: self.search_dialog._update_button_states()
        super().focusInEvent(event)

    def cursorPositionChanged(self):
        if self.search_dialog: self.search_dialog._update_button_states()
        super().cursorPositionChanged()

# --- 单个文件块控件 ---
class FileBlockWidget(QWidget):
    delete_requested = pyqtSignal(QWidget) # 信号，参数为自身

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.original_content_on_load = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        path_layout = QHBoxLayout()
        self.path_button = QPushButton("选择文件")
        self.path_button.clicked.connect(self.select_file)
        self.path_label = QLabel("未选择文件")
        self.path_label.setWordWrap(True)
        self.path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.path_label.setToolTip("文件路径")

        self.delete_button = QPushButton("X")
        self.delete_button.setFixedSize(22, 22) # 调整大小以适应
        self.delete_button.setToolTip("删除此文件块")
        self.delete_button.clicked.connect(self._request_delete_self)

        path_layout.addWidget(self.path_button)
        path_layout.addWidget(self.path_label, 1)
        path_layout.addWidget(self.delete_button) # 添加删除按钮到布局
        layout.addLayout(path_layout)

        self.content_edit = FileContentTextEdit()
        self.content_edit.setPlaceholderText("文件内容将在此显示和编辑...")
        self.content_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.content_edit)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

    def _request_delete_self(self):
        self.delete_requested.emit(self) # 发出删除请求信号

    def select_file(self):
        global LAST_FILE_SELECTION_PATH

        # 以上次打开的目录作为起始路径
        start_path = LAST_FILE_SELECTION_PATH
        if not os.path.exists(start_path):
            start_path = os.path.expanduser("~")

        formats = "*.swift *.py *.html *.css *.js *.scpt *.txt *.json *.csv *.db"
        f_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            start_path,
            f"支持的文件 ({formats});;所有文件 (*)"
        )
        if not f_path:
            return

        # 选中文件后，更新全局的“上次打开目录”
        LAST_FILE_SELECTION_PATH = os.path.dirname(f_path)
        self.file_path = f_path
        display_path = f"...{os.sep}{os.path.basename(f_path)}" \
            if len(f_path) >= 50 else f_path
        self.path_label.setText(display_path)
        self.path_label.setToolTip(f_path)

        _, file_extension = os.path.splitext(f_path) # 获取文件扩展名

        # 检查文件扩展名是否为 .db
        if file_extension.lower() in (".db", ".scpt"):
            self.content_edit.clear() # 清空内容区域
            # 设置占位符文本，提示用户这是一个.db文件，内容未加载
            # 设置占位符文本，提示用户这是一个二进制文件，内容未加载
            self.content_edit.setPlaceholderText(
                f"这是一个 {file_extension} 二进制文件，内容未加载。\n"
                "您可以在此手动输入或编辑与该数据库文件相关的信息或说明。"
            )
            self.original_content_on_load = "" # 对于.db或.scpt文件，我们视其加载内容为空
        else:
            # 对于非.db文件，按原逻辑处理
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.content_edit.setPlainText(content)
                    self.original_content_on_load = content
            except Exception as e:
                QMessageBox.warning(self, "读取文件错误", f"无法读取文件 {f_path}:\n{e}")
                self.content_edit.clear()
                self.original_content_on_load = ""

    def get_file_info(self):
        filename = "未知文件"
        current_path_text = self.path_label.text()
        if self.file_path:
            filename = os.path.basename(self.file_path)
        elif current_path_text not in ["未选择文件", "路径未记录"]:
            filename = os.path.basename(current_path_text)
        content = self.content_edit.toPlainText()
        actual_path = self.file_path if self.file_path else \
                      (current_path_text if current_path_text not in ["未选择文件", "路径未记录"] else "")
        return actual_path, filename, content

    def load_data(self, path_text, content_text):
        self.file_path = path_text
        self.path_label.setText(path_text if path_text else "路径未记录")
        self.path_label.setToolTip(path_text if path_text else "")
        self.content_edit.setPlainText(content_text)
        self.original_content_on_load = content_text

# --- 输出对话框 ---
class OutputDialog(QDialog):
    def __init__(self, text_content, parent=None):
        super().__init__(parent)
        self.original_title = "生成结果"  # 保存原始标题
        self.setWindowTitle(self.original_title)
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        self.text_edit = QTextEdit(text_content)
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

        self.button_box = QDialogButtonBox() # 先创建一个空的 QDialogButtonBox

        # 添加 "确定" 按钮
        self.ok_button = self.button_box.addButton(QDialogButtonBox.Ok) # 添加标准 OK 按钮
        self.ok_button.setText("确定") # 设置文本
        self.button_box.accepted.connect(self.accept) # 连接 accepted 信号 (当OK按钮被点击时触发)

        # 添加 "复制到剪贴板" 按钮
        self.copy_btn = QPushButton("复制到剪贴板") # 创建自定义按钮
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.button_box.addButton(self.copy_btn, QDialogButtonBox.ActionRole) # 将自定义按钮添加到box中

        layout.addWidget(self.button_box)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        self.setWindowTitle("已复制到剪贴板!")  # 更改标题栏文本
        # 设置一个2秒的定时器，2秒后调用 restore_title 方法
        QTimer.singleShot(2000, self.restore_title)

    def restore_title(self):
        """恢复对话框的原始标题"""
        self.setWindowTitle(self.original_title)

# --- 历史记录选择对话框 (修改后) ---
class HistoryDialog(QDialog):
    record_selected = pyqtSignal(dict)
    # history_updated = pyqtSignal(list) # 如果希望主窗口处理保存，可以使用这个信号

    def __init__(self, history_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史记录")
        self.setMinimumSize(850, 550)
        self.history_data = list(history_data) # 创建一个副本以允许修改

        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：列表
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection) # 允许多选
        self._populate_list_widget() # 抽取为方法
        self.list_widget.itemDoubleClicked.connect(self.load_selected_record)
        self.list_widget.currentItemChanged.connect(self.update_preview)
        self.list_widget.itemSelectionChanged.connect(self._update_button_states) # 更新按钮状态
        splitter.addWidget(self.list_widget)

        # 右侧：预览区
        preview_group = QWidget()
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(0,0,0,0)
        # preview_layout.addWidget(QLabel("预览:")) # 统一标签
        self.prompt_preview_edit = QTextEdit()
        self.prompt_preview_edit.setReadOnly(True)
        self.prompt_preview_edit.setPlaceholderText("在此预览选定记录的文件列表和Prompt指令...")
        preview_layout.addWidget(self.prompt_preview_edit)
        splitter.addWidget(preview_group)
        splitter.setSizes([300, 550])
        main_layout.addWidget(splitter)

        # 按钮
        self.buttons_box = QDialogButtonBox()
        self.load_button = self.buttons_box.addButton("加载选中记录", QDialogButtonBox.AcceptRole)
        self.delete_button = self.buttons_box.addButton("删除选中记录", QDialogButtonBox.DestructiveRole)
        self.cancel_button = self.buttons_box.addButton(QDialogButtonBox.Cancel)
        self.cancel_button.setText("取消")

        self.load_button.clicked.connect(self.load_selected_record)
        self.delete_button.clicked.connect(self.delete_selected_records)
        self.cancel_button.clicked.connect(self.reject)
        main_layout.addWidget(self.buttons_box)

        self._update_button_states()
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            self.update_preview(self.list_widget.currentItem())


    def _populate_list_widget(self):
        self.list_widget.clear()
        # 倒序显示，最新的在最上面
        # UserRole 存储的是记录在 self.history_data 中的原始（未反转的）索引
        for i, record in enumerate(reversed(self.history_data)):
            timestamp_str = record.get("id", f"记录 {len(self.history_data) - i}")
            project_name = record.get("project_name", "未命名项目")
            list_item_text = f"{timestamp_str} - {project_name}"
            item = QListWidgetItem(list_item_text)
            original_index = len(self.history_data) - 1 - i
            item.setData(Qt.UserRole, original_index)
            self.list_widget.addItem(item)

    def _update_button_states(self):
        has_selection = bool(self.list_widget.selectedItems())
        self.load_button.setEnabled(len(self.list_widget.selectedItems()) == 1) # 只允许加载单条
        self.delete_button.setEnabled(has_selection)

    def _save_history_to_file_internal(self):
        """将当前的 self.history_data 保存到文件"""
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            QMessageBox.warning(self, "保存历史失败", f"无法将更改保存到历史记录文件: {e}")
            return False

    def update_preview(self, current_item, previous_item=None):
        if not current_item:
            self.prompt_preview_edit.clear()
            self.prompt_preview_edit.setPlaceholderText("请选择一条历史记录以预览。")
            return

        original_index = current_item.data(Qt.UserRole)
        if not (0 <= original_index < len(self.history_data)):
            self.prompt_preview_edit.setPlainText("错误：无法获取记录数据。")
            return

        selected_record_data = self.history_data[original_index]
        preview_lines = []

        # 文件列表展示
        files_in_record = selected_record_data.get("files", [])
        if files_in_record:
            preview_lines.append("--- 文件列表 ---")
            for file_entry in files_in_record:
                filename = file_entry.get("filename", "未知文件")
                # content_exists = bool(file_entry.get("content", "").strip())
                # path_info = file_entry.get("path", "")
                # display_name = filename
                # if filename == "未知文件" and not content_exists:
                #     continue # 完全空的条目

                # if not path_info and filename != "未知文件":
                #     display_name += " (仅内容)"
                # elif not path_info and filename == "未知文件" and content_exists:
                #     display_name = "匿名内容块"

                # 只显示有效的文件名
                if filename != "未知文件" or file_entry.get("content","").strip():
                    preview_lines.append(f"  • {filename}")
            preview_lines.append("") # 空行

        # Prompt指令展示
        prompt_content = selected_record_data.get("final_prompt", "").strip()
        preview_lines.append("--- 最终Prompt指令 ---")
        if prompt_content:
            preview_lines.append(prompt_content)
        else:
            preview_lines.append("(无)")

        self.prompt_preview_edit.setPlainText("\n".join(preview_lines))

    def delete_selected_records(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        reply = QMessageBox.question(self, "确认删除",
                                     f"确定要删除选中的 {len(selected_items)} 条历史记录吗？此操作不可恢复。",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # 获取选中项在 self.history_data 中的原始索引，并降序排列以便安全删除
        original_indices_to_delete = sorted([item.data(Qt.UserRole) for item in selected_items], reverse=True)

        for index in original_indices_to_delete:
            if 0 <= index < len(self.history_data):
                del self.history_data[index]

        if self._save_history_to_file_internal():
            QMessageBox.information(self, "删除成功", f"已成功删除 {len(selected_items)} 条记录。")
            # self.history_updated.emit(self.history_data) # 如果主窗口保存
        else:
            # 保存失败的消息已在 _save_history_to_file_internal 中显示
            # 可能需要重新加载原始数据或提示用户
            pass

        # 更新UI
        current_row_before_delete = self.list_widget.currentRow()
        self._populate_list_widget() # 重新填充列表

        if self.list_widget.count() > 0:
            # 尝试恢复选择到相似位置，或选择第一个
            new_row = min(current_row_before_delete, self.list_widget.count() - 1)
            self.list_widget.setCurrentRow(new_row if new_row >=0 else 0)
            if not self.list_widget.currentItem() and self.list_widget.count() > 0 : # 以防万一
                self.list_widget.setCurrentRow(0)

        else:
            self.prompt_preview_edit.clear()
            self.prompt_preview_edit.setPlaceholderText("没有历史记录可供预览。")

        self._update_button_states()


    def load_selected_record(self):
        selected_items = self.list_widget.selectedItems()
        if len(selected_items) == 1:
            current_item = selected_items[0]
            original_index = current_item.data(Qt.UserRole)
            if 0 <= original_index < len(self.history_data):
                selected_record_data = self.history_data[original_index]
                self.record_selected.emit(selected_record_data)
                self.accept()
            else:
                QMessageBox.warning(self, "错误", "无法加载选中的记录，索引无效。")
        elif len(selected_items) > 1:
             QMessageBox.information(self, "提示", "请只选择一条记录进行加载。")
        # else: No item selected, do nothing or handled by button state

# --- 主窗口 ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.file_blocks = [] # 这个列表主要在添加新块时使用
        self.init_ui()
        self._ensure_history_file_exists()

    def _ensure_history_file_exists(self):
        if not os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f)
            except IOError as e:
                QMessageBox.critical(self, "文件错误", f"无法创建历史文件: {HISTORY_FILE}\n{e}")

    def _load_history_from_file(self):
        if not os.path.exists(HISTORY_FILE): return []
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return history if isinstance(history, list) else []
        except (json.JSONDecodeError, IOError) as e:
            QMessageBox.warning(self, "加载历史失败", f"无法读取历史文件: {e}")
            return []

    def _save_record_to_file(self, record_data):
        history = self._load_history_from_file()
        history.append(record_data)
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
            # QMessageBox.information(self, "已保存", "当前记录已保存到历史。") # <--- 将此行注释或删除
            print("记录已自动保存到历史。") # 可以选择在控制台输出一条信息，或者完全静默
        except Exception as e:
            QMessageBox.warning(self, "保存失败", f"无法保存历史记录: {e}")

    def init_ui(self):
        self.setWindowTitle("代码与Prompt整合工具")
        self.setGeometry(100, 100, 1200, 800)
        main_layout = QVBoxLayout(self)

        top_buttons_layout = QHBoxLayout()
        self.load_history_button = QPushButton("加载历史记录")
        self.load_history_button.clicked.connect(self.show_history_dialog)
        top_buttons_layout.addWidget(self.load_history_button)
        top_buttons_layout.addStretch()
        main_layout.addLayout(top_buttons_layout)

        top_section_layout = QHBoxLayout()
        # ... (项目名称和介绍部分不变) ...
        project_name_group = QVBoxLayout()
        project_name_group.addWidget(QLabel("项目名称:"))
        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("例如：Finance")
        project_name_group.addWidget(self.project_name_input)
        top_section_layout.addLayout(project_name_group, 1)
        project_desc_group = QVBoxLayout()
        project_desc_group.addWidget(QLabel("项目介绍:"))
        self.project_desc_input = QTextEdit()
        # 设置预设的文本内容，而不是占位符
        self.project_desc_input.setPlainText("我有一个Xcode开发的iPhone手机应用程序.")
        self.project_desc_input.setFixedHeight(80) # 保持固定高度
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
        self.add_file_block_button.clicked.connect(lambda: self._add_file_block_widget(add_to_list_ref=True))
        add_button_layout = QVBoxLayout()
        add_button_layout.addWidget(self.add_file_block_button)
        add_button_layout.addStretch()
        second_section_wrapper_layout.addLayout(add_button_layout)
        main_layout.addLayout(second_section_wrapper_layout)

        for _ in range(3):
            self._add_file_block_widget(add_to_list_ref=True)

        bottom_section_layout = QVBoxLayout()
        bottom_section_layout.addWidget(QLabel("最终Prompt指令:"))
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("例如：我现在需要制作底部tab里的“资产”页面...")
        self.prompt_input.setMinimumHeight(100)
        self.prompt_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # 允许扩展
        bottom_section_layout.addWidget(self.prompt_input)
        self.generate_button = QPushButton("生成最终文本并保存记录")
        self.generate_button.setFixedHeight(40)
        self.generate_button.clicked.connect(self.generate_and_save_output)
        generate_button_wrapper = QHBoxLayout()
        generate_button_wrapper.addStretch()
        generate_button_wrapper.addWidget(self.generate_button)
        bottom_section_layout.addLayout(generate_button_wrapper)
        main_layout.addLayout(bottom_section_layout)

        main_layout.setStretchFactor(top_buttons_layout, 0)
        main_layout.setStretchFactor(top_section_layout, 0) # 项目名称和介绍部分不拉伸
        main_layout.setStretchFactor(second_section_wrapper_layout, 1) # 文件块部分可拉伸
        main_layout.setStretchFactor(bottom_section_layout, 0) # Prompt指令部分不拉伸，但其内部的QTextEdit可拉伸

    def _clear_all_file_blocks_ui(self):
        """仅清除UI上的文件块，不修改 self.file_blocks 引用"""
        while self.file_blocks_layout.count():
            child = self.file_blocks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _add_file_block_widget(self, add_to_list_ref=False, file_data=None):
        """
        add_to_list_ref: 是否将新创建的块添加到 self.file_blocks 列表。
                         在用户手动点击"+"或初始化时应为True。
                         在从历史记录加载时，我们会单独管理 self.file_blocks。
        """
        file_block = FileBlockWidget()
        file_block.delete_requested.connect(self._handle_delete_file_block) # 连接信号
        if file_data:
            file_block.load_data(file_data.get("path"), file_data.get("content"))
        self.file_blocks_layout.addWidget(file_block)
        if add_to_list_ref: # 只有在明确需要时才添加到 self.file_blocks
            self.file_blocks.append(file_block)
        return file_block

    def _handle_delete_file_block(self, block_to_delete):
        """处理文件块删除请求的槽函数"""
        if block_to_delete in self.file_blocks:
            self.file_blocks.remove(block_to_delete)

        self.file_blocks_layout.removeWidget(block_to_delete)
        block_to_delete.deleteLater()
        # print(f"Deleted block. Remaining in list: {len(self.file_blocks)}, Remaining in layout: {self.file_blocks_layout.count()}")


    def show_history_dialog(self):
        history_data = self._load_history_from_file()
        if not history_data:
            QMessageBox.information(self, "无历史记录", "目前没有已保存的历史记录。")
            return
        dialog = HistoryDialog(history_data, self)
        dialog.record_selected.connect(self.load_record_into_ui)
        dialog.exec_()

    def load_record_into_ui(self, record_data):
        self.project_name_input.setText(record_data.get("project_name", ""))
        self.project_desc_input.setPlainText(record_data.get("project_desc", "我有一个Xcode开发的iPhone手机应用程序.")) # 加载时也确保有默认值或记录值
        self.prompt_input.setPlainText(record_data.get("final_prompt", ""))

        self._clear_all_file_blocks_ui() # 清除UI上的现有文件块
        self.file_blocks.clear() # 清空内部跟踪列表

        loaded_files_data = record_data.get("files", [])
        if loaded_files_data:
            for file_info in loaded_files_data:
                new_block = self._add_file_block_widget(add_to_list_ref=False, file_data=file_info)
                self.file_blocks.append(new_block) # 加载时，我们重新构建 self.file_blocks
        else: # 如果历史记录中没有文件块
            pass # 不自动添加，保持为空

        # 确保至少有一定数量的空块，或者按需补齐 (可选逻辑)
        # 当前逻辑：如果历史记录没有文件，则文件区为空。如果需要默认块，在这里添加。
        # 例如，确保至少有一个块，如果加载后为空：
        # if not self.file_blocks:
        #    self._add_file_block_widget(add_to_list_ref=True)

        # 如果希望加载后，若文件块少于3个，则补齐到3个空块：
        num_to_add = 3 - len(self.file_blocks)
        if num_to_add > 0:
            for _ in range(num_to_add):
                self._add_file_block_widget(add_to_list_ref=True)


        QMessageBox.information(self, "加载完成", f"记录 '{record_data.get('id')}' 已加载。")

    def generate_and_save_output(self):
        project_name = self.project_name_input.text().strip()
        project_desc = self.project_desc_input.toPlainText().strip()
        final_prompt = self.prompt_input.toPlainText().strip()

        if not project_desc or not project_name: # 理论上 project_desc 不会为空了，因为有预设值
            QMessageBox.warning(self, "信息不完整", "请输入项目名称和项目介绍。")
            return

        current_record = {
            "id": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project_name": project_name,
            "project_desc": project_desc,
            "files": [],
            "final_prompt": final_prompt
        }
        file_tree_lines = []
        valid_file_infos_for_output = []

        # 从UI布局中获取当前文件块，而不是依赖 self.file_blocks 可能的过时状态
        current_ui_file_blocks = []
        for i in range(self.file_blocks_layout.count()):
            widget = self.file_blocks_layout.itemAt(i).widget()
            if isinstance(widget, FileBlockWidget):
                current_ui_file_blocks.append(widget)

        for block_widget in current_ui_file_blocks:
            path, filename, content = block_widget.get_file_info()
            # 只有当文件块包含实际内容或有效路径时才保存和用于输出
            if content.strip() or (path and path not in ["未选择文件", "路径未记录"]):
                current_record["files"].append({
                    "path": path,
                    "filename": filename,
                    "content": content # 对于.db文件，这里会保存用户输入的内容
                })
                if path and path not in ["未选择文件", "路径未记录"]:
                    file_tree_lines.append(f"  ├── {filename}")
                    # 对于.db文件，如果用户在content_edit中输入了内容，也会被加入
                    valid_file_infos_for_output.append({"path": path, "content": content})
                elif content.strip() and filename != "未知文件": # 即使是.db文件，如果用户输入了内容，也应该算作有内容
                    file_tree_lines.append(f"  ├── {filename} (无路径, 仅内容)")
                    valid_file_infos_for_output.append({"path": f"{filename} (内容)", "content": content})
                # 如果只有空的content和“未知文件”，则不加入输出文本

        self._save_record_to_file(current_record) # 保存记录，现在不会弹窗了

        final_builder = [project_desc]
        tree_string = "\n".join(file_tree_lines) if file_tree_lines else ""
        final_builder.append(f'\n"{project_name}"' + (f'\n{tree_string}' if tree_string else ""))

        for info in valid_file_infos_for_output:
            # 确保路径和内容不都为空才添加到最终输出
            # 对于.db文件，其文件路径是有的，内容是用户输入的（如果输入了）
            # 如果用户没有为.db文件输入任何内容，info["content"]会是空字符串
            # 这里的逻辑是，只要有路径或者有内容，就加入。
            # 如果希望 .db 文件即使内容为空也显示其路径，可以调整这里的判断
            # 当前逻辑：如果.db文件路径存在，且用户未输入任何内容，则输出类似 "路径/文件名.db\n“”; "
            # 如果希望不输出空的 “”，可以修改为：
            # if info["path"].strip():
            #     final_builder.append(f'\n\n{info["path"]}')
            #     if info["content"].strip():
            #          final_builder.append(f'\n“{info["content"]}”；')
            #     else:
            #          final_builder.append('； # 内容未提供或为空') # 或者其他标记
            # elif info["content"].strip(): # 无路径但有内容
            #     final_builder.append(f'\n\n{info["path"]}\n“{info["content"]}”；')

            # 保持原逻辑，如果.db文件内容为空，则输出 "路径/文件名.db\n“”; "
            if info["path"].strip() or info["content"].strip():
                 final_builder.append(f'\n\n{info["path"]}\n“{info["content"]}”；')


        if final_prompt:
            final_builder.append(f'\n\n{final_prompt}')
        final_text = "".join(final_builder)

        output_dialog = OutputDialog(final_text, self)
        output_dialog.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 创建 HISTORY_FILE 所在的目录（如果尚不存在）
    history_dir = os.path.dirname(HISTORY_FILE)
    if history_dir and not os.path.exists(history_dir): # 确保目录非空再创建
        try:
            os.makedirs(history_dir)
        except OSError as e:
            # 如果因为权限等问题无法创建目录，这里可以给用户一个提示
            # 但通常情况下，用户文档目录应该是可写的
            print(f"警告: 无法创建历史记录目录 {history_dir}: {e}")
            # 程序仍可继续，但历史记录可能无法保存到预期位置（如果_ensure_history_file_exists也失败）

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())