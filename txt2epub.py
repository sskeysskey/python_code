from ebooklib import epub
import re
import os
import glob
import shutil
from bs4 import BeautifulSoup

def find_all_news_files(directory):
    pattern = os.path.join(directory, "News_*.txt")
    return sorted(glob.glob(pattern))

def get_epub_path(txt_path):
    # 获取目录路径和文件名
    directory = os.path.dirname(txt_path)
    filename = os.path.basename(txt_path)
    
    # 将.txt替换为.epub
    epub_filename = os.path.splitext(filename)[0] + '.epub'
    
    return os.path.join(directory, epub_filename)

def needs_conversion(txt_path, epub_path):
    # 如果epub文件不存在，需要转换
    if not os.path.exists(epub_path):
        return True
    
    # 如果txt文件比epub文件新，需要转换
    txt_mtime = os.path.getmtime(txt_path)
    epub_mtime = os.path.getmtime(epub_path)
    return txt_mtime > epub_mtime

def move_cnh_file(source_dir):
    """
    移动第一个找到的TodayCNH_文件到backup目录
    
    Args:
        source_dir (str): 源目录路径
        
    Returns:
        bool: 移动是否成功
    """
    try:
        # 构建源文件搜索模式
        cnh_pattern = os.path.join(source_dir, "TodayCNH_*.html")
        cnh_files = glob.glob(cnh_pattern)
        
        if not cnh_files:
            print("没有找到TodayCNH_开头的文件")
            return False
            
        # 获取第一个匹配的文件
        source_file = cnh_files[0]
        
        # 构建目标目录路径
        backup_dir = os.path.join(source_dir, "backup", "backup")
        
        # 确保目标目录存在
        os.makedirs(backup_dir, exist_ok=True)
        
        # 构建目标文件路径
        target_file = os.path.join(backup_dir, os.path.basename(source_file))
        
        # 移动文件
        os.rename(source_file, target_file)
        print(f"成功移动文件: {os.path.basename(source_file)} -> {backup_dir}")
        return True
        
    except Exception as e:
        print(f"移动文件时出错: {str(e)}")
        return False

def parse_article_copier(file_path):
    """解析article_copier.txt文件，返回URL和图片的映射关系"""
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
    
    # 添加调试信息
    print("解析到的URL和图片映射:")
    for url, images in url_images.items():
        print(f"URL: {url}")
        print(f"Images: {images}")
        
    return url_images

def find_images_for_content(content, url_images):
    """按文章分组找到内容中URL对应的图片文件"""
    article_images = []
    
    # 使用URL来分割文章内容
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
        # 从文章内容中提取URL
        url_match = re.search(r'(https?://[^\s]+)', article)
        if url_match:
            url = url_match.group(1)
            print(f"\nArticle URL: {url}")
            
            # 查找匹配的URL及其图片
            for article_url, images in url_images.items():
                if url in article_url or article_url in url:
                    print(f"Matched with: {article_url}")
                    print(f"Images found: {images}")
                    article_images.append((article, images))
                    break
    
    return article_images

def distribute_images_in_content(content, url_images):
    """在每篇文章中均匀分布图片"""
    if not url_images:
        return content
    
    # 获取文章和对应的图片
    article_images = find_images_for_content(content, url_images)
    
    print("\n开始分布图片:")
    print(f"找到 {len(article_images)} 篇文章需要处理")
    
    # 处理每篇文章
    processed_content = content
    for article, images in article_images:
        if not images:
            continue
            
        print(f"\n处理文章，包含 {len(images)} 张图片")
        
        # 将文章分割成URL和正文部分
        lines = article.strip().split('\n')
        url_line = next((line for line in lines if line.startswith('http')), '')
        content_lines = [line for line in lines if line != url_line and line.strip()]
        
        # 重新组织文章内容，在URL后立即插入第一张图片
        new_content = [url_line]
        if images:
            new_content.append(f"--IMAGE_PLACEHOLDER_{images[0]}--")
        
        # 计算剩余图片的分布间隔
        remaining_images = images[1:] if images else []
        if content_lines and remaining_images:
            spacing = max(1, len(content_lines) // len(remaining_images))
            
            for i, line in enumerate(content_lines):
                new_content.append(line)
                if remaining_images and (i + 1) % spacing == 0:
                    new_content.append(f"--IMAGE_PLACEHOLDER_{remaining_images[0]}--")
                    remaining_images = remaining_images[1:]
            
            # 添加剩余的图片
            for img in remaining_images:
                new_content.append(f"--IMAGE_PLACEHOLDER_{img}--")
        else:
            new_content.extend(content_lines)
        
        # 使用更安全的替换方法
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
        
        # 解析article_copier.txt
        url_images = parse_article_copier(article_copier_path)
        
        # 先处理图片分布
        cleaned_content = distribute_images_in_content(content, url_images)
        
        # 获取所有图片路径（在处理链接之前）
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
        
        # 删除URL行
        cleaned_content = re.sub(r'^https?://[^\n]+\n?', '', cleaned_content, flags=re.MULTILINE)
        
        # 清理多余的空行
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        return cleaned_content.strip(), images
        
    except Exception as e:
        print(f"处理文本时出现错误: {str(e)}")
        return None, []

def txt_to_epub_with_formatting(txt_path, epub_path, article_copier_path, image_dir):
    try:
        # 获取清理后的内容和图片
        content, images = clean_and_format_text(txt_path, article_copier_path, image_dir)
        if not content:
            return False
            
        print(f"\n开始创建EPUB: {epub_path}")
        print(f"图片数量: {len(images)}")
        
        # 创建epub书籍
        book = epub.EpubBook()
        
        # 设置元数据
        book.set_identifier('id123456')
        book.set_title(os.path.splitext(os.path.basename(txt_path))[0])
        book.set_language('zh-CN')
        
        # 将换行转换为HTML段落标签并处理图片
        html_content = ''
        image_items = {}  # 使用字典存储图片项
        
        # 将内容分割成段落
        paragraphs = content.split('\n\n')
        
        # 处理段落和图片
        for paragraph in paragraphs:
            if paragraph.strip():
                if '--IMAGE_PLACEHOLDER_' in paragraph:
                    # 从占位符中提取图片文件名
                    img_filename = paragraph.replace('--IMAGE_PLACEHOLDER_', '').replace('--', '').strip()
                    img_path = os.path.join(image_dir, img_filename)
                    print(f"\n处理图片: {img_filename}")
                    print(f"图片路径: {img_path}")
                    print(f"图片存在: {os.path.exists(img_path)}")
                    
                    if os.path.exists(img_path):
                        if img_filename not in image_items:
                            # 创建图片项
                            img_id = f'image_{len(image_items)}'
                            try:
                                with open(img_path, 'rb') as img_file:
                                    image_content = img_file.read()
                                print(f"成功读取图片内容: {len(image_content)} bytes")
                                image_item = epub.EpubItem(
                                    uid=img_id,
                                    file_name=f'images/{img_filename}',
                                    media_type='image/jpeg',
                                    content=image_content
                                )
                                image_items[img_filename] = image_item
                                print("成功创建图片项")
                            except Exception as e:
                                print(f"处理图片时出错: {str(e)}")
                                
                        # 添加图片和描述
                        html_content += f'''
                            <div class="image-container">
                                <img src="images/{img_filename}" alt="{img_filename}"/>
                                <p class="image-caption">{img_filename}</p>
                            </div>
                        '''
                else:
                    html_content += f'<p>{paragraph.replace("\n", "<br/>")}</p>\n'
        
        # 创建章节
        chapter = epub.EpubHtml(title='Content',
                               file_name='content.xhtml',
                               lang='zh-CN')
        
        # 添加CSS样式
        style = '''
            p {
                margin: 1em 0;
                line-height: 1.5;
            }
            .image-container {
                margin: 1em 0;
                text-align: center;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
            }
            .image-caption {
                font-size: 0.9em;
                font-style: italic;
                color: #666;
                margin-top: 0.5em;
                text-align: center;
            }
        '''
        css = epub.EpubItem(
            uid="style",
            file_name="style.css",
            media_type="text/css",
            content=style
        )
        
        book.add_item(css)
        chapter.add_item(css)
        
        # 添加图片到书籍
        for image_item in image_items.values():
            book.add_item(image_item)
        
        chapter.content = f'<html><head></head><body>{html_content}</body></html>'
        
        # 添加章节
        book.add_item(chapter)
        
        # 创建目录
        book.toc = (epub.Link('content.xhtml', 'Content', 'content'),)
        
        # 添加导航
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 定义阅读顺序
        book.spine = ['nav', chapter]
        
        # 生成epub
        epub.write_epub(epub_path, book, {})
        
        return True
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        return False

def process_all_files(directory, article_copier_path, image_dir):
    # 获取所有News_开头的txt文件
    txt_files = find_all_news_files(directory)
    
    if not txt_files:
        print(f"在 {directory} 目录下没有找到以News_开头的txt文件")
        return
    
    # 统计处理结果
    converted = 0
    skipped = 0
    failed = 0
    
    # 处理每个文件
    for txt_file in txt_files:
        epub_file = get_epub_path(txt_file)
        
        try:
            if needs_conversion(txt_file, epub_file):
                print(f"正在处理: {os.path.basename(txt_file)}")
                if txt_to_epub_with_formatting(txt_file, epub_file, article_copier_path, image_dir):
                    print(f"成功转换: {os.path.basename(txt_file)} -> {os.path.basename(epub_file)}")
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
    
    # 打印统计信息
    print("\n处理完成:")
    print(f"成功转换: {converted} 个文件")
    print(f"跳过处理: {skipped} 个文件")
    print(f"转换失败: {failed} 个文件")

if __name__ == "__main__":
    news_directory = "/Users/yanzhang/Documents/News/"
    article_copier_path = "/Users/yanzhang/Documents/News/article_copier.txt"  # 修改为实际路径
    image_dir = "/Users/yanzhang/Downloads/news_image"
    
    # 处理epub转换
    process_all_files(news_directory, article_copier_path, image_dir)
    
    # 移动TodayCNH_文件
    move_cnh_file(news_directory)