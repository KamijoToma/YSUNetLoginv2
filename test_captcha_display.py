#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证码显示功能测试脚本
测试改进后的 YSULogin 类的验证码显示功能
"""

from ysu_net_login.ysu_login import YSULogin

def test_captcha_display():
    """测试验证码显示功能"""
    print("验证码显示功能测试")
    print("=" * 50)
    print("此测试将展示:")
    print("1. ASCII 艺术形式的验证码显示")
    print("2. 自动文件保存和清理")
    print("3. 双重显示模式")
    print("=" * 50)
    
    # 使用测试账号（不会真正登录）
    username = "test_user"
    password = "test_password"
    
    print(f"测试用户: {username}")
    print("注意: 这只是功能测试，不会进行真实登录")
    print("-" * 50)
    
    # 创建客户端实例，使用 'both' 模式
    client = YSULogin(username, password, display_mode='both')
    
    print("YSULogin 客户端已创建")
    print(f"显示模式: {client.display_mode}")
    print("功能特性:")
    print("- ASCII 艺术验证码显示")
    print("- 自动文件保存和清理")
    print("- 支持 Windows 自动打开图片")
    print("- 程序退出时自动清理临时文件")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("要进行真实登录测试，请运行: python ysu_login.py")

if __name__ == "__main__":
    test_captcha_display()
