import os
import sys
import pyperclip
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QTextBrowser, QMainWindow, QAction
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl

# 保持原有的搜索目录列表
searchFolders = [
    "/Users/yanzhang/Documents/ScriptEditor/",
    "/Users/yanzhang/Library/Services/",
    "/Users/yanzhang/Documents/Financial_System",
    "/Users/yanzhang/Documents/python_code",
    "/Users/yanzhang/Documents/News/backup",
    "/Users/yanzhang/Documents/sskeysskey.github.io",
    # "/Users/yanzhang/Documents/LuxuryBox",
    # "/Users/yanzhang/Downloads/backup/TXT",
    # "/Users/yanzhang/Documents/Books",
    # "/Users/yanzhang/Downloads/backup/FT金融时报/ft-kanmagazine"
]

class CustomTextBrowser(QTextBrowser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setOpenLinks(False)  # 禁止自动打开链接

class SearchWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, directories, keywords):
        super().__init__()
        self.directories = directories
        self.keywords = keywords

    def run(self):
        results = search_files(self.directories, self.keywords)
        self.finished.emit(results)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("代码和文件搜索")
        self.setGeometry(350, 200, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setFixedHeight(30)
        self.input_field.setFont(QFont("Arial", 18))
        self.search_button = QPushButton("搜索")
        self.search_button.setFixedSize(60, 30)
        self.input_layout.addWidget(self.input_field, 7)
        self.input_layout.addWidget(self.search_button, 1)
        self.layout.addLayout(self.input_layout)

        self.loading_label = QLabel("正在搜索...", self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setFont(QFont("Arial", 14))
        self.loading_label.hide()
        self.layout.addWidget(self.loading_label)

        self.result_area = CustomTextBrowser()
        self.result_area.anchorClicked.connect(self.open_file)
        self.result_area.setFont(QFont("Arial", 12))
        self.layout.addWidget(self.result_area)

        self.search_button.clicked.connect(self.start_search)
        self.input_field.returnPressed.connect(self.start_search)
        self.result_area.anchorClicked.connect(self.open_file)

        # 添加 ESC 键关闭窗口的功能
        self.shortcut_close = QKeySequence("Esc")
        self.quit_action = QAction("Quit", self)
        self.quit_action.setShortcut(self.shortcut_close)
        self.quit_action.triggered.connect(self.close)
        self.addAction(self.quit_action)

    def start_search(self):
        keywords = self.input_field.text()
        self.loading_label.show()
        self.result_area.clear()
        self.result_area.setEnabled(False)
        self.search_button.setEnabled(False)
        self.input_field.setEnabled(False)
        self.worker = SearchWorker(searchFolders, keywords)
        self.worker.finished.connect(self.show_results)
        self.worker.start()

    def show_results(self, results):
        self.loading_label.hide()
        self.result_area.setEnabled(True)
        self.search_button.setEnabled(True)
        self.input_field.setEnabled(True)
        
        html_content = ""

        for directory, files in results.items():
            if files:
                html_content += f"<h2 style='color: yellow; font-size: 18px;'>{directory}</h2>"
                for file in files:
                    file_path = os.path.join(directory, file)
                    html_content += f"<p><a href='{file_path}' style='color: orange; text-decoration: underline; font-size: 18px;'>{file}</a></p>"

        self.result_area.setHtml(html_content)

        # 滚动到顶部
        self.result_area.verticalScrollBar().setValue(0)

    def open_file(self, url):
        if url.scheme() == 'symbol':
            # 提取 symbol
            symbol = url.toString().replace('symbol://', '').strip()
            if symbol:
                # 将 symbol 复制到剪贴板
                pyperclip.copy(symbol)
                # 获取 stock_chart.py 的绝对路径
                stock_chart_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '/Users/yanzhang/Documents/Financial_System/Query/Stock_Chart.py')
                # 调用 stock_chart.py，传递 'paste' 参数
                subprocess.Popen([sys.executable, stock_chart_path, 'paste'])
        else:
            file_path = url.toLocalFile()
            if not file_path:
                file_path = url.toString()
            try:
                if sys.platform == "win32":
                    os.startfile(file_path)
                else:
                    subprocess.call(("open", file_path))
            except Exception as e:
                print(f"无法打开文件 {file_path}: {e}")

# 保持原有的搜索相关函数不变
def search_files(directories, keywords):
    matched_files = {}
    keywords_lower = [keyword.strip().lower() for keyword in keywords.split()]

    for directory in directories:
        matched_files[directory] = []
        for root, dirs, files in os.walk(directory):
            for dir_name in dirs:
                if dir_name.endswith('.workflow'):
                    handle_workflow_dir(root, dir_name, directory, keywords_lower, matched_files)
            for name in files:
                handle_file(root, name, directory, keywords_lower, matched_files)
    return matched_files

def handle_workflow_dir(root, dir_name, directory, keywords_lower, matched_files):
    workflow_path = os.path.join(root, dir_name)
    if all(keyword_lower in dir_name.lower() for keyword_lower in keywords_lower):
        matched_files[directory].append(os.path.relpath(workflow_path, directory))
        return
    try:
        wflow_path = os.path.join(workflow_path, 'contents/document.wflow')
        with open(wflow_path, 'r') as file:
            content = file.read().lower()
        if all(keyword_lower in content for keyword_lower in keywords_lower):
            matched_files[directory].append(os.path.relpath(workflow_path, directory))
    except Exception as e:
        print(f"Error reading {wflow_path}: {e}")

def handle_file(root, name, directory, keywords_lower, matched_files):
    item_path = os.path.join(root, name)
    if all(keyword_lower in name.lower() for keyword_lower in keywords_lower):
        matched_files[directory].append(os.path.relpath(item_path, directory))
        return
    if item_path.endswith('.scpt'):
        try:
            content = subprocess.check_output(['osadecompile', item_path], text=True).lower()
            if all(keyword_lower in content for keyword_lower in keywords_lower):
                matched_files[directory].append(os.path.relpath(item_path, directory))
        except Exception as e:
            print(f"Error decompiling {item_path}: {e}")
    elif item_path.endswith(('.txt', '.py', '.json', '.js', '.css', '.html', '.csv', '.md')):
        try:
            with open(item_path, 'r') as file:
                content = file.read().lower()
            if all(keyword_lower in content for keyword_lower in keywords_lower):
                matched_files[directory].append(os.path.relpath(item_path, directory))
        except Exception as e:
            print(f"Error reading {item_path}: {e}")

def read_file_content(path):
    if path.endswith('.scpt'):
        return subprocess.check_output(['osadecompile', path], text=True).lower()
    with open(path, 'r') as file:
        return file.read().lower()

if __name__ == "__main__":
    # 处理剪贴板警告
    try:
        from PyQt5.QtWidgets import QApplication
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass  # 较旧的 PyQt 版本可能没有这些属性

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "input":
            # 显示窗口，让用户输入
            pass
        elif arg == "paste":
            # 使用剪贴板内容进行搜索
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                window.input_field.setText(clipboard_content)
                window.start_search()
            else:
                print("剪贴板为空，请复制一些文本后再试。")
    else:
        print("请提供参数 input 或 paste")

    sys.exit(app.exec_())