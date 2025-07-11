import os
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- 配置 ---
BASE_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Resources')
ALLOWED_APPS = ['ONews', 'Finance']

# --- API 路由 ---
@app.route('/api/<app_name>/check_version', methods=['GET'])
def check_version(app_name):
    print(f"收到来自应用 '{app_name}' 的版本检查请求")
    if app_name not in ALLOWED_APPS:
        return jsonify({"error": "无效的应用名称"}), 404
    
    version_file_path = os.path.join(BASE_RESOURCES_DIR, app_name, 'version.json')
    print(f"正在尝试访问版本文件: {version_file_path}")
    
    if os.path.exists(version_file_path):
        return send_from_directory(os.path.join(BASE_RESOURCES_DIR, app_name), 'version.json')
    else:
        return jsonify({"error": "版本文件未找到"}), 404

# --- 新增的API：获取目录文件清单 ---
@app.route('/api/<app_name>/list_files', methods=['GET'])
def list_files(app_name):
    dirname = request.args.get('dirname')
    print(f"收到来自应用 '{app_name}' 的目录清单请求: {dirname}")

    if not dirname:
        return jsonify({"error": "缺少目录名参数"}), 400

    target_dir = os.path.join(BASE_RESOURCES_DIR, app_name, dirname)

    if not os.path.isdir(target_dir):
        return jsonify({"error": "目录未找到"}), 404
    
    try:
        # 只返回文件名，并且过滤掉macOS的系统隐藏文件
        files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f)) and not f.startswith('.')]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- 修改后的下载路由，现在可以处理子目录中的文件 ---
@app.route('/api/<app_name>/download', methods=['GET'])
def download_file(app_name):
    # filename 参数现在可能是 "some.json" 或 "some_dir/some_image.jpg"
    filename = request.args.get('filename')
    print(f"收到来自应用 '{app_name}' 的文件下载请求: {filename}")

    if app_name not in ALLOWED_APPS:
        return jsonify({"error": "无效的应用名称"}), 404
    if not filename:
        return jsonify({"error": "缺少文件名参数"}), 400

    # 安全地处理路径，防止目录遍历攻击
    # os.path.normpath 会处理 '..' 等路径
    safe_path = os.path.normpath(os.path.join(app_name, filename))
    if safe_path.startswith('..') or os.path.isabs(safe_path):
        return jsonify({"error": "无效的路径"}), 400
        
    # 从基础资源目录开始构建路径
    full_path = os.path.join(BASE_RESOURCES_DIR, safe_path)

    if not os.path.isfile(full_path):
        print(f"错误: 请求的文件不存在: {full_path}")
        return jsonify({"error": "文件未找到"}), 404

    try:
        # send_from_directory 需要目录和文件名作为分离的参数
        directory, file = os.path.split(full_path)
        print(f"正在发送文件 '{file}' 从目录 '{directory}'")
        return send_from_directory(directory, file, as_attachment=True)
    except Exception as e:
        print(f"发生错误: {e}")
        return jsonify({"error": str(e)}), 500

# --- 服务器启动 ---
if __name__ == '__main__':
    supported_apps_str = ", ".join(ALLOWED_APPS)
    print("多应用服务器正在启动...")
    print(f"支持的应用: {supported_apps_str}")
    print(f"资源目录被定位在: {BASE_RESOURCES_DIR}")
    host_ip = '192.168.50.148'
    port = 5000
    print("请确保您的手机和电脑连接到同一个Wi-Fi网络")
    print(f"在iOS App中请使用 http://{host_ip}:{port}/api/ONews/... 访问")
    app.run(host=host_ip, port=port, debug=False)