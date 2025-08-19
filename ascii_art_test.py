#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASCII Art 验证码显示测试脚本
测试将验证码图片转换为 ASCII 字符在终端显示的效果
"""

import os
from PIL import Image

class ASCIIArtConverter:
    def __init__(self):
        # 不同密度的字符集，从密集到稀疏
        self.ascii_chars_dense = "@%#*+=-:. "
        self.ascii_chars_standard = "@#S%?*+;:,. "
        self.ascii_chars_extended = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
        
    def image_to_ascii(self, image_path, width=80, char_set="standard"):
        """
        将图像转换为 ASCII 字符
        
        Args:
            image_path: 图像文件路径
            width: ASCII 输出宽度
            char_set: 字符集类型 ("dense", "standard", "extended")
        
        Returns:
            ASCII 字符串
        """
        try:
            # 选择字符集
            if char_set == "dense":
                ascii_chars = self.ascii_chars_dense
            elif char_set == "extended":
                ascii_chars = self.ascii_chars_extended
            else:
                ascii_chars = self.ascii_chars_standard
            
            # 打开图像
            image = Image.open(image_path)
            
            # 获取原始尺寸
            orig_width, orig_height = image.size
            
            # 计算新的高度，保持宽高比
            aspect_ratio = orig_height / orig_width
            height = int(aspect_ratio * width * 0.55)  # 0.55 用于补偿字符高宽比
            
            # 调整图像大小
            image = image.resize((width, height))
            
            # 转换为灰度
            image = image.convert('L')
            
            # 获取像素数据
            pixels = image.getdata()
            
            # 将像素映射到 ASCII 字符
            ascii_str = ""
            for i, pixel in enumerate(pixels):
                # 将像素值 (0-255) 映射到字符索引
                char_index = int(pixel * (len(ascii_chars) - 1) / 255)
                ascii_str += ascii_chars[char_index]
                
                # 每行结束时添加换行符
                if (i + 1) % width == 0:
                    ascii_str += "\n"
            
            return ascii_str, (orig_width, orig_height), (width, height)
            
        except Exception as e:
            return f"转换失败: {e}", None, None

def test_ascii_conversion():
    """测试 ASCII 转换效果"""
    converter = ASCIIArtConverter()
    image_path = "captcha.jpg"
    
    if not os.path.exists(image_path):
        print(f"错误: 找不到测试图片 {image_path}")
        print("请确保项目目录中有 captcha.jpg 文件")
        return
    
    print("=" * 80)
    print("ASCII Art 验证码显示测试")
    print("=" * 80)
    
    # 测试不同的参数组合
    test_configs = [
        {"width": 60, "char_set": "standard", "name": "标准字符集 (60宽)"},
        {"width": 80, "char_set": "standard", "name": "标准字符集 (80宽)"},
        {"width": 60, "char_set": "dense", "name": "密集字符集 (60宽)"},
        {"width": 80, "char_set": "extended", "name": "扩展字符集 (80宽)"},
    ]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{i}. {config['name']}")
        print("-" * 60)
        
        ascii_art, orig_size, new_size = converter.image_to_ascii(
            image_path, 
            width=config["width"], 
            char_set=config["char_set"]
        )
        
        if orig_size:
            print(f"原始尺寸: {orig_size[0]}x{orig_size[1]}")
            print(f"ASCII尺寸: {new_size[0]}x{new_size[1]}")
            print()
            print(ascii_art)
        else:
            print(ascii_art)
        
        print("-" * 60)
        
        # 询问用户是否继续
        if i < len(test_configs):
            try:
                input("按 Enter 继续下一个测试，或 Ctrl+C 退出...")
            except KeyboardInterrupt:
                print("\n测试已中断")
                break
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("请评估 ASCII Art 显示效果是否足够清晰来识别验证码内容。")
    print("=" * 80)

if __name__ == "__main__":
    test_ascii_conversion()
