# Video2Text UI 改进设计

> **Date:** 2026-04-22
> **Status:** Approved
> **Goal:** 三大改进：Ollama 模型动态加载、任务进度显示、可执行文件打包

---

## 1. Ollama 模型动态加载

### 行为定义

- 当用户切换到 Ollama 选项卡时，异步加载模型列表
- 调用 `GET http://localhost:11434/api/tags`，解析返回的模型名称
- 加载期间下拉框显示 "加载中..."，其他交互暂时禁用
- 加载成功后填充模型列表，自动选中上次使用的模型（从 config 读取）
- 加载失败（Ollama 未运行）时，显示错误提示，保留默认 fallback 列表：`["llama3.2", "deepseek-r1:7b"]`

### 新增文件

**`src/video2text/core/ollama_client.py`**

```python
"""Ollama API client for model discovery."""
from typing import List, Optional
import requests


def list_models(base_url: str = "http://localhost:11434") -> List[str]:
    """Fetch available models from local Ollama instance."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        return [m["name"] for m in models]
    except Exception:
        return []


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama service is reachable."""
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
```

### 修改 `main_window.py`

- `_update_model_list()` 中当 `provider == "ollama"` 时，改为调用 `list_models()` 异步加载
- 新增 `_load_ollama_models()` 方法，用 QThread/异步方式调用 API，结果返回后填充下拉框
- 加载失败时用 `QMessageBox.warning()` 提示用户

### 错误处理

| 场景 | 处理 |
|------|------|
| Ollama 未运行 | 警告框提示，fallback 默认列表 |
| 网络超时（5s） | 同上 |
| 返回格式异常 | 同上 |

---

## 2. 任务进度显示

### 进度条工作模式

**两种模式切换：**

1. **Indeterminate 模式** — 用于快速步骤（准备文件、下载、提取音频、生成摘要）
2. **Percentage 模式** — 用于 Whisper 转录（耗时最长，可获取真实进度）

### 进度步骤定义

| 步骤 | 状态文本 | 进度条模式 |
|------|----------|-----------|
| 0 | "正在准备文件..." | Indeterminate |
| 1 | "正在下载视频..."（URL）或"正在验证文件..."（本地） | Indeterminate |
| 2 | "正在提取音频..." | Indeterminate |
| 3 | "正在转录音频... X%" | Percentage (0-100) |
| 4 | "正在生成摘要..." | Indeterminate |
| 5 | "处理完成！" | 进度条隐藏 |

### 修改 `transcriber.py`

新增 `transcribe_with_progress()` 函数，接收 `progress_callback`：

```python
def transcribe_with_progress(audio_path: str, model: str = "base",
                               progress_callback=None) -> List[dict]:
    """Transcribe with progress callback. callback(current, total)"""
    # ... 初始化模型 ...
    def seg_to_progress(segment):
        # faster-whisper supports no built-in progress,
        # so estimate based on segment index is approximate.
        # For real % we'd need to track audio position / duration.
        pass

    segments, info = model_instance.transcribe(
        audio_path, beam_size=5,
        word_timestamps=True  # enables better progress estimation
    )
    # yield progress as we iterate segments
```

> **注：** faster-whisper 本身不暴露原生进度回调。通过 `word_timestamps=True` 和 segment 数量可估算进度百分比。

### 修改 `main_window.py` — Worker 类

```python
class Worker(QThread):
    progress = pyqtSignal(str)        # 状态文本
    progress_pct = pyqtSignal(int)    # 百分比 (0-100)
    progress_mode = pyqtSignal(str)    # "indeterminate" | "percentage"

    def run(self):
        # 步骤 0-2: indeterminate
        self.progress_mode.emit("indeterminate")
        self.progress.emit("正在准备文件...")

        # 步骤 2 切换到 percentage
        self.progress_mode.emit("percentage")
        self.progress_pct.emit(0)

        # 转录时实时更新
        def on_transcribe_progress(current, total):
            pct = int(current / total * 100) if total > 0 else 0
            self.progress_pct.emit(pct)

        segments = transcribe_with_progress(
            audio_path, model=self.whisper_model,
            progress_callback=on_transcribe_progress
        )
```

### 修改 `main_window.py` — MainWindow 类

```python
def _on_progress(self, msg: str):
    self.status_label.setText(msg)

def _on_progress_pct(self, pct: int):
    self.progress_bar.setValue(pct)

def _on_progress_mode(self, mode: str):
    if mode == "indeterminate":
        self.progress_bar.setMaximum(0)
        self.progress_bar.setValue(0)
    else:
        self.progress_bar.setMaximum(100)
```

Worker 的 `progress_pct` 和 `progress_mode` 信号连接到对应的槽。

---

## 3. 可执行文件打包（NSIS + PyInstaller）

### 完整自包含打包方案

**目标：** 用户安装后无需预装 Python、FFmpeg、PyQt6 或任何运行时。安装包即完整可用。

### 工具链

```
Python 源码
    ↓ [PyInstaller — 单目录模式]
output/video2text/          ← 包含 video2text.exe + 所有依赖
    ↓ [NSIS — 打包为安装程序]
Video2Text-Setup.exe        ← 最终用户安装包
```

### PyInstaller 配置

**`video2text.spec`** （放在项目根目录）:

```spec
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/video2text/__main__.py'],
    pathex=[],
    binaries=[
        # Bundled FFmpeg — 只需 ffmpeg.exe 和 ffprobe.exe
        ('ffmpeg/*', 'ffmpeg/'),   # 第三方 ffmpeg 二进制文件
    ],
    datas=[
        # .env 配置（不包含密钥，仅defaults）
        ('src/video2text/utils/.env.default', 'video2text/utils/'),
    ],
    hiddenimports=[
        'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui',
        'faster_whisper', 'yt_dlp', 'ollama', 'openai', 'google.genai',
        'dotenv',
    ],
    ...
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts,
    [],
    exclude_binaries=False,
    name='Video2Text',
    console=False,          # 不显示控制台窗口
    icon='assets/icon.ico', # 应用图标
    ...
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,
    name='video2text',
)
```

### FFmpeg Bundled 方案

- 从 https://github.com/BtbN/FFmpeg-Builds 下载 `ffmpeg-master-latest-win64-gpl.zip`
- 解压后只取 `ffmpeg.exe` 和 `ffprobe.exe`（体积最小化）
- 放入项目 `vendor/ffmpeg/` 目录
- PyInstaller 的 `binaries` 参数将其打包进输出目录

### NSIS 安装脚本

**`installer.nsi`**:

```nsis
!include "MUI2.nsh"

Name "Video2Text"
OutFile "Video2Text-Setup.exe"
InstallDir "$PROGRAMFILES\Video2Text"
InstallDirRegKey HKCU "Software\Video2Text" "InstallDir"

Section "Install"
    SetOutPath "$INSTDIR"

    # 复制 PyInstaller 输出目录中的所有文件
    File /r "dist\video2text\*.*"

    # 创建开始菜单
    CreateDirectory "$SMPROGRAMS\Video2Text"
    CreateShortcut "$SMPROGRAMS\Video2Text\Video2Text.lnk" "$INSTDIR\Video2Text.exe"
    CreateShortcut "$SMPROGRAMS\Video2Text\卸载 Video2Text.lnk" "$INSTDIR\Uninstall.exe"

    # 桌面快捷方式
    CreateShortcut "$DESKTOP\Video2Text.lnk" "$INSTDIR\Video2Text.exe"

    # 注册卸载信息
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Video2Text" "InstallDir" "$INSTDIR"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\*.*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\Video2Text\*.*"
    RMDir "$SMPROGRAMS\Video2Text"
    Delete "$DESKTOP\Video2Text.lnk"
    DeleteRegKey HKCU "Software\Video2Text"
SectionEnd
```

### 打包命令

```bash
# 1. 下载并准备 bundled FFmpeg
scripts\prepare-ffmpeg.ps1

# 2. 安装 PyInstaller 并打包
pip install pyinstaller
pyinstaller video2text.spec --clean

# 3. 使用 NSIS 编译安装包
makensis installer.nsi
```

### 体积预估

| 组件 | 估计大小 |
|------|---------|
| Python 运行时 + 标准库 | ~25 MB |
| PyQt6 | ~80 MB |
| faster-whisper + 模型支持 | ~20 MB |
| yt-dlp, openai, google-genai | ~15 MB |
| FFmpeg (ffmpeg.exe + ffprobe.exe) | ~150 MB |
| 应用代码 | ~5 MB |
| **总计** | **~300 MB** |

最终 `Video2Text-Setup.exe` 约 300 MB，单 exe 用户直接运行约 300 MB。

---

## 修改文件清单

| 文件 | 操作 |
|------|------|
| `src/video2text/core/ollama_client.py` | 新增 |
| `src/video2text/core/transcriber.py` | 修改：新增 `transcribe_with_progress()` |
| `src/video2text/ui/main_window.py` | 修改：Ollama 懒加载 + 进度信号 + 进度条切换 |
| `src/video2text/utils/config.py` | 修改：支持 `get_ollama_base_url` 读取 |
| `video2text.spec` | 新增：PyInstaller 配置 |
| `installer.nsi` | 新增：NSIS 安装脚本 |
| `scripts/prepare-ffmpeg.ps1` | 新增：下载 bundled FFmpeg |
| `CLAUDE.md` | 更新：打包命令 |
