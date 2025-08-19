# 燕山大学锐捷V2网络认证命令行工具

一个基于Python的UNIX风格命令行工具，用于燕山大学锐捷V2网络认证系统的登录、登出和状态管理。

## 特性

- 🚀 **UNIX风格**: 支持非交互式使用，适合脚本化和自动化
- 🔐 **智能交互**: 仅在需要验证码或缺少凭据时才提示用户输入
- 🌐 **代理支持**: 支持HTTP/HTTPS/SOCKS5代理
- 📊 **状态管理**: 实时检查登录状态和账户信息
- 🛡️ **错误处理**: 完善的错误处理和用户友好的错误提示
- ⚙️ **配置灵活**: 支持命令行参数、环境变量等多种配置方式

## 安装

### 1. 克隆项目
```bash
git clone https://github.com/KamijoToma/YSUNetLoginv2.git
cd YSURuijieLoginv2
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

## 使用方法

### 基本命令

```bash
# 登录（交互式）
python ruijie_cli.py login

# 登录（非交互式）
python ruijie_cli.py login -u 202211040044 -p mypassword

# 登录到指定服务（使用英文别名）
python ruijie_cli.py login -u 202211040044 -p mypassword -s unicom

# 列出可用服务并选择
python ruijie_cli.py login -u 202211040044 -p mypassword -s

# 检查登录状态
python ruijie_cli.py status

# 登出
python ruijie_cli.py logout

# 查看账户信息
python ruijie_cli.py info

# 查看帮助
python ruijie_cli.py --help
```

### 环境变量配置

为了避免在命令行中暴露密码，推荐使用环境变量：

```bash
# 设置用户名和密码
export RUIJIE_USERNAME=1145141919810
export RUIJIE_PASSWORD=mypassword

# 然后直接登录
python ruijie_cli.py login
```

支持的环境变量：
- `RUIJIE_USERNAME`: 默认用户名
- `RUIJIE_PASSWORD`: 默认密码
- `RUIJIE_VERBOSE`: 启用详细输出 (1/true/yes)
- `RUIJIE_SERVICE`: 服务名称 (默认: 校园网)
- `HTTP_PROXY`: HTTP代理URL
- `HTTPS_PROXY`: HTTPS代理URL

### 代理配置

如果需要使用代理，可以通过以下方式配置：

```bash
# 方法1: 命令行参数
python ruijie_cli.py login --proxy socks5://127.0.0.1:1080

# 方法2: 环境变量
export HTTP_PROXY=socks5://127.0.0.1:1080
export HTTPS_PROXY=socks5://127.0.0.1:1080
python ruijie_cli.py login
```

### 服务选择

程序支持多种网络服务，并提供英文别名以解决中文输入问题：

```bash
# 使用中文服务名
python ruijie_cli.py login -s 校园网
python ruijie_cli.py login -s 中国联通

# 使用英文别名
python ruijie_cli.py login -s campus     # 校园网
python ruijie_cli.py login -s unicom     # 中国联通
python ruijie_cli.py login -s telecom    # 中国电信
python ruijie_cli.py login -s mobile     # 中国移动

# 使用数字别名
python ruijie_cli.py login -s 1          # 校园网
python ruijie_cli.py login -s 2          # 中国联通
python ruijie_cli.py login -s 3          # 中国电信
python ruijie_cli.py login -s 4          # 中国移动

# 列出可用服务并交互式选择
python ruijie_cli.py login -s
```

### 详细输出

启用详细输出可以查看登录过程的详细信息：

```bash
# 方法1: 命令行参数
python ruijie_cli.py login -v

# 方法2: 环境变量
export RUIJIE_VERBOSE=1
python ruijie_cli.py login
```

## 使用示例

### 1. 日常使用
```bash
# 早上到校后登录
python ruijie_cli.py login -u 1145141919810 -p mypassword

# 检查网络状态
python ruijie_cli.py status
# 输出: Online: 1145141919810 (中国联通)

# 离校前登出
python ruijie_cli.py logout
```

### 2. 脚本化使用
```bash
#!/bin/bash
# auto_login.sh

export RUIJIE_USERNAME=1145141919810
export RUIJIE_PASSWORD=mypassword

# 检查是否已登录
if python ruijie_cli.py status | grep -q "Offline"; then
    echo "Not logged in, attempting to login..."
    python ruijie_cli.py login
else
    echo "Already logged in"
fi
```

### 3. 验证码处理
当系统要求验证码时，程序会自动：
1. 下载验证码图片到临时文件
2. 提示用户查看图片位置
3. 等待用户输入验证码
4. 完成登录后清理临时文件

```bash
$ python ruijie_cli.py login -u 1145141919810 -p mypassword
请查看并输入验证码图片: captcha.jpg
请输入验证码: abcd
Login successful.
```

## 退出码

程序遵循UNIX约定的退出码：
- `0`: 操作成功
- `1`: 操作失败
- `130`: 用户中断 (Ctrl+C)

这使得程序可以很好地与shell脚本集成：

```bash
if python ruijie_cli.py login; then
    echo "Login successful"
else
    echo "Login failed"
fi
```

## 错误处理

程序提供用户友好的错误提示：

- **网络连接错误**: "Network connection failed. Please check your internet connection."
- **认证失败**: "Authentication failed. Please check your username and password."
- **门户访问失败**: "Portal access failed. You may not be connected to the campus network."
- **验证码错误**: "Captcha verification failed. Please try again."

## 文件结构

```
YSURuijieLoginv2/
├── ruijie_cli.py          # 主程序入口
├── ruijie_client.py       # 核心客户端类
├── config.py              # 配置管理
├── ysu_login.py          # CAS登录模块
├── requirements.txt       # 依赖列表
├── ruijie_ysu.ipynb      # 原始研究笔记本
├── TECH.md               # 技术文档
└── README.md             # 本文档
```

## 技术说明

本工具基于对燕山大学锐捷V2网络认证系统的逆向工程，主要包含以下技术组件：

1. **HTTP客户端**: 使用requests库处理网络请求
2. **CAS认证**: 集成统一身份认证系统
3. **会话管理**: 自动处理登录流程中的会话状态
4. **加密支持**: 支持CAS登录所需的AES加密
5. **验证码处理**: 自动检测并处理验证码要求

## 注意事项

1. **网络环境**: 本工具需要在校园网环境下使用
2. **凭据安全**: 建议使用环境变量而非命令行参数传递密码
3. **验证码**: 当系统要求验证码时，需要用户手动输入
4. **代理设置**: 开发环境中的代理配置已移除，实际使用时无需代理

## 故障排除

### 常见问题

**Q: 提示"Portal access failed"**
A: 请确保您已连接到校园网络

**Q: 提示"Authentication failed"**
A: 请检查用户名和密码是否正确

**Q: 程序卡住不动**
A: 可能是网络问题，请使用 `-v` 参数查看详细日志

**Q: 验证码识别失败**
A: 请手动查看验证码图片并正确输入

### 调试模式

使用详细输出模式可以帮助诊断问题：

```bash
python ruijie_cli.py login -v
```

## 许可证

本项目仅供学习和研究使用。

## 作者

SkyRain <admin@misakacloud.net>

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。
