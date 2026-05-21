# 跨国串门 (International Visiting) Web 版升级架构设计

## 1. 概述
将现有的 CLI 自动化流水线升级为生产可用的 Web 应用程序。用户可以通过浏览器提交播客 URL，实时查看处理进度，并在转换完成后在线播放和下载 RSS。

## 2. 核心挑战
*   **长时任务**：转换流程耗时长（30min+），需解决 Web 请求超时问题。
*   **并发控制**：防止多个用户同时提交导致 GPU/CPU/API 频率过载。
*   **状态反馈**：前端需实时感知后端处理到哪一个步骤（ASR、翻译或合成）。

## 3. 技术栈建议
*   **后端 API**: FastAPI (高性能异步 Python 框架)
*   **任务队列**: Celery + Redis (处理后台长耗时任务)
*   **数据库**: SQLite (初级) / PostgreSQL (进阶) - 存储任务状态、元数据和用户设置
*   **存储**: 本地目录 (初级) / 阿里云 OSS 或 AWS S3 (进阶) - 存储生成的 MP3 和 JSON
*   **前端**: Vue.js 或 React + Tailwind CSS (现代响应式 UI)

## 4. 系统架构图 (逻辑)
```text
[浏览器前端] <--> [FastAPI 后端] <--> [Redis 任务队列] <--> [Celery Worker(s)]
      ^                |                                      |
      |                v                                      v
      +---------- [数据库] <----------------------------------+ [核心引擎]
                                                               (Downloader/Whisper/LLM/TTS)
```

## 5. 核心模块修改
### 5.1 后端封装 (API Layer)
*   `POST /api/jobs`: 接收 URL 和 API Key，创建任务并返回 `job_id`。
*   `GET /api/jobs/{job_id}`: 返回任务当前状态（PENDING, RUNNING, COMPLETED, FAILED）及进度百分比。
*   `GET /api/podcasts`: 列表展示所有已转换完成的播客。

### 5.2 任务异步化 (Worker Layer)
*   将 `main.py` 的逻辑重构为 Celery Task。
*   在每个步骤结束时更新数据库中的任务进度：
    *   Step 1: Download -> 进度 10%
    *   Step 2: Transcribe -> 进度 40%
    *   ...

### 5.3 前端交互 (UI Layer)
*   **Dashboard**: 显示所有历史转换记录。
*   **Submission**: 支持输入 Apple Podcasts URL。
*   **Real-time Player**: 继承并优化现有的“双语高亮滚动”功能。

## 6. 实施路线图
1.  **阶段 1: API 骨架** - 搭建 FastAPI 并将现有核心函数封装进 API。
2.  **阶段 2: 任务队列** - 集成 Redis 和 Celery，实现后台静默处理。
3.  **阶段 3: 进度追踪** - 在核心引擎中插入 Webhook 或数据库更新逻辑。
4.  **阶段 4: 前端开发** - 制作现代化的 Web 交互界面。

---
这份设计旨在以最小的代码变动（复用 80% 核心代码）实现最高效的 Web 转型。
