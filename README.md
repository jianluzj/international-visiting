# 跨国串门 (International Visiting) 🎙️🌍

**跨国串门** 是一个自动化工具，旨在打破语言壁垒，将优质的英文播客转换为中文播客，并保留中英双语对照文本。它生成的标准 RSS 订阅源可以让你在手机播客 App 中像听中文节目一样收听全球资讯。

## ✨ 核心特性

- **一键转换**：输入 Apple Podcasts 链接，自动完成下载、听写、翻译、合成全流程。
- **高精度听写**：集成 OpenAI 开源的 `Whisper` 模型，精准捕捉英文原意。
- **智能翻译**：支持接入 LLM (如 GPT-4o, DeepSeek) 进行地道的语境翻译。
- **自然合成**：采用 Microsoft `Edge-TTS` 免费方案，生成自然流畅的中文配音。
- **双语 RSS**：生成包含中英对照 Show Notes 的 RSS 订阅源，支持 Apple Podcasts、小宇宙等客户端。
- **灵活预览**：支持生成 5 分钟测试片段，快速验证效果。

## 🛠️ 技术架构

1.  **Downloader**: 解析 iTunes API 提取原始音频。
2.  **Transcriber**: 使用 Whisper 进行 ASR 语音识别。
3.  **Translator**: 调用大模型进行分段翻译并生成双语结构。
4.  **Synthesizer**: 使用 Edge-TTS 合成中文 MP3。
5.  **RSS Generator**: 封装标准播客 XML 协议。

## 🚀 快速开始

### 1. 环境准备
确保系统中已安装 `ffmpeg` 和 `python3-venv`。

### 2. 安装项目
```bash
git clone <your-repo-url>
cd international-visiting
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 运行转换
```bash
# 测试运行（5分钟片段，不带 API Key 使用占位翻译）
python3 main.py "https://podcasts.apple.com/..."

# 正式运行（完整转换，使用 API Key）
python3 main.py "https://podcasts.apple.com/..." --full --llm-key "YOUR_API_KEY"
```

### 4. 订阅收听
转换完成后，`output` 目录会生成 `podcast.xml` 和 `chinese_podcast.mp3`。
启动本地服务：
```bash
cd output
python3 -m http.server 8000
```
在手机播客 App 中通过 URL 添加：`http://<你的服务器IP>:8000/podcast.xml`。

## ⚙️ 配置说明

可以通过环境变量或命令行参数配置：
- `LLM_API_KEY`: 翻译用的 API 密钥。
- `LLM_BASE_URL`: API 代理地址（如需）。
- `BASE_URL`: RSS 文件中音频的访问根地址。

---
🤖 *本项目由 Gemini CLI 协作开发完成。*  
Maintainer: [jianluzj](mailto:jianluzj@gmail.com)
