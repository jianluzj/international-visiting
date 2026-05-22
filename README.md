# 跨国串门 (International Visiting) 🎙️🌍

**跨国串门** 是一个先进的自动化平台，旨在打破语言壁垒，将优质的英文播客转换为地道的中文播客。它不仅生成标准的聚合 RSS 订阅源，还提供了一个支持双语字幕同步滚动、多集管理的 Web 门户。

## ✨ 核心特性

- **🌐 Web 交互式提交**：提供直观的网页表单，直接粘贴 Apple Podcasts 链接即可触发转换任务。
- **📊 实时进度追踪**：基于异步任务队列，在网页端实时显示“正在听写”、“正在翻译”、“正在合成”等进度百分比。
- **📚 播客库管理**：支持多单集并存，自动生成播客目录首页，不再覆盖旧任务。
- **🎙️ AI 角色分离 (Diarization)**：利用 LLM 智能识别主持人与嘉宾，并自动分配不同的中文音色（男声/女声），打造真实对谈听感。
- **🚀 异步并发架构**：后端采用 FastAPI + Celery + Redis，翻译与合成速度提升 3-5 倍，且网页端提交任务不阻塞。
- **🧠 专业级翻译**：支持全局术语表 (Glossary) 与全篇语境增强，确保金融、科技等专业领域翻译的准确性。
- **📻 动态 RSS 聚合**：自动生成包含所有已转换单集的标准 RSS 订阅源，完美适配 Apple Podcasts 和小宇宙。

## 🛠️ 技术架构

1.  **Backend**: FastAPI (接口) + Celery (异步任务) + Redis (中间件)。
2.  **ASR Engine**: 基于 `Whisper` 的高性能语音识别。
3.  **Translation**: `AsyncOpenAI` 驱动，支持 DeepSeek, GPT-4o 等模型。
4.  **TTS Engine**: `Edge-TTS` 并发合成，支持说话人音色映射。
5.  **Web Portal**: 移动端优先的 HTML5 播放器，支持卡拉 OK 式字幕滚动与点击跳转。

## 🚀 快速开始

### 1. 准备工作
- 确保您的服务器已安装 **Docker** 和 **Docker Compose**。
- 创建 `.env` 文件并配置您的 API 密钥：
```bash
LLM_API_KEY=您的_API_KEY
LLM_BASE_URL=https://api.openai.com/v1 # 或 SenseNova 等代理地址
LLM_MODEL=deepseek-v4-flash
BASE_URL=http://your-domain.com:8080 # Docker 模式下默认为 8080 端口
```

### 2. Docker 一键部署 (推荐)
这是最简单、最稳健的启动方式，自动集成了所有依赖环境：
```bash
git clone https://github.com/jianluzj/international-visiting.git
cd international-visiting
docker-compose up -d --build
```
*   **访问地址**：`http://您的服务器IP:8080`
*   **优点**：无需手动安装 FFmpeg、Redis 等，环境高度隔离，支持自动重启。

---

### 3. 备选方案：本地脚本启动
如果您不使用 Docker，可以手动安装依赖并启动：
1. **安装环境**：安装 `ffmpeg`、`redis-server`、`python3-venv`。
2. **初始化**：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **启动服务**：
   ```bash
   chmod +x start_web_app.sh
   ./start_web_app.sh
   ```
*   **访问地址**：`http://您的服务器IP:8000` (Web) 和 `http://您的服务器IP:8080` (API)

## 📖 使用指南

### 1. 访问网页门户
在浏览器打开：
*   **Docker 模式**: `http://您的服务器IP:8080`
*   **本地脚本模式**: `http://您的服务器IP:8000`
*   **添加播客**：在页面顶部输入链接，点击“开始转换”，观察进度条。
*   **浏览列表**：在首页查看所有已处理完成的历史播客。
*   **交互播放**：点击单集进入播放页，享受双语字幕同步。

### 2. 播客 App 订阅
在 Apple Podcasts 或小宇宙中选择“通过 URL 添加”，输入：
`http://您的服务器IP:8000/podcast.xml`
*该订阅源会自动包含您库中所有的转换单集。*

### 3. 命令行高级用法 (CLI)
```bash
# 断点续传（如果 Web 任务中断）
./venv/bin/python3 main.py --resume
```

## ⚙️ 进阶配置
在 `config.py` 中您可以深度自定义：
- **声音映射**：修改 `speaker_voice_map` 为 HOST 和 GUEST 分配不同音色。
- **术语优化**：在 `glossary` 中添加特定领域的专有名词对照表。

## 🔮 未来优化计划 (Future Roadmap)
- [ ] **听感极致化：原音复刻 (Voice Cloning)**: 引入先进 TTS，提取原片声音样本进行音色克隆，实现“原音说中文”的震撼体验。
- [ ] **结构化阅读：智能章节 (Smart Chapters)**: 利用 LLM 自动识别话题切换点，生成带时间戳的章节导航。
- [ ] **渠道扩展：YouTube 支持**: 支持直接粘贴 YouTube 视频链接进行转换。
- [ ] **交互式校对：Web 版编辑器**: 在翻译和合成之间增加一个人工校对环节，确保“出版级”质量。

---
🤖 *本项目由 Gemini CLI 协作开发完成。*  
Maintainer: [jianluzj](mailto:jianluzj@gmail.com)
