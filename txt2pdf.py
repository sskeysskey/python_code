from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from PIL import Image
import re
import os
import glob
import shutil
import io

def find_all_news_files(directory):
    pattern = os.path.join(directory, "News_*.txt")
    return sorted(glob.glob(pattern))

def get_pdf_path(txt_path):
    directory = os.path.dirname(txt_path)
    filename = os.path.basename(txt_path)
    pdf_filename = os.path.splitext(filename)[0] + '.pdf'
    return os.path.join(directory, pdf_filename)

def needs_conversion(txt_path, pdf_path):
    if not os.path.exists(pdf_path):
        return True
    txt_mtime = os.path.getmtime(txt_path)
    pdf_mtime = os.path.getmtime(pdf_path)
    return txt_mtime > pdf_mtime

def move_cnh_file(source_dir):
    try:
        cnh_pattern = os.path.join(source_dir, "TodayCNH_*.html")
        cnh_files = glob.glob(cnh_pattern)
        
        if not cnh_files:
            print("没有找到TodayCNH_开头的文件")
            return False
            
        source_file = cnh_files[0]
        backup_dir = os.path.join(source_dir, "backup", "backup")
        os.makedirs(backup_dir, exist_ok=True)
        target_file = os.path.join(backup_dir, os.path.basename(source_file))
        os.rename(source_file, target_file)
        print(f"成功移动文件: {os.path.basename(source_file)} -> {backup_dir}")
        return True
        
    except Exception as e:
        print(f"移动文件时出错: {str(e)}")
        return False

def parse_article_copier(file_path):
    url_images = {}
    current_url = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('http'):
            current_url = line
            url_images[current_url] = []
        elif line.endswith('.jpg') and current_url:
            url_images[current_url].append(line)
    
    print("解析到的URL和图片映射:")
    for url, images in url_images.items():
        print(f"URL: {url}")
        print(f"Images: {images}")
        
    return url_images

def find_images_for_content(content, url_images):
    article_images = []
    articles = []
    current_article = []
    lines = content.strip().split('\n')
    
    for line in lines:
        if line.startswith('http'):
            if current_article:
                articles.append('\n'.join(current_article))
                current_article = []
        current_article.append(line)
    
    if current_article:
        articles.append('\n'.join(current_article))
    
    print("\n找到的文章和URL:")
    for article in articles:
        url_match = re.search(r'(https?://[^\s]+)', article)
        if url_match:
            url = url_match.group(1)
            print(f"\nArticle URL: {url}")
            
            for article_url, images in url_images.items():
                if url in article_url or article_url in url:
                    print(f"Matched with: {article_url}")
                    print(f"Images found: {images}")
                    article_images.append((article, images))
                    break
    
    return article_images

def distribute_images_in_content(content, url_images):
    if not url_images:
        return content
    
    article_images = find_images_for_content(content, url_images)
    
    print("\n开始分布图片:")
    print(f"找到 {len(article_images)} 篇文章需要处理")
    
    processed_content = content
    for article, images in article_images:
        if not images:
            continue
            
        print(f"\n处理文章，包含 {len(images)} 张图片")
        
        lines = article.strip().split('\n')
        url_line = next((line for line in lines if line.startswith('http')), '')
        content_lines = [line for line in lines if line != url_line and line.strip()]
        
        new_content = [url_line]
        if images:
            new_content.append(f"--IMAGE_PLACEHOLDER_{images[0]}--")
        
        remaining_images = images[1:] if images else []
        if content_lines and remaining_images:
            spacing = max(1, len(content_lines) // len(remaining_images))
            
            for i, line in enumerate(content_lines):
                new_content.append(line)
                if remaining_images and (i + 1) % spacing == 0:
                    new_content.append(f"--IMAGE_PLACEHOLDER_{remaining_images[0]}--")
                    remaining_images = remaining_images[1:]
            
            for img in remaining_images:
                new_content.append(f"--IMAGE_PLACEHOLDER_{img}--")
        else:
            new_content.extend(content_lines)
        
        try:
            new_article = '\n\n'.join(new_content)
            processed_content = processed_content.replace(article, new_article)
            print("文章内容替换成功")
        except Exception as e:
            print(f"文章内容替换失败: {str(e)}")
    
    return processed_content

def clean_and_format_text(txt_path, article_copier_path, image_dir):
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"\n处理文件: {txt_path}")
        print("\n原始内容的前200个字符:")
        print(repr(content[:200]))  # 使用repr()可以显示空白字符
        
        url_images = parse_article_copier(article_copier_path)
        cleaned_content = distribute_images_in_content(content, url_images)

        print("\n处理后内容的前200个字符:")
        print(repr(cleaned_content[:200]))
        
        images = []
        print("\n找到的图片占位符:")
        for img_placeholder in re.finditer(r'--IMAGE_PLACEHOLDER_(.*?)--(?:\n|$)', cleaned_content):
            img_name = img_placeholder.group(1).strip()
            img_path = os.path.join(image_dir, img_name)
            print(f"Image placeholder: {img_name}")
            print(f"Full path: {img_path}")
            print(f"Exists: {os.path.exists(img_path)}")
            if os.path.exists(img_path):
                images.append(img_path)
        
        # 在删除URL之前打印
        print("\n准备删除URL...")

        cleaned_content = re.sub(r'^\s*\ufeff?https?://[^\n]+\n?', '', cleaned_content, flags=re.MULTILINE)

        print("\n删除URL后的前200个字符:")
        print(repr(cleaned_content[:200]))

        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        return cleaned_content.strip(), images
        
    except Exception as e:
        print(f"处理文本时出现错误: {str(e)}")
        return None, []

def txt_to_pdf_with_formatting(txt_path, pdf_path, article_copier_path, image_dir):
    try:
        content, images = clean_and_format_text(txt_path, article_copier_path, image_dir)
        if not content:
            return False
            
        print(f"\n开始创建PDF: {pdf_path}")
        print(f"图片数量: {len(images)}")
        
        # 创建PDF文档
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # 设置中文字体
        try:
            pdfmetrics.registerFont(TTFont('PingFang', '/Users/yanzhang/Library/Fonts/FangZhengHeiTiJianTi-1.ttf'))
            font_name = 'PingFang'
            font_size = 40  # 增加字体大小，原来是12
        except:
            print("无法加载中文字体，使用默认字体")
            font_name = 'Helvetica'
            font_size = 14
            
        def set_font():
            c.setFont(font_name, font_size)
            
        set_font()  # 初始设置字体
        
        x = 20  # 减小左边距，原来是50
        y = height - 30  # 减小上边距，原来是height - 50
        line_height = 44  # 减小行高，原来是20
        
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if '--IMAGE_PLACEHOLDER_' in paragraph:
                img_filename = paragraph.replace('--IMAGE_PLACEHOLDER_', '').replace('--', '').strip()
                img_path = os.path.join(image_dir, img_filename)
                
                if os.path.exists(img_path):
                    try:
                        img = Image.open(img_path)
                        img_width, img_height = img.size
                        
                        # 调整图片大小以适应页面
                        aspect = img_width / float(img_height)
                        if img_width > width - 40:
                            img_width = width - 60
                            img_height = img_width / aspect
                        
                        # 如果当前页空间不足，新建页面
                        if y < img_height + 80:  # 增加空间以容纳描述文字
                            c.showPage()
                            set_font()
                            y = height - 30
                            
                        # 绘制图片
                        img_x = (width - img_width) / 2  # 图片水平居中
                        c.drawImage(img_path, img_x, y - img_height + 20, width=img_width, height=img_height)
                        
                        # 处理图片描述文字
                        description = os.path.splitext(img_filename)[0]  # 移除文件扩展名
                        c.setFont(font_name, font_size * 0.4)
                        
                        # 计算描述文字的行数和位置
                        desc_font_size = font_size * 0.4
                        max_desc_width = width - 60  # 留出左右边距
                        desc_words = []
                        current_line = ""
                        
                        # 将描述文字分行
                        for char in description:
                            test_line = current_line + char
                            if c.stringWidth(test_line, font_name, desc_font_size) <= max_desc_width:
                                current_line = test_line
                            else:
                                desc_words.append(current_line)
                                current_line = char
                        if current_line:
                            desc_words.append(current_line)
                        
                        # 绘制描述文字
                        desc_y = y - img_height - 10
                        for line in desc_words:
                            line_width = c.stringWidth(line, font_name, desc_font_size)
                            desc_x = (width - line_width) / 2  # 文字水平居中
                            c.drawString(desc_x, desc_y, line)
                            desc_y -= desc_font_size + 2  # 行间距
                        
                        set_font()  # 恢复原来的字体大小
                        y -= (img_height + 80)  # 增加间距以容纳描述文字
                        
                    except Exception as e:
                        print(f"处理图片时出错: {str(e)}")
                        
            else:
                # 处理文本段落
                text = paragraph.strip()
                max_width = width - 30  # 减小文本区域边距，原来是100
                
                while text:
                    # 计算当前行可以容纳的文字
                    line = ''
                    i = 0
                    while i < len(text):
                        if c.stringWidth(line + text[i]) < max_width:
                            line += text[i]
                            i += 1
                        else:
                            break
                    
                    # 如果一个字符都放不下，强制换页
                    if not line:
                        line = text[0]
                        i = 1
                    
                    # 检查是否需要换页
                    if y < 30:  # 减小底部边距，原来是50
                        c.showPage()
                        set_font()  # 新页面重新设置字体
                        y = height - 40
                    
                    # 绘制当前行
                    c.drawString(x, y, line)
                    y -= line_height
                    
                    # 更新剩余文本
                    text = text[i:]
                
                # 段落间距
                y -= 10  # 减小段落间距，原来是10
        
        c.save()
        return True
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        return False

def process_all_files(directory, article_copier_path, image_dir):
    txt_files = find_all_news_files(directory)
    
    if not txt_files:
        print(f"在 {directory} 目录下没有找到以News_开头的txt文件")
        return
    
    converted = 0
    skipped = 0
    failed = 0
    
    for txt_file in txt_files:
        pdf_file = get_pdf_path(txt_file)
        
        try:
            if needs_conversion(txt_file, pdf_file):
                print(f"正在处理: {os.path.basename(txt_file)}")
                if txt_to_pdf_with_formatting(txt_file, pdf_file, article_copier_path, image_dir):
                    print(f"成功转换: {os.path.basename(txt_file)} -> {os.path.basename(pdf_file)}")
                    converted += 1
                else:
                    print(f"转换失败: {os.path.basename(txt_file)}")
                    failed += 1
            else:
                print(f"跳过已存在的文件: {os.path.basename(txt_file)}")
                skipped += 1
                
        except Exception as e:
            print(f"处理 {os.path.basename(txt_file)} 时出错: {str(e)}")
            failed += 1
    
    print("\n处理完成:")
    print(f"成功转换: {converted} 个文件")
    print(f"跳过处理: {skipped} 个文件")
    print(f"转换失败: {failed} 个文件")

if __name__ == "__main__":
    news_directory = "/Users/yanzhang/Documents/News/"
    article_copier_path = "/Users/yanzhang/Documents/News/article_copier.txt"
    image_dir = "/Users/yanzhang/Downloads/news_image"
    
    process_all_files(news_directory, article_copier_path, image_dir)
    move_cnh_file(news_directory)