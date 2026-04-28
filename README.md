# Video2Text

视频/音频内容提取与摘要工具。从本地视频文件或在线视频 URL 中提取音频、转换为文字，并使用 LLM 生成内容摘要。

## 功能

- 支持本地视频文件 (MP4, MKV, AVI, MOV) 和音频文件 (MP3, WAV, M4A)
- 支持 YouTube、Bilibili 等在线视频 URL
- 使用 Whisper (faster-whisper) 进行语音识别，完全免费
- 支持三种 LLM Provider:
  - Ollama (本地免费)
  - OpenAI GPT (云端付费)
  - Google Gemini (云端付费)
- 导出为 Markdown 或 JSON 格式
- 打包为 Windows 安装包，无需配置 Python 环境

## 安装

### 1. 安装 FFmpeg

Windows: `winget install FFmpeg` 或从 https://ffmpeg.org 下载

### 2. 安装 Ollama（本地 LLM，可选）

Ollama 用于本地免费的 LLM 摘要功能。

**Windows/macOS/Linux:**
1. 从 https://ollama.com 下载安装
2. 启动 Ollama 服务（Windows 通常自动启动）
3. 下载模型，例如：
   ```bash
   ollama pull llama3.2      # 基础模型，约 2GB
   ollama pull deepseek-r1:7b # 中文能力强
   ```

**常用命令:**
```bash
ollama list           # 查看已下载的模型
ollama pull <模型名>   # 下载新模型
ollama rm <模型名>     # 删除模型
ollama run <模型名>    # 直接运行模型测试
```

### 3. Whisper 模型（首次自动下载）

faster-whisper 首次使用时会自动从 Hugging Face 下载模型（需要网络连接）。模型会缓存到本地，后续无需重新下载。

可用模型：tiny, base, small, medium, large（越大越准确但越慢）

### 4. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 5. 配置 (可选)

复制 `.env.example` 为 `.env`，填入 API 密钥：

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
WHISPER_MODEL=base
```

### 6. 运行

```bash
python -m video2text
```

## 使用方法

1. 选择本地文件或输入 URL
2. 配置 Whisper 模型（默认 base）
3. 选择是否生成摘要
4. 选择 LLM Provider 和模型
5. 点击"开始处理"
6. 预览结果并导出

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# PyInstaller 打包
pyinstaller video2text.spec --clean
```

## 技术栈

- **UI**: PyQt6
- **音频提取**: FFmpeg
- **语音识别**: faster-whisper
- **视频下载**: yt-dlp
- **LLM 抽象**: Ollama / OpenAI / Gemini
- **打包**: PyInstaller + NSIS