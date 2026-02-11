import os
import sys
from typing import Optional, Dict, Any


class Config:
    """配置管理类"""
    
    # 预定义的服务映射（解决中文输入问题）
    SERVICE_MAPPING = {
        "campus": "校园网",
        "unicom": "中国联通", 
        "telecom": "中国电信",
        "mobile": "中国移动",
        "1": "校园网",
        "2": "中国联通",
        "3": "中国电信", 
        "4": "中国移动"
    }
    
    def __init__(self):
        self.username = None
        self.password = None
        self.proxies = {}
        self.verbose = False
        self.service = "校园网"
        self.list_services = False
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        self.username = os.getenv('RUIJIE_USERNAME')
        self.password = os.getenv('RUIJIE_PASSWORD')
        
        # 代理配置
        http_proxy = os.getenv('RUIJIE_HTTP_PROXY') or os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('RUIJIE_HTTPS_PROXY') or os.getenv('HTTPS_PROXY')
        
        if http_proxy or https_proxy:
            self.proxies = {}
            if http_proxy:
                self.proxies['http'] = http_proxy
            if https_proxy:
                self.proxies['https'] = https_proxy
        
        # 详细输出
        self.verbose = os.getenv('RUIJIE_VERBOSE', '').lower() in ('1', 'true', 'yes')
        
        # 服务名称
        self.service = os.getenv('RUIJIE_SERVICE', '校园网')
    
    def update_from_args(self, args):
        """从命令行参数更新配置"""
        if hasattr(args, 'username') and args.username:
            self.username = args.username
        if hasattr(args, 'password') and args.password:
            self.password = args.password
        if hasattr(args, 'verbose') and args.verbose:
            self.verbose = args.verbose
        if hasattr(args, 'service') and args.service:
            self.service = args.service
        
        # 代理配置
        if hasattr(args, 'proxy') and args.proxy:
            proxy_url = args.proxy
            self.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
    
    def get_credentials_interactive(self):
        """交互式获取用户凭据"""
        if not self.username:
            try:
                self.username = input("Username: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                sys.exit(1)
        
        if not self.password:
            try:
                import getpass
                self.password = getpass.getpass("Password: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                sys.exit(1)
    
    def validate_credentials(self):
        """验证凭据是否完整"""
        return bool(self.username and self.password)
    
    def get_client_config(self):
        """获取客户端配置"""
        return {
            'proxies': self.proxies,
            'verbose': self.verbose
        }


def get_error_message(exception):
    """
    将异常转换为用户友好的错误消息
    
    Args:
        exception: 异常对象
        
    Returns:
        str: 用户友好的错误消息
    """
    error_msg = str(exception).lower()
    
    # 网络相关错误
    if 'connection' in error_msg or 'timeout' in error_msg:
        return "Network connection failed. Please check your internet connection."
    
    # 认证相关错误
    if 'authentication failed' in error_msg or 'cas' in error_msg:
        return f"Authentication failed. Detail: {error_msg}"
    
    # API相关错误
    if 'api error' in error_msg:
        return f"Server error: {exception}"
    
    # 门户重定向错误
    if 'portal redirection failed' in error_msg:
        return "Portal access failed. You may not be connected to the campus network."
    
    # CAS重定向错误
    if 'cas redirection failed' in error_msg:
        return "CAS authentication failed. Please try again."
    
    # 验证码相关错误
    if 'captcha' in error_msg or '验证码' in error_msg:
        return "Captcha verification failed. Please try again."
    
    # 默认错误消息
    return f"Operation failed: {exception}"


def print_status_info(user_info):
    """
    打印用户状态信息
    
    Args:
        user_info: 用户信息字典
    """
    portal_info = user_info.get("portalOnlineUserInfo", {})
    online_info = user_info.get("onlineUser", {})
    
    username = portal_info.get("userName") or portal_info.get("userId")
    service = portal_info.get("service")
    user_ip = portal_info.get("userIp")
    login_time = online_info.get("authenticationTime")
    location = online_info.get("nodePhysicalLocation")
    
    if username:
        print(f"Online: {username}", end="")
        if service:
            print(f" ({service})", end="")
        print()
        
        if user_ip:
            print(f"IP: {user_ip}")
        if login_time:
            print(f"Login Time: {login_time}")
        if location:
            print(f"Location: {location}")
    else:
        print("Status information unavailable")


def print_account_info(account_info):
    """
    打印账户信息
    
    Args:
        account_info: 账户信息字典
    """
    if not account_info:
        print("Account information unavailable")
        return
    
    print("Account Information:")
    
    # 显示基本信息
    basic_fields = {
        "name": "Name",
        "service": "Service", 
        "allowMab": "MAB Allowed",
        "nosenseEnable": "Nosense Enabled",
        "goLink": "Portal URL"
    }
    
    for key, label in basic_fields.items():
        if key in account_info and account_info[key] is not None:
            value = account_info[key]
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            print(f"  {label}: {value}")
    
    # 显示账户详细信息（动态处理）
    if account_info.get("accountInfo") and isinstance(account_info["accountInfo"], list):
        print("  Details:")
        for detail in account_info["accountInfo"]:
            if isinstance(detail, dict):
                title = detail.get("title", "")
                content = detail.get("content", "")
                if title and content:
                    print(f"    {title}: {content}")
    
    # 显示其他字段（排除已处理的和不重要的字段）
    excluded_fields = {"name", "service", "allowMab", "nosenseEnable", "goLink", "accountInfo", "portalSuccessUrl"}
    for key, value in account_info.items():
        if key not in excluded_fields and value is not None and value != "":
            print(f"  {key}: {value}")


def print_services_list(services_data):
    """
    打印可用服务列表
    
    Args:
        services_data: 服务数据字典
    """
    if not services_data:
        print("No services available")
        return
    
    print("Available Services:")
    
    # 从服务数据中提取服务列表
    services = []
    if isinstance(services_data, dict):
        # 尝试从不同可能的字段中获取服务列表
        if 'services' in services_data:
            services = services_data['services']
        elif 'serviceList' in services_data:
            services = services_data['serviceList']
        elif 'data' in services_data:
            services = services_data['data']
        else:
            # 如果没有找到标准字段，尝试查找包含服务信息的字段
            for key, value in services_data.items():
                if isinstance(value, list) and value:
                    services = value
                    break
    elif isinstance(services_data, list):
        services = services_data
    
    if not services:
        print("  No services found in response")
        return
    
    # 显示服务列表
    for i, service in enumerate(services, 1):
        if isinstance(service, str):
            print(f"  {i}. {service}")
        elif isinstance(service, dict):
            service_name = service.get('name') or service.get('serviceName') or service.get('service') or str(service)
            print(f"  {i}. {service_name}")
        else:
            print(f"  {i}. {service}")
    
    # 显示快捷映射
    print("\nQuick selection (for non-Chinese terminals):")
    print("  campus or 1 -> 校园网")
    print("  unicom or 2 -> 中国联通") 
    print("  telecom or 3 -> 中国电信")
    print("  mobile or 4 -> 中国移动")


def resolve_service_name(service_input, config):
    """
    解析服务名称，支持英文别名和数字选择
    
    Args:
        service_input: 用户输入的服务名称
        config: 配置对象
        
    Returns:
        str: 解析后的服务名称
    """
    if not service_input:
        return config.service
    
    # 直接返回中文服务名
    if service_input in ["校园网", "中国联通", "中国电信", "中国移动"]:
        return service_input
    
    # 从映射表中查找
    service_lower = service_input.lower()
    if service_lower in config.SERVICE_MAPPING:
        return config.SERVICE_MAPPING[service_lower]
    
    # 如果没有找到映射，返回原始输入
    return service_input


def interactive_service_selection(services_data):
    """
    交互式服务选择
    
    Args:
        services_data: 服务数据
        
    Returns:
        str: 选择的服务名称
    """
    print_services_list(services_data)
    
    try:
        choice = input("\nPlease select a service (number/name/alias): ").strip()
        
        # 如果是数字选择
        if choice.isdigit():
            choice_num = int(choice)
            
            # 从预定义映射中选择
            if 1 <= choice_num <= 4:
                service_names = ["校园网", "中国联通", "中国电信", "中国移动"]
                return service_names[choice_num - 1]
            
            # 从实际服务列表中选择
            services = []
            if isinstance(services_data, dict):
                for key, value in services_data.items():
                    if isinstance(value, list) and value:
                        services = value
                        break
            elif isinstance(services_data, list):
                services = services_data
            
            if 1 <= choice_num <= len(services):
                service = services[choice_num - 1]
                if isinstance(service, str):
                    return service
                elif isinstance(service, dict):
                    return service.get('name') or service.get('serviceName') or service.get('service') or str(service)
        
        # 使用resolve_service_name处理其他输入
        config = Config()  # 临时配置对象
        return resolve_service_name(choice, config)
        
    except (KeyboardInterrupt, EOFError):
        print("\nSelection cancelled, using default service: 校园网")
        return "校园网"
