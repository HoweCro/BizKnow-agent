#!/usr/bin/env bash
# Shell 启动脚本。
# 用于一键启动 AI 客服聊天机器人项目。
# 建议在 Linux、macOS、Git Bash 或 WSL 中运行。

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$PROJECT_ROOT/server"
client_DIR="$PROJECT_ROOT/client"   # 如果前端目录名称不同，请修改此处。

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # 终端默认颜色。

echo -e "${GREEN}AI Customer Support Chatbot Launcher${NC}"
echo "Project root: $PROJECT_ROOT"
echo ""

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}Error:${NC} $1 is required but not installed."
        exit 1
    fi
}

# ── 检查基础依赖 ──────────────────────────────────────────────────
check_command python3
check_command node   # 检查 Node.js 运行环境。
check_command npm

# ── 启动辅助函数 ──────────────────────────────────────────────────
start_backend() {
    echo -e "${YELLOW}Starting FastAPI backend...${NC}"
    cd "$SERVER_DIR" || { echo -e "${RED}Cannot cd to server directory${NC}"; exit 1; }

    # 如果虚拟环境存在，则先激活。
    if [ -d "env" ] && [ -f "env/bin/activate" ]; then
        # shellcheck disable=SC1091
        source env/bin/activate
    elif [ -d ".venv" ] && [ -f ".venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source .venv/bin/activate
    fi

    # 检查 Ollama 是否正在运行；如果没有，则尝试启动。
    if ! curl -s http://localhost:11434 > /dev/null; then
        echo -e "${YELLOW}Ollama not detected. Trying to start it in background...${NC}"
        ollama serve >/dev/null 2>&1 &
        sleep 3
    fi

    # 启动后端服务。
    exec uvicorn main:app --reload --port 8000
}

start_client() {
    echo -e "${YELLOW}Starting Next.js client...${NC}"
    cd "$client_DIR" || { echo -e "${RED}Cannot cd to client directory${NC}"; exit 1; }

    # 如果前端依赖尚未安装，则自动安装。
    if [ ! -d "node_modules" ]; then
        echo "Installing client dependencies..."
        npm install
    fi

    exec npm run dev
}

# ── 主流程 ────────────────────────────────────────────────────────
echo "Choose what you want to start:"
echo "  1) Backend only      (FastAPI + Ollama check)"
echo "  2) client only     (Next.js dev server)"
echo "  3) Both (recommended – opens two terminals)"
echo ""
read -rp "Enter number (1–3): " choice

case $choice in
    1)
        start_backend
        ;;
    2)
        start_client
        ;;
    3)
        echo -e "${GREEN}Launching both services...${NC}"
        echo "(You will need two terminal windows)"

        if command -v tmux >/dev/null 2>&1; then
            tmux new-session -d -s chatbot 'cd "'"$SERVER_DIR"'" && bash -c "source env/bin/activate 2>/dev/null || true; uvicorn main:app --reload --port 8000"'
            tmux split-window -h -t chatbot 'cd "'"$client_DIR"'" && npm run dev'
            tmux attach -t chatbot
        elif command -v gnome-terminal >/dev/null 2>&1; then
            gnome-terminal -- bash -c "cd '$SERVER_DIR' && source env/bin/activate 2>/dev/null || true && uvicorn main:app --reload --port 8000; exec bash" &
            gnome-terminal -- bash -c "cd '$client_DIR' && npm run dev; exec bash" &
        else
            echo -e "${YELLOW}Please open two terminals manually:${NC}"
            echo "Terminal 1: cd server && source env/bin/activate && uvicorn main:app --reload --port 8000"
            echo "Terminal 2: cd client && npm run dev"
        fi
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
