import requests
import base64
import random
import os
import tempfile
import atexit
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from bs4 import BeautifulSoup
import urllib3
from PIL import Image
from io import BytesIO

# 禁用 InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class YSULogin:
    LOGIN_URL = "https://cer.ysu.edu.cn/authserver/login?service=https%3A%2F%2Fehall.ysu.edu.cn%2Flogin"
    CHECK_CAPTCHA_URL = "https://cer.ysu.edu.cn/authserver/checkNeedCaptcha.htl"
    CAPTCHA_URL = "https://cer.ysu.edu.cn/authserver/getCaptcha.htl"

    def __init__(self, username, password, session=None, proxies={}, display_mode='both'):
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.proxies = proxies
        self.display_mode = display_mode  # 'ascii', 'file', 'both'
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
        self.captcha_files = []  # 跟踪创建的验证码文件
        
        # 注册退出时的清理函数
        atexit.register(self._cleanup_captcha_files)

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

    def _cleanup_captcha_files(self):
        """
        清理所有创建的验证码文件
        """
        for file_path in self.captcha_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已清理验证码文件: {file_path}")
            except Exception as e:
                print(f"清理验证码文件失败 {file_path}: {e}")
        self.captcha_files.clear()

    def _generate_captcha_filename(self):
        """
        生成唯一的验证码文件名
        """
        timestamp = str(int(random.random() * 1000000))
        filename = f"captcha_{timestamp}.jpg"
        return filename

    def _image_to_ascii(self, image_data, width=60, char_set="standard"):
        """
        将图像数据转换为 ASCII 字符
        
        Args:
            image_data: 图像二进制数据
            width: ASCII 输出宽度
            char_set: 字符集类型 ("dense", "standard", "extended")
        
        Returns:
            ASCII 字符串
        """
        try:
            # 不同密度的字符集
            ascii_chars_dense = "@%#*+=-:. "
            ascii_chars_standard = "@#S%?*+;:,. "
            ascii_chars_extended = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
            
            # 选择字符集
            if char_set == "dense":
                ascii_chars = ascii_chars_dense
            elif char_set == "extended":
                ascii_chars = ascii_chars_extended
            else:
                ascii_chars = ascii_chars_standard
            
            # 从二进制数据创建图像
            image = Image.open(BytesIO(image_data))
            
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
            return f"ASCII转换失败: {e}", None, None

    def _fetch_captcha(self):
        """
        获取验证码并由用户输入，支持ASCII艺术显示和文件保存
        """
        captcha_file = None
        try:
            # 获取验证码图片
            resp = self.session.get(self.CAPTCHA_URL, verify=False, timeout=5, proxies=self.proxies)
            resp.raise_for_status()
            image_data = resp.content
            
            print("=" * 60)
            print("验证码显示")
            print("=" * 60)
            
            # 根据显示模式处理验证码
            if self.display_mode in ['ascii', 'both']:
                # 显示ASCII艺术版本
                print("\nASCII 艺术版本:")
                print("-" * 40)
                ascii_art, orig_size, new_size = self._image_to_ascii(image_data, width=60, char_set="standard")
                if orig_size:
                    print(f"原始尺寸: {orig_size[0]}x{orig_size[1]} -> ASCII尺寸: {new_size[0]}x{new_size[1]}")
                    print()
                    print(ascii_art)
                else:
                    print(ascii_art)
                print("-" * 40)
            
            if self.display_mode in ['file', 'both']:
                # 保存到文件
                captcha_file = self._generate_captcha_filename()
                with open(captcha_file, 'wb') as f:
                    f.write(image_data)
                
                # 添加到跟踪列表
                self.captcha_files.append(captcha_file)
                
                print(f"\n验证码已保存到文件: {captcha_file}")
                
                # 尝试自动打开图片（Windows系统）
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(captcha_file)
                        print("验证码图片已自动打开")
                    else:
                        print(f"请手动打开验证码图片: {captcha_file}")
                except Exception:
                    print(f"无法自动打开图片，请手动查看: {captcha_file}")
            
            print("=" * 60)
            
            # 获取用户输入
            try:
                self.captcha = input("请输入验证码: ").strip()
                if not self.captcha:
                    print("警告：验证码为空")
                    return False
                    
                print(f"验证码输入完成: {self.captcha}")
                return True
                
            except (KeyboardInterrupt, EOFError):
                print("\n验证码输入已取消")
                raise KeyboardInterrupt("用户取消验证码输入")
                
        except requests.exceptions.RequestException as e:
            print(f"错误：获取验证码失败: {e}")
            return False
        except Exception as e:
            print(f"验证码处理出错: {e}")
            return False
        finally:
            # 立即清理当前验证码文件
            if captcha_file and os.path.exists(captcha_file):
                try:
                    os.remove(captcha_file)
                    print(f"验证码文件已清理: {captcha_file}")
                    if captcha_file in self.captcha_files:
                        self.captcha_files.remove(captcha_file)
                except Exception as e:
                    print(f"清理验证码文件失败: {e}")


    def login(self):
        """
        执行登录操作
        """
        if not self._fetch_login_page():
            return False

        if self._need_captcha():
            if not self._fetch_captcha():
                print("错误：需要验证码但获取失败。")
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
                    # 登录成功后清理所有验证码文件
                    self._cleanup_captcha_files()
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
    print("YSU 登录测试 - 支持验证码 ASCII 艺术显示")
    print("=" * 50)
    
    username = input("请输入用户名: ")
    password = input("请输入密码: ")
    
    client = YSULogin(username, password, display_mode='both')
    success = client.login()
    
    print("\n" + "=" * 50)
    print("登录流程结束。")
    print("登录结果:", "成功" if success else "失败")
    print("注意: 验证码文件已自动清理")

if __name__ == "__main__":
    test_login()
