from PIL import Image
import os

def vertically_concatenate_images(input_dir, output_dir, images_per_file=20, separator_height=10):
    # 获取输入目录中的所有PNG和JPEG文件并按名称排序
    image_extensions = ('.png', '.jpg', '.jpeg')
    image_paths = sorted([os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                          if f.lower().endswith(image_extensions)])
    
    if not image_paths:
        print("没有找到PNG或JPEG文件。")
        return

    # 将图片路径分组，每组20张
    image_groups = [image_paths[i:i+images_per_file] for i in range(0, len(image_paths), images_per_file)]

    for group_index, group in enumerate(image_groups):
        # 打开当前组的所有图片
        images = [Image.open(path) for path in group]
        
        # 计算总高度（包括分隔条）和最大宽度
        total_height = sum(img.height for img in images) + separator_height * (len(images) - 1)
        max_width = max(img.width for img in images)
        
        # 创建一个新的空白图像
        result_image = Image.new('RGB', (max_width, total_height), color='black')
        
        # 垂直拼接图片，并在每两张图片之间添加黑色分隔条
        y_offset = 0
        for i, img in enumerate(images):
            result_image.paste(img, (0, y_offset))
            y_offset += img.height
            
            # 如果不是最后一张图片，添加分隔条
            if i < len(images) - 1:
                y_offset += separator_height
        
        # 生成输出文件路径
        output_filename = f"concatenated_result_{group_index+1}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        # 保存结果
        result_image.save(output_path)
        print(f"第 {group_index+1} 组图片已拼接并保存到 {output_path}")

# 使用示例
if __name__ == "__main__":
    input_directory = "/Users/yanzhang/Movies/Subtitle"
    output_directory = "/Users/yanzhang/Downloads"
    
    vertically_concatenate_images(input_directory, output_directory)