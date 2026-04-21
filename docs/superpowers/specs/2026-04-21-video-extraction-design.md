# 视频/音频内容提取与摘要工具 - 设计文档

**日期**: 2026-04-21

## 1. 项目概述

- **项目名称**: Video2Text
- **类型**: 桌面应用程序（Windows）
- **核心功能**: 从视频文件和在线视频 URL 中提取音频、转换为文字，并使用 LLM 生成内容摘要
- **目标用户**: 需要将视频/音频内容转换为可编辑文本的用户（学生、研究人员、内容创作者等）

## 2. 技术架构

```
┌──────────────────────────────────────────────────────────┐
│                      PyQt 界面层                          │
│  (文件上传 / URL 输入 / LLM 配置 / 进度显示 / 结果预览)      │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│                      业务逻辑层                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │ FileHandler │  │ VideoDownloader│ │ TranscriptionEngine│ │
│  │ 本地文件处理 │  │ URL 下载     │  │ Whisper 转录    │   │
│  └─────────────┘  └─────────────┘  └────────┬────────┘   │
│                                             │             │
│                    ┌────────────────────────▼────────┐   │
│                    │        SummaryEngine            │   │
│                    │  Ollama / OpenAI / Gemini LLM    │   │
│                    └─────────────────────────────────┘   │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│                      工具层                               │
│  FFmpeg (音视频处理)  |  yt-dlp (视频下载)  |  Whisper    │
└──────────────────────────────────────────────────────────┘
```

## 3. 模块设计

### 3.1 UI 层 (PyQt6)

**主窗口组件**:
- `MainWindow` - 主窗口，包含所有 UI 元素
- `FileSelectionPanel` - 文件选择（拖拽上传 + 浏览按钮）
- `UrlInputPanel` - URL 输入框
- `SettingsPanel` - LLM 配置面板（Provider 选择、模型选择）
- `ProgressPanel` - 进度显示区域
- `ResultPreviewPanel` - 结果预览区域
- `ExportPanel` - 导出按钮（.md / .json）

**UI 流程**:
1. 用户选择输入方式（本地文件 或 URL）
2. 配置 LLM 选项
3. 点击"开始处理"
4. 显示实时进度
5. 预览结果，支持导出

### 3.2 业务逻辑层

**FileHandler**
- 验证文件格式（mp4, mkv, avi, mov, mp3, wav, m4a）
- 调用 FFmpeg 提取音频

**VideoDownloader**
- 使用 yt-dlp 下载 YouTube / Bilibili 视频
- 支持 cookies 自定义（绕过登录限制）

**TranscriptionEngine**
- 使用 Whisper 开源版（ transformers + faster-whisper）
- 支持模型选择: tiny, base, small, medium, large
- 输出带时间戳的文本片段

**SummaryEngine**
- 抽象接口 `LLMProvider`:
  - `OllamaProvider` - 本地 Ollama
  - `OpenAIProvider` - OpenAI GPT
  - `GeminiProvider` - Google Gemini
- 统一接口: `generate_summary(text) -> str`

### 3.3 工具层

| 工具 | 用途 | 费用 |
|------|------|------|
| FFmpeg | 音频提取、格式转换 | 免费 |
| yt-dlp | 视频下载 | 免费 |
| Whisper | 语音转文字（开源版） | 免费 |
| Ollama | 本地 LLM | 免费 |
| OpenAI API | 云端 LLM | 按量付费 |
| Gemini API | 云端 LLM | 按量付费 |

## 4. 数据流

```
输入 (文件路径 或 URL)
    │
    ▼
[下载/读取] ──► FFmpeg 音频提取
    │
    ▼
Whisper 转录 ──► 时间戳文本
    │
    ├── [transcribe-only 模式] ──► 输出完整转录
    │
    └── [摘要模式] ──► LLM 摘要 ──► 结构化文档
```

## 5. 输出格式

### Markdown 格式 (.md)

```markdown
# 视频/音频内容提取结果

**来源**: /path/to/video.mp4 | https://youtube.com/...
**时长**: 00:15:30
**处理时间**: 2026-04-21 16:00:00
**转录模型**: base
**摘要模型**: gpt-4o

---

## 完整转录

[00:00:00] 开场介绍
[00:00:15] 主题说明
...

---

## 内容摘要

1. 要点一：...
2. 要点二：...
3. 要点三：...

---

## 关键信息

- 关键信息点 1
- 关键信息点 2
```

### JSON 格式 (.json)

```json
{
  "source": "/path/to/video.mp4",
  "duration": "00:15:30",
  "processed_at": "2026-04-21T16:00:00",
  "transcription_model": "base",
  "summary_model": "gpt-4o",
  "full_transcript": [
    {"timestamp": "00:00:00", "text": "开场介绍"},
    {"timestamp": "00:00:15", "text": "主题说明"}
  ],
  "summary": {
    "key_points": ["要点一", "要点二", "要点三"],
    "key_information": ["关键信息1", "关键信息2"]
  }
}
```

## 6. 依赖项

```
PyQt6>=6.6.0
faster-whisper>=1.0.0
yt-dlp>=2024.0.0
openai>=1.0.0
google-genai>=0.8.0
python-dotenv>=1.0.0
```

## 7. 使用方式

### 7.1 图形界面

启动应用后，通过 UI 操作：
1. 选择本地文件或输入 URL
2. 选择是否生成摘要
3. 配置 LLM（本地 Ollama / OpenAI / Gemini）
4. 点击"开始处理"
5. 预览并下载结果

### 7.2 命令行（可选）

```bash
# 本地文件 + Ollama 摘要
python -m video2text video.mp4 --llm ollama --model llama3

# URL + GPT-4 摘要
python -m video2text "https://youtube.com/..." --llm openai --model gpt-4o

# 仅转录
python -m video2text video.mp4 --transcribe-only
```

## 8. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 文件格式不支持 | 弹出错误提示框 |
| URL 下载失败 | 显示错误信息，允许重试 |
| Whisper 转录失败 | 记录日志，提示用户检查音频质量 |
| Ollama 未运行 | 提示启动 Ollama 或切换云端 LLM |
| API 调用失败 | 显示错误信息，包含重试选项 |
| 网络连接失败 | 提示检查网络，切换离线模式 |

## 9. 配置管理

- 使用 `.env` 文件存储 API 密钥和默认设置
- 支持在 UI 中修改 Ollama 地址（默认 `http://localhost:11434`）
- 记住用户上次的 LLM 选择

## 10. 项目结构

```
video-analysis/
├── src/
│   └── video2text/
│       ├── __init__.py
│       ├── main.py              # PyQt 应用入口
│       ├── ui/
│       │   ├── __init__.py
│       │   └── main_window.py   # 主窗口 UI
│       ├── core/
│       │   ├── __init__.py
│       │   ├── file_handler.py  # 文件处理
│       │   ├── downloader.py    # 视频下载
│       │   ├── transcriber.py   # Whisper 转录
│       │   └── summarizer.py    # LLM 摘要
│       └── utils/
│           ├── __init__.py
│           └── config.py        # 配置管理
├── docs/
│   └── specs/
│       └── 2026-04-21-video-extraction-design.md
├── requirements.txt
├── .env.example
└── README.md
```
