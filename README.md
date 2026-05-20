# 跨国串门 (International Visiting) 🎙️🌍

**跨国串门** 是一个先进的自动化工具，旨在打破语言壁垒，将优质的英文播客转换为地道的中文播客。它不仅生成标准的 RSS 订阅源，还提供了一个支持双语字幕同步滚动的高级 Web 播放器。

## ✨ 核心特性

- **一键全自动转换**：输入 Apple Podcasts 链接，自动完成下载、听写、翻译、合成、发布全流程。
- **🚀 异步并发架构**：翻译与合成阶段全面采用 `asyncio` 并发处理，处理速度比传统串行模式提升 3-5 倍。
- **🎙️ AI 角色分离 (Diarization)**：利用 LLM 智能识别主持人与嘉宾，并自动分配不同的中文音色（如男声主持人、女声嘉宾），打造真实对谈听感。
- **🧠 专业级翻译**：
    - **全局术语表 (Glossary)**：支持自定义专业词汇映射，确保核心概念翻译前后一致。
    - **语境增强**：翻译前自动生成全篇背景摘要，让 AI 深入理解节目主旨后再进行片段翻译。
- **🌐 交互式 Web 播放器**：
    - **卡拉 OK 字幕**：中英双语对照文本随音频播放同步高亮滚动。
    - **点击即播**：点击任意一段文本，音频自动跳转到对应时间点播放。
- **📻 手机端原生订阅**：生成包含完整双语 Show Notes 的 RSS 订阅源，支持 Apple Podcasts、小宇宙等客户端。

## 🛠️ 技术架构

1.  **Downloader**: 健壮的下载器，支持 iTunes API 解析、UA 伪装及下载进度实时显示。
2.  **Transcriber**: 基于 `Whisper` 的高性能语音识别。
3.  **Translator**: 使用 `AsyncOpenAI` 驱动的智能翻译引擎，内置断点续传与重试机制。
4.  **Synthesizer**: `Edge-TTS` 并发合成引擎，支持多角色音色映射。
5.  **Web Portal**: 基于 HTML5 + Vanilla JS 的轻量级移动端优先播放器。

## 📖 使用指南 (Usage Guide)

### 1. 配置 API 密钥 (必选)
在项目根目录创建 `.env` 文件，配置您的大模型 API 密钥以获得真实翻译效果：
```bash
LLM_API_KEY=您的_API_KEY
LLM_BASE_URL=https://api.openai.com/v1 # 或您的代理地址
```

### 2. 转换播客

#### **A. 手动转换 (单次)**
输入一个 Apple Podcasts 链接即可开始：
```bash
# 测试模式：仅转换前 5 分钟（建议先用此模式检查音色和翻译）
./venv/bin/python3 main.py "https://podcasts.apple.com/..."

# 全量模式：转换整集播客
./venv/bin/python3 main.py "https://podcasts.apple.com/..." --full

# 断点续传：如果任务中断，运行此命令自动从失败处继续
./venv/bin/python3 main.py --resume
```

#### **B. 自动监控 (长期运行)**
1. 在 `config.py` 的 `monitored_urls` 中添加您关注的播客链接。
2. 运行监控脚本：
```bash
./venv/bin/python3 monitor.py
```
*建议配合 `crontab -e` 设置定时任务：`0 * * * * cd /path/to/project && ./venv/bin/python3 monitor.py`*

### 3. 收听与体验成果

#### **第一步：启动展示服务**
```bash
cd output
python3 -m http.server 8000
```

#### **第二步：访问方式**
- **Web 交互播放器**：浏览器打开 `http://<服务器IP>:8000/index.html`。
    - *特性：双语字幕随动高亮，点击文字跳转播放。*
- **播客 App 订阅**：在 Apple Podcasts 或小宇宙中选择“通过 URL 添加”，输入 `http://<服务器IP>:8000/podcast.xml`。
    - *特性：标准 RSS 体验，支持后台播放，Show Notes 查看双语对照。*

## ⚙️ 进阶配置
在 `config.py` 中您可以深度自定义：
- **声音更换**：修改 `speaker_voice_map` 映射不同角色的 Edge-TTS 音色。
- **术语优化**：在 `glossary` 中添加特定领域的专有名词对照表。

---
🤖 *本项目由 Gemini CLI 协作开发完成。*  
Maintainer: [jianluzj](mailto:jianluzj@gmail.com)
