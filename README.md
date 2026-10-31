# BizKnow 公司员工助手 🚀

这是一款完全本地运行、注重隐私的客服聊天机器人，使用检索增强生成（RAG）技术。它根据你自己的 PDF 文档回答问题，无需调用云端 API，文档也不会上传到云端。

![聊天机器人预览](https://placehold.co/1200x630?text=AI+Support+Assistant+Chat+Interface&font=roboto)

## ✨ 功能特点

- **基于文档回答**：将 PDF（制度、手册、常见问题等）用作知识库
- **本地运行并保护隐私**：通过 Ollama 在本机运行
- **快速检索**：使用 FAISS 向量数据库进行语义搜索
- **Agent 工具调用**：按问题调用公司制度检索和工作日计算工具
- **现代化聊天界面**：使用 shadcn/ui，支持动画、响应式布局和深色模式
- **实时反馈**：生成回答时显示流畅的“正在思考……”动画
- **跨平台**：支持 Linux、Windows 和 macOS

## 🔎 RAG 工作流程

1. [`server/app/ingest.py`](server/app/ingest.py) 使用 `PyPDFLoader` 读取 PDF 的每一页，将内容切分为 500 个字符的文本块，相邻文本块重叠 50 个字符，再将文本块向量化并保存到 `server/vectorstore/` 下的 FAISS 索引中。
2. [`server/app/rag.py`](server/app/rag.py) 使用相同的嵌入模型将问题转换为向量，从 FAISS 中检索最相关的 5 个文本块，并将它们作为上下文放入提示词。
3. Ollama 使用 `qwen2.5:0.5b` 运行 Agent。Agent 会判断是否调用公司制度检索工具或工作日计算工具，再根据工具结果生成简短回答。FastAPI 通过 `POST /ask` 提供接口，Next.js 聊天页面调用该接口。

嵌入模型（`all-MiniLM-L6-v2`）将文本转换为向量，用于语义检索，不负责撰写回答。Ollama 模型通过 LangChain Agent 的工具调用机制选择要执行的工具：制度问题会调用 FAISS 检索，日期区间问题可以调用工作日计算。回答下方会显示本次实际调用的工具。工作日工具按周一至周五计算，不扣除法定节假日。

在本地联调前端和后端时，将 `client/.env.example` 复制为 `client/.env.local`，并将 `NEXT_PUBLIC_API_BASE_URL` 设置为 FastAPI 服务地址（默认是 `http://localhost:8000`）。启动 Ollama、导入 PDF，再将 FastAPI 运行在 8000 端口、前端运行在 3000 端口。可以通过后端的 `GET /health` 和 `GET /docs` 检查服务状态并查看接口文档。

## 👥 员工账号

- 员工档案和密码哈希保存在本地 SQLite 数据库 `server/data/employees.sqlite3` 中（Git 不会跟踪该文件）。密码使用 PBKDF2 加盐哈希，不会以明文保存。
- 在 `server` 目录运行 `python -m app.create_admin` 创建首个管理员。程序会提示输入管理员登录信息和个人资料。
- 在前端页面登录后，管理员可在账号面板中创建和查看员工账号。管理员为新账号设置初始密码后，应通过公司认可的安全渠道告知员工。
- 登录接口为 `POST /auth/login`；`GET /auth/me` 返回当前登录员工的个人资料。`POST /employees` 和 `GET /employees` 仅管理员可用。调用 `POST /ask` 必须先登录。
- 本地演示以外的使用场景必须设置唯一的 `EMPLOYEE_AUTH_SECRET` 环境变量；内置默认密钥仅供开发使用。登录令牌 8 小时后过期。若要部署到互联网，还应使用 HTTPS、安全的 HttpOnly Cookie 或公司单点登录，并实现账号恢复、停用、审计日志和托管数据库等功能。

即使尚未准备 PDF 索引，API 也可以启动，管理员仍可创建员工账号。此时员工可以登录，但在知识库建成之前，`/ask` 会返回 HTTP 503。

在 Windows PowerShell 中安装后端依赖并激活虚拟环境后，在同一个终端设置一个长期保存的随机密钥，然后创建首个管理员并启动 API：

```powershell
$env:EMPLOYEE_AUTH_SECRET = "paste-a-long-random-secret-here"
python -m app.create_admin
uvicorn main:app --reload --port 8000
```

请将密钥保存在公司认可的密钥管理工具中。启动前端时，将 `client/.env.example` 复制为 `client/.env.local`，然后在 `client` 目录运行 `pnpm dev`。

## 🛠️ 技术栈

### 后端

- Python 3.10+
- FastAPI
- LangChain（新版 Runnable API）
- FAISS（向量数据库）
- SentenceTransformers (`all-MiniLM-L6-v2`)
- Ollama（当前配置模型为 `qwen2.5:0.5b`）

### 前端

- Next.js 14+（App Router）
- TypeScript
- Tailwind CSS
- shadcn/ui 组件
- Framer Motion（动画）
- Lucide React 图标

### AI 模型

- **RAG 链路当前配置**：`qwen2.5:0.5b`（体积较小、运行较快，详见 `server/app/rag.py`）
- 其他可选模型：`phi3:mini`、`gemma2:2b`、`llama3.2:3b`

## 📋 环境要求

1. **Node.js**（v18 或更高版本）和 **npm**
2. **Python**（建议使用 3.10–3.12）
3. 安装 [Ollama](https://ollama.com/download)

   安装 Ollama 后，下载模型：

   ```bash
   ollama pull qwen2.5:0.5b
   ```

## 🚀 快速开始（一键启动）

### 方式一：使用启动脚本（推荐）

在项目根目录运行：

```bash
# Linux / macOS / Git Bash / WSL 下运行
./run.sh

# Windows PowerShell 下运行
.\run.ps1
```

根据菜单选择只启动后端、只启动前端或同时启动。

### 方式二：手动启动

```bash
# 1. 克隆项目并进入项目目录
git clone <your-repo-url>
cd customer-support-chatbot

# 2. 配置后端
cd server
python -m venv env
source env/bin/activate          # Windows：运行 env\Scripts\activate
pip install -r requirements.txt

# 3. 配置前端
cd ../client
npm install
# 或使用 pnpm install / yarn install

# 4. 导入文档（仅首次需要）
cd ../server
python -m app.ingest             # PDF 文件应放在 server/data/docs/

# 5. 启动服务（需要两个终端）
# 终端 1：后端
cd server
source env/bin/activate
uvicorn main:app --reload --port 8000

# 终端 2：前端
cd client
npm run dev
```

在浏览器中打开：[http://localhost:3000](http://localhost:3000)

API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

## 📚 添加知识库

1. 将 PDF 文件放入 `server/data/docs/`
2. 运行导入命令：
   ```bash
   cd server
   source env/bin/activate
   python -m app.ingest
   ```
3. 重启后端服务。

完成后，聊天机器人就可以根据这些文档回答问题。

## ⚙️ 性能建议（配置较低的电脑）

例如，Ryzen 3 3200G 可尝试以下设置：

- 使用当前配置的 `qwen2.5:0.5b` 降低内存占用；如果硬件性能允许，也可以尝试更大的模型以提高回答质量。
- 限制 Ollama 使用的线程数：
  ```bash
  export OLLAMA_NUM_THREADS=3
  ```
- 如有需要，可在 `app/rag.py` 中调小上下文长度。

在 Apple M4 设备上，回答预计需要 **2–5 秒**；老旧电脑可能需要更长时间。

## 🐛 常见问题排查

| 问题 | 解决方法 |
| --- | --- |
| 聊天页面提示知识库不可用 | 将 PDF 放入 `server/data/docs/`，运行 `python -m app.ingest` 构建索引，然后重启后端。 |
| 提示无法连接服务器 | 确认后端已在 8000 端口运行。 |
| 回答速度较慢 | 换用较小的模型，并限制线程数。 |
| Ollama 报错 | 运行 `ollama serve &`，并通过 `ollama list` 检查模型。 |
| 找不到向量库 | 重新运行文档导入脚本。 |
| 导入模块时报错 | 在干净的虚拟环境中重新安装依赖。 |

## 🤝 参与贡献

欢迎参与改进，例如：

- 改进界面和交互体验
- 增加 Markdown 渲染
- 支持更多文档类型
- 优化运行性能

## 📄 许可证

本项目采用 MIT 许可证，可用于商业用途或进行修改。

---

由 [HoweCro](https://github.com/HoweCro) 修改并维护 · 2026 年


**祝你使用愉快** 🚀
