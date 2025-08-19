import requests
import time
import functools
import inspect
from urllib.parse import urlparse, parse_qs
import ysu_login


class RuijieClient:
    """燕山大学锐捷V2网络认证客户端"""
    
    def __init__(self, proxies=None, verbose=False):
        """
        初始化锐捷客户端
        
        Args:
            proxies: 代理设置字典，格式如 {"http": "...", "https": "..."}
            verbose: 是否输出详细日志
        """
        self.client = requests.Session()
        self.proxies = proxies or {}
        self.verbose = verbose
        
        # 设置User-Agent
        self.client.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        })
        
        if self.proxies:
            self.client.proxies.update(self.proxies)
    
    def _log(self, message):
        """输出日志信息"""
        if self.verbose:
            print(f"[DEBUG] {message}")
    
    def _unwrap_response(self, response, json_response=False):
        """
        解包响应结果
        
        Args:
            response: requests.Response对象
            json_response: 是否需要JSON响应处理
            
        Returns:
            响应数据或抛出异常
        """
        response.raise_for_status()
        
        if json_response:
            data = response.json()
            if data.get("code") == 200:
                return data.get("data")
            raise ValueError(f"API error: {data.get('message')}")
        
        return response.json()
    
    def get_online_user_info(self, session_id='114514'):
        """
        获取当前在线用户信息
        
        Args:
            session_id: 会话ID，检查状态时可以使用默认值
            
        Returns:
            用户在线信息字典
        """
        timestamp = int(time.time() * 1000)
        url = f"https://auth1.ysu.edu.cn/eportal/adaptor/getOnlineUserInfo?sessionId={session_id}&{timestamp}&version=this%20is%20a%20git-commit"
        
        response = self.client.get(url, proxies=self.proxies)
        return self._unwrap_response(response, json_response=True)
    
    def redirect_to_portal(self, redirect_url='https://auth1.ysu.edu.cn/eportal/redirect.jsp?mode=history'):
        """
        重定向到门户网站获取会话信息
        
        Args:
            redirect_url: 重定向URL
            
        Returns:
            包含sessionId等参数的字典
        """
        resp = self.client.get(redirect_url, allow_redirects=True, proxies=self.proxies)
        
        # 处理JavaScript重定向
        if "location.href=" in resp.text:
            redirect_url_2 = resp.text.split("'")[1].split("'")[0]
            resp = self.client.get(redirect_url_2, allow_redirects=True, proxies=self.proxies)
        
        if "portal-main" not in resp.request.url:
            raise Exception(f"Portal redirection failed. Expected URL to contain 'portal-main', but got: {resp.request.url}")
        
        # 解析URL参数
        parsed_url = urlparse(resp.request.url)
        request_params = parse_qs(parsed_url.query)
        
        # 移除列表包装，只保留第一个值
        request_params = {k: v[0] for k, v in request_params.items()}
        
        return request_params
    
    def _get_current_node(self, session_info, flowKey='portal_auth'):
        """
        获取当前登录流程节点
        
        Args:
            session_info: 会话信息字典
            flowKey: 流程键
            
        Returns:
            当前节点信息
        """
        node_url = "https://auth1.ysu.edu.cn/eportal/workFlow/getCurrentNode"
        response = self.client.post(
            node_url,
            json={
                "sessionId": session_info['sessionId'],
                "flowKey": flowKey
            },
            proxies=self.proxies
        )
        
        node_resp = response.json()
        current_node = node_resp['data'].get('currentNodePath', 'Unknown')
        self._log(f"Current Node: {current_node}")
        
        return node_resp
    
    def sam_login(self, session_info):
        """
        执行SAM登录
        
        Args:
            session_info: 会话信息字典
            
        Returns:
            登录响应
        """
        session_id = session_info['sessionId']
        custom_page_id = session_info['customPageId']
        nas_ip = session_info['nasIp']
        user_ip = session_info['userIp']
        ssid = session_info['ssid']
        user_mac = session_info['userMac']
        
        sam_url = f"https://auth1.ysu.edu.cn/sam-sso/login?flowSessionId={session_id}&customPageId={custom_page_id}&preview=false&appType=normal&language=zh-CN&nasIp={nas_ip}&userIp={user_ip}&ssid={ssid}&userMac={user_mac}"
        
        resp = self.client.post(sam_url, json=session_info, proxies=self.proxies, allow_redirects=True)
        
        # 客户端重定向到YSU CAS服务器
        cas_redirect_url = "https://auth1.ysu.edu.cn/sam-sso/clientredirect?client_name=sidadapter&service=https://auth1.ysu.edu.cn/portal/entry/pc/authenticate;flowParams=undefined;from="
        resp = self.client.get(cas_redirect_url, allow_redirects=True, proxies=self.proxies)
        
        if "cer.ysu.edu.cn" not in resp.request.url and "ticket=" not in resp.request.url:
            raise Exception(f"CAS redirection failed. Expected redirect to CAS server or successful login, but got: {resp.request.url}")
        
        self._get_current_node(session_info)
        return resp
    
    def service_selection(self, session_info):
        """
        获取可用服务列表
        
        Args:
            session_info: 会话信息字典
            
        Returns:
            服务选择响应数据
        """
        service_url = "https://auth1.ysu.edu.cn/eportal/network/serviceSelection"
        response = self.client.post(service_url, json={
            "sessionId": session_info['sessionId']
        }, proxies=self.proxies)
        
        self._get_current_node(session_info)
        return self._unwrap_response(response, json_response=True)
    
    def service_login(self, session_info, service="校园网"):
        """
        登录到指定服务
        
        Args:
            session_info: 会话信息字典
            service: 服务名称
            
        Returns:
            服务登录响应
        """
        service_url = "https://auth1.ysu.edu.cn/eportal/network/serviceLogin"
        response = self.client.post(service_url, json={
            "sessionId": session_info['sessionId'],
            "service": service
        }, proxies=self.proxies)
        
        self._get_current_node(session_info)
        return response.json()
    
    def user_online(self, session_info):
        """
        检查用户是否在线
        
        Args:
            session_info: 会话信息字典
            
        Returns:
            用户在线状态数据
        """
        online_url = "https://auth1.ysu.edu.cn/eportal/network/userOnline"
        response = self.client.post(online_url, json={
            "sessionId": session_info['sessionId']
        }, proxies=self.proxies)
        
        return self._unwrap_response(response, json_response=True)
    
    def get_account_info(self, session_info):
        """
        获取账户信息
        
        Args:
            session_info: 会话信息字典
            
        Returns:
            账户信息数据
        """
        account_url = "https://auth1.ysu.edu.cn/eportal/operator/getAccountInfo"
        response = self.client.post(account_url, json={
            "sessionId": session_info['sessionId']
        }, proxies=self.proxies)
        
        return self._unwrap_response(response, json_response=True)
    
    def offline(self, session_info):
        """
        用户登出
        
        Args:
            session_info: 会话信息字典
            
        Returns:
            登出响应数据
        """
        offline_url = "https://auth1.ysu.edu.cn/eportal/network/offline"
        response = self.client.post(offline_url, json={
            "sessionId": session_info['sessionId']
        }, proxies=self.proxies)
        
        return self._unwrap_response(response, json_response=True)
    
    def check_login_status(self):
        """
        检查当前登录状态
        
        Returns:
            tuple: (is_logged_in, user_info_or_redirect_url)
        """
        try:
            user_info = self.get_online_user_info()
            redirect_url = user_info["portalOnlineUserInfo"].get("redirectUrl")
            
            if redirect_url:
                # 未登录
                return False, redirect_url
            else:
                # 已登录
                return True, user_info
        except Exception as e:
            self._log(f"Error checking login status: {e}")
            return False, None
    
    def get_available_services(self, username, password):
        """
        获取可用服务列表（不执行登录）
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            list: 可用服务列表
        """
        try:
            # 1. 检查当前状态
            is_logged_in, info = self.check_login_status()
            if is_logged_in:
                # 如果已登录，获取会话信息并查询服务
                session_info = self.redirect_to_portal()
                services = self.service_selection(session_info)
                return services
            
            # 2. 重定向到门户获取会话信息
            session_info = self.redirect_to_portal()
            self._log(f"Got session info: {session_info}")
            
            # 3. CAS登录
            cas_client = ysu_login.YSULogin(username, password, session=self.client, proxies=self.proxies)
            cas_result = cas_client.login()
            if not cas_result:
                raise Exception("CAS authentication failed")
            
            # 4. SAM登录
            self.sam_login(session_info)
            
            # 5. 获取服务列表
            services = self.service_selection(session_info)
            self._log(f"Available services: {services}")
            
            return services
            
        except Exception as e:
            if self.verbose:
                self._log(f"Get services failed: {e}")
            raise e

    def login(self, username, password, service="校园网"):
        """
        执行完整的登录流程
        
        Args:
            username: 用户名
            password: 密码
            service: 要登录的服务名称
            
        Returns:
            bool: 登录是否成功
        """
        try:
            # 1. 检查当前状态
            is_logged_in, info = self.check_login_status()
            if is_logged_in:
                self._log("Already logged in")
                return True
            
            # 2. 重定向到门户获取会话信息
            session_info = self.redirect_to_portal()
            self._log(f"Got session info: {session_info}")
            
            # 3. CAS登录
            cas_client = ysu_login.YSULogin(username, password, session=self.client, proxies=self.proxies)
            cas_result = cas_client.login()
            if not cas_result:
                raise Exception("CAS authentication failed")
            
            # 4. SAM登录
            self.sam_login(session_info)
            
            # 5. 获取服务列表
            services = self.service_selection(session_info)
            self._log(f"Available services: {services}")
            
            # 6. 登录到指定服务
            login_result = self.service_login(session_info, service)
            self._log(f"Service login result: {login_result}")
            
            # 7. 验证登录状态
            online_status = self.user_online(session_info)
            self._log(f"User online status: {online_status}")
            
            # 8. 检查认证结果
            if login_result.get('code') == 200 and login_result.get('data'):
                auth_result = login_result['data'].get('authResult')
                if auth_result == 'fail':
                    auth_message = login_result['data'].get('authMessage', 'Unknown authentication error')
                    raise Exception(f"Authentication failed: {auth_message}")
                elif auth_result != 'success':
                    raise Exception(f"Unexpected authentication result: {auth_result}")
            else:
                raise Exception(f"Invalid service login response: {login_result}")
            
            # 9. 检查在线状态
            if not online_status.get('online', False):
                error_message = online_status.get('message', 'User is not online after authentication')
                raise Exception(f"Login verification failed: {error_message}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                self._log(f"Login failed: {e}")
            raise e
    
    def logout(self):
        """
        执行登出操作
        
        Returns:
            bool: 登出是否成功
        """
        try:
            # 1. 检查当前状态
            is_logged_in, info = self.check_login_status()
            if not is_logged_in:
                self._log("Already logged out")
                return True
            
            # 2. 重定向到门户获取会话信息
            session_info = self.redirect_to_portal()
            self._log(f"Got session info for logout: {session_info}")
            
            # 3. 执行登出
            offline_result = self.offline(session_info)
            self._log(f"Offline result: {offline_result}")
            
            # 4. 验证登出状态
            final_status = self.user_online(session_info)
            self._log(f"Final user status: {final_status}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                self._log(f"Logout failed: {e}")
            raise e
