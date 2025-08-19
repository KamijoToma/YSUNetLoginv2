# YSU 登录验证码显示改进

## 概述

对 `ysu_login.py` 中的验证码处理逻辑进行了全面改进，实现了 ASCII 艺术显示和完善的文件管理功能。

## 主要改进

### 1. ASCII 艺术显示
- **功能**: 将验证码图片转换为 ASCII 字符在终端显示
- **实现**: 使用 Pillow 库进行图像处理，支持多种字符集
- **字符集选项**:
  - `dense`: `@%#*+=-:. ` (密集字符集)
  - `standard`: `@#S%?*+;:,. ` (标准字符集，默认)
  - `extended`: 包含更多字符的扩展集

### 2. 显示模式
- **`ascii`**: 仅显示 ASCII 艺术版本
- **`file`**: 仅保存文件并自动打开
- **`both`**: 同时显示 ASCII 艺术和保存文件 (默认)

### 3. 文件管理改进
- **唯一文件名**: 使用时间戳生成唯一的验证码文件名
- **自动清理**: 验证码输入完成后立即删除临时文件
- **退出清理**: 程序退出时自动清理所有残留文件
- **文件跟踪**: 维护文件列表确保完全清理

### 4. 用户体验优化
- **自动打开**: Windows 系统下自动打开验证码图片
- **清晰提示**: 改进的用户界面和提示信息
- **错误处理**: 完善的异常处理和错误提示

## 技术实现

### 新增依赖
```python
from PIL import Image
from io import BytesIO
import os
import atexit
```

### 核心方法

#### `_image_to_ascii(image_data, width=60, char_set="standard")`
- 将图像数据转换为 ASCII 字符
- 支持自定义宽度和字符集
- 自动调整高宽比

#### `_fetch_captcha()`
- 支持多种显示模式
- 自动文件管理
- 完善的错误处理

#### `_cleanup_captcha_files()`
- 清理所有跟踪的验证码文件
- 注册为程序退出时的清理函数

## 使用方法

### 基本使用
```python
from ysu_login import YSULogin

# 使用默认的双重显示模式
client = YSULogin(username, password)
success = client.login()
```

### 指定显示模式
```python
# 仅 ASCII 显示
client = YSULogin(username, password, display_mode='ascii')

# 仅文件显示
client = YSULogin(username, password, display_mode='file')

# 双重显示（推荐）
client = YSULogin(username, password, display_mode='both')
```

## 测试

### ASCII 艺术效果测试
```bash
python ascii_art_test.py
```

### 功能测试
```bash
python test_captcha_display.py
```

### 真实登录测试
```bash
python ysu_login.py
```

## 文件结构

```
├── ysu_login.py              # 主要登录类（已改进）
├── ascii_art_test.py         # ASCII 艺术效果测试
├── test_captcha_display.py   # 功能测试脚本
├── requirements.txt          # 依赖列表（已更新）
└── CAPTCHA_IMPROVEMENTS.md   # 本文档
```

## 优势

1. **无需外部图片查看器**: ASCII 艺术直接在终端显示
2. **自动文件管理**: 无需手动清理临时文件
3. **灵活的显示选项**: 支持多种显示模式
4. **向后兼容**: 保持原有 API 不变
5. **健壮的错误处理**: 完善的异常处理机制

## 注意事项

- ASCII 艺术显示效果取决于终端字体和大小
- 复杂验证码可能在 ASCII 形式下难以识别
- 建议使用 `both` 模式以获得最佳体验
- 文件会在验证码输入后自动清理

## 兼容性

- **操作系统**: Windows, Linux, macOS
- **Python**: 3.6+
- **依赖**: Pillow >= 8.0.0
