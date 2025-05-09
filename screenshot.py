import os
import cv2
import sys
import time
import pyautogui
import numpy as np
from time import sleep
from PIL import ImageGrab
from typing import List, Tuple, Optional

class ScreenDetector:
    def __init__(self, template_names: str | List[str], clickValue: bool = False, 
                 Opposite: bool = False, x_offset: Optional[int] = None, 
                 y_offset: Optional[int] = None, nth_match: int = 1):
        self.templates = []
        self.clickValue = clickValue
        self.Opposite = Opposite # 注意：Opposite 参数在 run1 和 run2 中似乎没有直接使用其布尔值来反转逻辑，而是用来选择 run1 还是 run2
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.nth_match = max(1, nth_match) # 确保 nth_match 至少为 1
        
        # 存储模板名称列表，用于判断是否有多个模板
        if isinstance(template_names, str):
            self.template_name_list = [name.strip() for name in template_names.split(',')]
        else:
            self.template_name_list = template_names
        
        self._load_templates(self.template_name_list) # 使用 self.template_name_list

    def _load_templates(self, template_names_list: List[str]) -> None: # 参数名修改以更清晰
        """优化的模板加载方法"""
        for template_name in template_names_list:
            template_path = os.path.join('/Users/yanzhang/Documents/python_code/Resource', template_name)
            try:
                # 使用 with self._load_template(template_path) as template:
                # cv2.imread 返回的 numpy 数组不需要特别的资源释放，所以 contextmanager 可能不是必须的
                # 但如果未来 _load_template 做了更复杂的事情，它仍然有用
                template_img = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template_img is None:
                    print(f"警告: 模板图片未能正确读取于路径 {template_path}")
                    continue
                self.templates.append((template_name, template_img))
            except FileNotFoundError as e: # cv2.imread 不会抛 FileNotFoundError, 而是返回 None
                print(f"Error during template loading (should not happen if imread fails): {e}")
                continue
            except Exception as e: # 捕获其他可能的cv2错误
                print(f"An unexpected error occurred while loading template {template_name}: {e}")
                continue

    def capture_screen(self) -> np.ndarray:
        """优化的屏幕捕获方法"""
        # ImageGrab.grab() 已经是上下文管理器了，但这里显式使用 with 更好
        with ImageGrab.grab() as screenshot:
            # 直接转换为numpy数组并更改颜色空间
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def find_images_on_screen(self, threshold: float = 0.9) -> Tuple[Optional[str], Optional[Tuple[int, int]], Optional[Tuple[int, int, int]]]:
        """
        在屏幕上查找图像。
        按Y轴优先（从上到下），然后X轴优先（从左到右）的顺序，
        返回第 nth_match 个匹配项。
        """
        screen = self.capture_screen() # 捕获一次屏幕用于所有模板的比较
        
        # 遍历每个模板
        for template_name, template in self.templates:
            if template is None: # 以防万一有模板加载失败但仍然在列表中
                continue

            # TM_CCOEFF_NORMED 范围是 -1 到 1，但通常我们寻找接近 1 的值
            # 对于一些灰度图或颜色不敏感的匹配，阈值可能需要调整
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            
            # 获取所有得分高于阈值的位置
            # locations[0] 是 y 坐标数组, locations[1] 是 x 坐标数组
            locations_y, locations_x = np.where(result >= threshold)
            
            if locations_y.size > 0:
                # 将坐标 (y,x) 和对应的得分组合起来
                current_matches_for_this_template = []
                for i in range(locations_x.size):
                    x, y = locations_x[i], locations_y[i]
                    current_matches_for_this_template.append(
                        ((x, y), template_name, template.shape) 
                    )
                
                # 排序：主键是 Y 坐标 (loc[1])，次键是 X 坐标 (loc[0])
                current_matches_for_this_template.sort(key=lambda item: (item[0][1], item[0][0]))
                
                # 如果找到了足够的匹配项
                if len(current_matches_for_this_template) >= self.nth_match:
                    # 获取排序后的第 nth_match 个匹配项
                    selected_match = current_matches_for_this_template[self.nth_match - 1]
                    match_location = selected_match[0]    # (x,y)
                    match_template_name = selected_match[1] # 'template_name'
                    match_shape = selected_match[2]       # (h,w,c)
                    return match_template_name, match_location, match_shape
        
        # 如果循环完所有模板都没有找到满足条件的第 nth_match 个匹配
        return None, None, None

    def _perform_click(self, location: Tuple[int, int], shape: Tuple[int, int, int]) -> None:
        """优化的点击操作"""
        center_x = (location[0] + shape[1] // 2) // 2
        center_y = (location[1] + shape[0] // 2) // 2
        
        if self.x_offset is not None:
            center_x += self.x_offset
        if self.y_offset is not None:
            center_y += self.y_offset
        
        pyautogui.click(center_x, center_y)

    def run1(self) -> str:
        """优化的运行方法1，返回找到的图片名"""
        timeout = time.time() + 590 # 约 9.8 分钟
        
        while time.time() < timeout:
            template_name, location, shape = self.find_images_on_screen()
            
            if location and template_name and shape: #确保所有值都有效
                if self.clickValue:
                    self._perform_click(location, shape)
                print(f"找到图片 {template_name} 位置: {location}")

                # 如果有多个模板名被传入构造函数，打印特定格式信息
                if len(self.template_name_list) > 1 : # 或者 self.templates
                    print(f"FOUND_IMAGE:{template_name}")
                return template_name # 返回找到的第一个符合 nth_match 条件的模板名         
            
            # print("未找到任何目标图片，继续监控...") # 频繁打印可能过多，可以考虑减少频率
            sleep(1) # 等待1秒再试
        
        print(f"在 {590} 秒内未找到图片，退出程序。")
        return "TIMEOUT"

    def run2(self) -> None:
        """优化的运行方法2 - 持续查找并滚动，直到找不到"""
        while True:
            template_name, location, shape = self.find_images_on_screen() # 这里nth_match仍然生效
            
            if not location: # 如果没找到 (或者 template_name/shape 为 None)
                print("未找到图片，停止滚动并退出run2。")
                break # 退出 while 循环
            
            # 如果找到了，则执行滚动
            # 注意：如果 clickValue 为 True，这里不会自动点击，run2 似乎只负责滚动
            # 如果希望 run2 也点击，需要添加 self._perform_click 调用
            pyautogui.scroll(-120) # 向下滚动
            print(f"找到图片 {template_name} 位置: {location}，已滚动。")
            sleep(1) # 操作后稍作等待

def parse_args() -> Tuple[str | List[str], bool, bool, Optional[int], Optional[int], int]:
    """参数解析函数"""
    if len(sys.argv) < 4:
        print("用法: python a.py <image_name1[,image_name2,...]> <clickValue:true|false> <Opposite:true|false> [x_offset] [y_offset] [nth_match]")
        sys.exit(1)

    image_names_str = sys.argv[1]
    # 支持单个或多个逗号分隔的图片名
    # image_names = [name.strip() for name in image_names_str.split(',')] if ',' in image_names_str else image_names_str

    clickValue = sys.argv[2].lower() == 'true'
    Opposite = sys.argv[3].lower() == 'true' # 这个参数决定调用 run1 还是 run2

    x_offset: Optional[int] = None
    y_offset: Optional[int] = None
    nth_match: int = 1 # 默认 nth_match 为 1

    remaining_args = sys.argv[4:]
    
    try:
        if len(remaining_args) >= 1 and remaining_args[0]:
            # 尝试将第一个可选参数作为 nth_match (如果它是唯一的数字参数)
            # 或作为 x_offset (如果后面还有 y_offset)
            # 为了明确，最好要求 nth_match 是最后一个参数或有固定位置
            # 当前逻辑：如果只有一个额外参数，它是 nth_match
            # 如果有两个，是 x_offset, y_offset
            # 如果有三个，是 x_offset, y_offset, nth_match
            if len(remaining_args) == 1: # nth_match
                nth_match = int(remaining_args[0])
            elif len(remaining_args) == 2: # x_offset, y_offset
                x_offset = int(remaining_args[0]) if remaining_args[0] else None
                y_offset = int(remaining_args[1]) if remaining_args[1] else None
            elif len(remaining_args) >= 3: # x_offset, y_offset, nth_match
                x_offset = int(remaining_args[0]) if remaining_args[0] else None
                y_offset = int(remaining_args[1]) if remaining_args[1] else None
                nth_match = int(remaining_args[2]) if remaining_args[2] else 1
    
    except ValueError as e:
        print(f"参数值无效: {e}. 请确保偏移量和 nth_match 是整数。")
        sys.exit(1)
    except IndexError:
        # 正常情况，意味着没有提供所有可选参数
        pass
        
    # image_names 可以直接传递字符串，构造函数会处理
    return image_names_str, clickValue, Opposite, x_offset, y_offset, nth_match

if __name__ == '__main__':
    args_tuple = parse_args() # (image_names_str, clickValue, Opposite, x_offset, y_offset, nth_match)
    
    # print(f"Parsed args: {args_tuple}") # 调试用

    # 创建 ScreenDetector 实例
    detector = ScreenDetector(
        template_names=args_tuple[0],
        clickValue=args_tuple[1],
        Opposite=args_tuple[2], # 这个参数主要用于选择 run1 还是 run2
        x_offset=args_tuple[3],
        y_offset=args_tuple[4],
        nth_match=args_tuple[5]
    )
    
    try:
        if args_tuple[2]:  # Opposite is True, run run2
            detector.run2()
        else: # Opposite is False, run run1
            detector.run1()
    finally:
        # 清理模板列表中的图像数据（如果需要手动管理，但cv2图像通常由GC处理）
        # self.templates.clear() 实际上不需要，因为 detector 实例会被销毁
        # del detector # 也不需要显式删除
        print("程序执行完毕。")