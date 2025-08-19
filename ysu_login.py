import requests
import base64
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from bs4 import BeautifulSoup
import urllib3

# 禁用 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class YSULogin:
    LOGIN_URL = "https://cer.ysu.edu.cn/authserver/login?service=https%3A%2F%2Fehall.ysu.edu.cn%2Flogin"
    CHECK_CAPTCHA_URL = "https://cer.ysu.edu.cn/authserver/checkNeedCaptcha.htl"
    CAPTCHA_URL = "https://cer.ysu.edu.cn/authserver/getCaptcha.htl"

    def __init__(self, username, password, session=None, proxies={}):
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.proxies = proxies
        # 模拟浏览器 User-Agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.lt = None
        self.execution = None
        self.salt = None
        self.cllt = None
        self.dllt = None
        self._eventId = None
        self.captcha = None

    def _random_string(self, length):
        chars = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
        return ''.join(random.choice(chars) for _ in range(length))

    def _encrypt_password(self, password, salt):
        """
        使用AES/CBC/PKCS7对密码进行加密，与JS端逻辑保持一致
        """
        prefix = self._random_string(64)
        iv = self._random_string(16).encode('utf-8')
        key = salt.strip().encode('utf-8')
        data_to_encrypt = (prefix + password).encode('utf-8')

        cipher = AES.new(key, AES.MODE_CBC, iv)

        # PKCS7 填充
        padded_data = pad(data_to_encrypt, AES.block_size)

        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')

    def _fetch_login_page(self):
        """
        访问登录页面，获取表单所需参数
        """
        try:
            resp = self.session.get(self.LOGIN_URL, verify=False, timeout=10, proxies=self.proxies)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 首先定位到账号密码登录的表单，以确保获取正确的参数
            form = soup.find('form', {'id': 'pwdFromId'})
            if not form:
                print("错误：未能找到ID为 'pwdFromId' 的登录表单。")
                return False

            self.lt = form.find('input', {'name': 'lt'}).get('value', '')
            self.execution = form.find('input', {'name': 'execution'}).get('value', '')
            self.salt = form.find('input', {'id': 'pwdEncryptSalt'}).get('value', '')
            self.cllt = form.find('input', {'name': 'cllt'}).get('value', 'userNameLogin')
            self.dllt = form.find('input', {'name': 'dllt'}).get('value', 'generalLogin')
            self._eventId = form.find('input', {'name': '_eventId'}).get('value', 'submit')

            if not all([self.execution, self.salt]):
                print("错误：未能从登录页面获取到所有必要的参数。")
                return False
            return True
        except requests.exceptions.RequestException as e:
            print(f"错误：访问登录页面失败: {e}")
            return False
        except (AttributeError, TypeError) as e:
            print(f"错误：解析登录页面失败: {e}")
            return False


    def _need_captcha(self):
        """
        检查是否需要输入验证码
        """
        try:
            resp = self.session.post(self.CHECK_CAPTCHA_URL, data={"username": self.username}, verify=False, timeout=5, proxies=self.proxies)
            resp.raise_for_status()
            data = resp.json()
            return data.get("isNeed", False)
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"警告：检查验证码失败，将不使用验证码登录。错误: {e}")
            return False

    def _fetch_captcha(self, save_path='captcha.jpg'):
        """
        获取验证码并由用户输入
        """
        try:
            resp = self.session.get(self.CAPTCHA_URL, verify=False, timeout=5, proxies=self.proxies)
            resp.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            print(f"请查看并输入验证码图片: {save_path}")
            self.captcha = input("请输入验证码: ")
        except requests.exceptions.RequestException as e:
            print(f"错误：获取验证码失败: {e}")


    def login(self):
        """
        执行登录操作
        """
        if not self._fetch_login_page():
            return False

        if self._need_captcha():
            self._fetch_captcha()
            if not self.captcha:
                print("错误：需要验证码但未输入。")
                return False

        enc_pwd = self._encrypt_password(self.password, self.salt)

        data = {
            "username": self.username,
            "password": enc_pwd,
            "captcha": self.captcha or "",
            "lt": self.lt,
            "execution": self.execution,
            "_eventId": self._eventId,
            "cllt": self.cllt,
            "dllt": self.dllt,
        }

        try:
            # 提交登录表单
            resp = self.session.post(self.LOGIN_URL, data=data, allow_redirects=False, verify=False, timeout=10, proxies=self.proxies)

            # 检查是否登录成功 (成功时通常是302重定向)
            if resp.status_code == 302 and 'Location' in resp.headers:
                location = resp.headers['Location']
                print(f"登录成功！正在跳转到: {location}")
                # 可以选择访问跳转后的页面来确认
                final_resp = self.session.get(location, verify=False, proxies=self.proxies)
                if "统一身份认证" not in final_resp.text:
                    print("确认登录成功。")
                    return True
                else:
                    print("登录似乎成功，但又跳转回了登录页，请检查。")
                    return False

            # 处理登录失败
            else:
                soup = BeautifulSoup(resp.text, 'html.parser')
                error_msg_span = soup.find('span', {'id': 'showErrorTip'})
                if error_msg_span:
                    error_msg = error_msg_span.get_text(strip=True)
                    print(f"登录失败：{error_msg}")
                else:
                    print("登录失败，未找到明确的错误信息。")
                return False

        except requests.exceptions.RequestException as e:
            print(f"登录请求失败: {e}")
            return False

# 测试用例
def test_login():
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    client = YSULogin(username, password)
    success = client.login()
    print("\n登录流程结束。")
    print("登录结果:", "成功" if success else "失败")

if __name__ == "__main__":
    test_login()
