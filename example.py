#!/usr/bin/env python3
"""
燕山大学锐捷V2网络认证工具使用示例

这个脚本展示了如何在Python代码中使用锐捷客户端
"""

import os
import sys
from ruijie_client import RuijieClient
from config import get_error_message, print_status_info, print_account_info


def example_check_status():
    """示例：检查登录状态"""
    print("=== 检查登录状态 ===")
    
    client = RuijieClient(verbose=True)
    
    try:
        is_logged_in, info = client.check_login_status()
        
        if is_logged_in:
            print("当前状态：已登录")
            print_status_info(info)
        else:
            print("当前状态：未登录")
            if info:
                print(f"重定向URL: {info}")
        
        return is_logged_in
        
    except Exception as e:
        print(f"检查状态失败: {get_error_message(e)}")
        return False


def example_login():
    """示例：登录到网络"""
    print("\n=== 登录示例 ===")
    
    # 从环境变量获取凭据
    username = os.getenv('RUIJIE_USERNAME')
    password = os.getenv('RUIJIE_PASSWORD')
    
    if not username or not password:
        print("请设置环境变量 RUIJIE_USERNAME 和 RUIJIE_PASSWORD")
        return False
    
    client = RuijieClient(verbose=True)
    
    try:
        success = client.login(username, password)
        if success:
            print("登录成功！")
            return True
        else:
            print("登录失败")
            return False
            
    except Exception as e:
        print(f"登录失败: {get_error_message(e)}")
        return False


def example_get_account_info():
    """示例：获取账户信息"""
    print("\n=== 获取账户信息 ===")
    
    client = RuijieClient(verbose=True)
    
    try:
        # 检查是否已登录
        is_logged_in, user_info = client.check_login_status()
        
        if not is_logged_in:
            print("未登录，无法获取账户信息")
            return False
        
        # 获取会话信息
        session_info = client.redirect_to_portal()
        
        # 获取账户信息
        account_info = client.get_account_info(session_info)
        
        # 显示信息
        print_status_info(user_info)
        print()
        print_account_info(account_info)
        
        return True
        
    except Exception as e:
        print(f"获取账户信息失败: {get_error_message(e)}")
        return False


def example_logout():
    """示例：登出"""
    print("\n=== 登出示例 ===")
    
    client = RuijieClient(verbose=True)
    
    try:
        success = client.logout()
        if success:
            print("登出成功！")
            return True
        else:
            print("登出失败")
            return False
            
    except Exception as e:
        print(f"登出失败: {get_error_message(e)}")
        return False


def main():
    """主函数"""
    print("燕山大学锐捷V2网络认证工具 - Python API 使用示例")
    print("=" * 50)
    
    # 1. 检查当前状态
    is_logged_in = example_check_status()
    
    # 2. 如果未登录，尝试登录
    if not is_logged_in:
        print("\n检测到未登录状态，尝试登录...")
        login_success = example_login()
        if not login_success:
            print("登录失败，退出示例")
            return
    
    # 3. 获取账户信息
    example_get_account_info()
    
    # 4. 询问是否登出
    try:
        choice = input("\n是否要登出？(y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            example_logout()
    except (KeyboardInterrupt, EOFError):
        print("\n示例结束")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n示例被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n示例执行出错: {e}")
        sys.exit(1)
