#!/usr/bin/env python3
"""
燕山大学锐捷V2网络认证命令行工具

Usage:
    python ruijie_cli.py login [--username USERNAME] [--password PASSWORD]
    python ruijie_cli.py logout
    python ruijie_cli.py status
    python ruijie_cli.py info
    python ruijie_cli.py --help

Author: SkyRain <admin@misakacloud.net>
"""

import sys
import argparse
from .ruijie_client import RuijieClient
from .config import Config, get_error_message, print_status_info, print_account_info, resolve_service_name, interactive_service_selection


def cmd_login(args, config):
    """执行登录命令"""
    # 更新配置
    config.update_from_args(args)
    
    # 如果没有提供凭据，交互式获取
    if not config.validate_credentials():
        config.get_credentials_interactive()
    
    # 创建客户端
    client = RuijieClient(**config.get_client_config())
    
    try:
        # 处理服务选择
        service_name = config.service
        
        # 检查是否需要列出服务或交互式选择
        if hasattr(args, 'service') and args.service is not None:
            if args.service == "":
                # -s 选项没有提供参数，列出可用服务并让用户选择
                print("Fetching available services...")
                services_data = client.get_available_services(config.username, config.password)
                service_name = interactive_service_selection(services_data)
                # 清空 Cookie 以避免重复登陆
                client.client.cookies.clear()
            else:
                # 解析用户提供的服务名称
                service_name = resolve_service_name(args.service, config)
        
        # 执行登录
        success = client.login(config.username, config.password, service_name)
        if success:
            print(f"Login successful to service: {service_name}")
            return 0
        else:
            print("Login failed.")
            return 1
    except Exception as e:
        print(f"Error: {get_error_message(e)}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_logout(args, config):
    """执行登出命令"""
    config.update_from_args(args)
    
    client = RuijieClient(**config.get_client_config())
    
    try:
        success = client.logout()
        if success:
            print("Logout successful.")
            return 0
        else:
            print("Logout failed.")
            return 1
    except Exception as e:
        print(f"Error: {get_error_message(e)}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_status(args, config):
    """检查登录状态"""
    config.update_from_args(args)
    
    client = RuijieClient(**config.get_client_config())
    
    try:
        is_logged_in, info = client.check_login_status()
        
        if is_logged_in:
            print_status_info(info)
            return 0
        else:
            print("Offline")
            return 0
    except Exception as e:
        print(f"Error: {get_error_message(e)}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cmd_info(args, config):
    """获取账户信息"""
    config.update_from_args(args)
    
    client = RuijieClient(**config.get_client_config())
    
    try:
        # 首先检查是否已登录
        is_logged_in, user_info = client.check_login_status()
        
        if not is_logged_in:
            print("Error: Not logged in. Please login first.")
            return 1
        
        # 获取会话信息
        session_info = client.redirect_to_portal()
        
        # 获取账户信息
        account_info = client.get_account_info(session_info)
        
        # 打印用户状态信息
        print_status_info(user_info)
        print()
        
        # 打印账户信息
        print_account_info(account_info)
        
        return 0
        
    except Exception as e:
        print(f"Error: {get_error_message(e)}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return 1


def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="燕山大学锐捷V2网络认证命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s login -u 1145141919810 -p mypassword
  %(prog)s login  # Interactive login
  %(prog)s status
  %(prog)s logout
  %(prog)s info

Environment Variables:
  RUIJIE_USERNAME     Default username
  RUIJIE_PASSWORD     Default password
  RUIJIE_VERBOSE      Enable verbose output (1/true/yes)
  RUIJIE_SERVICE      Service name (default: 校园网)
  HTTP_PROXY          HTTP proxy URL
  HTTPS_PROXY         HTTPS proxy URL
        """
    )
    
    # 全局选项
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--proxy', metavar='URL',
                       help='Proxy URL (e.g., socks5://127.0.0.1:1080)')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # login 命令
    login_parser = subparsers.add_parser('login', help='Login to network')
    login_parser.add_argument('-u', '--username', metavar='USERNAME',
                             help='Username for authentication')
    login_parser.add_argument('-p', '--password', metavar='PASSWORD',
                             help='Password for authentication')
    login_parser.add_argument('-s', '--service', metavar='SERVICE', nargs='?', const='',
                             help='Service name. Use -s without argument to list available services. Supports aliases: campus/1=校园网, unicom/2=中国联通, telecom/3=中国电信, mobile/4=中国移动')
    
    # logout 命令
    logout_parser = subparsers.add_parser('logout', help='Logout from network')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='Check login status')
    
    # info 命令
    info_parser = subparsers.add_parser('info', help='Show account information')
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1
    
    # 创建配置对象
    config = Config()
    
    # 根据命令执行相应操作
    if args.command == 'login':
        return cmd_login(args, config)
    elif args.command == 'logout':
        return cmd_logout(args, config)
    elif args.command == 'status':
        return cmd_status(args, config)
    elif args.command == 'info':
        return cmd_info(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
