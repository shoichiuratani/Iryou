#!/bin/bash

# Surgi-Motion Visualizer 統合起動スクリプト
# 手術手技3D分析システムの起動

set -e  # エラー時に終了

# カラー出力の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ヘッダー表示
echo "================================================================="
echo "🏥 Surgi-Motion Visualizer - 手術手技3D分析システム"
echo "================================================================="
echo ""

# 現在のディレクトリを確認
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log_info "起動ディレクトリ: $PWD"

# Python環境チェック
check_python() {
    log_info "Python環境をチェック中..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3がインストールされていません"
        log_info "Ubuntu/Debian: sudo apt install python3 python3-pip"
        log_info "CentOS/RHEL: sudo yum install python3 python3-pip"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    log_success "Python $PYTHON_VERSION が見つかりました"
    
    # Python 3.8以上かチェック
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Pythonバージョンは要件を満たしています"
    else
        log_error "Python 3.8以上が必要です（現在: $PYTHON_VERSION）"
        exit 1
    fi
}

# Node.js環境チェック（フロントエンドサーバー用）
check_node() {
    log_info "Node.js環境をチェック中..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js $NODE_VERSION が見つかりました"
    else
        log_warning "Node.js が見つかりません（フロントエンドのHTTPサーバーとして使用）"
        log_info "Python HTTPサーバーを代替として使用します"
    fi
}

# 仮想環境のセットアップ
setup_venv() {
    log_info "Python仮想環境をセットアップ中..."
    
    VENV_DIR="./venv"
    
    if [ ! -d "$VENV_DIR" ]; then
        log_info "仮想環境を作成中..."
        python3 -m venv "$VENV_DIR"
    fi
    
    log_info "仮想環境をアクティベート中..."
    source "$VENV_DIR/bin/activate"
    
    log_success "仮想環境がアクティベートされました"
    
    # pipをアップグレード
    pip install --upgrade pip
}

# バックエンド依存関係のインストール
install_backend_deps() {
    log_info "バックエンドの依存関係をインストール中..."
    
    cd backend
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "バックエンドの依存関係がインストールされました"
    else
        log_error "requirements.txt が見つかりません"
        exit 1
    fi
    
    cd ..
}

# バックエンドサーバーの起動
start_backend() {
    log_info "バックエンドサーバーを起動中..."
    
    cd backend
    
    # バックグラウンドでサーバーを起動
    python3 start_server.py --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
    BACKEND_PID=$!
    
    # PIDを保存
    echo $BACKEND_PID > ../backend.pid
    
    cd ..
    
    log_success "バックエンドサーバーが起動されました (PID: $BACKEND_PID)"
    log_info "ログファイル: backend.log"
    
    # サーバーが起動するまで待機
    log_info "サーバーの起動を待機中..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/ > /dev/null 2>&1; then
            log_success "バックエンドサーバーが正常に起動しました"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "バックエンドサーバーの起動に失敗しました"
            log_info "ログを確認してください: cat backend.log"
            exit 1
        fi
        
        sleep 1
    done
}

# フロントエンドサーバーの起動
start_frontend() {
    log_info "フロントエンドサーバーを起動中..."
    
    cd frontend
    
    # Node.jsが利用可能な場合
    if command -v node &> /dev/null && command -v npm &> /dev/null; then
        log_info "Node.jsを使用してフロントエンドサーバーを起動..."
        
        # 簡易HTTPサーバー（http-server）を使用
        if ! npm list -g http-server > /dev/null 2>&1; then
            log_info "http-serverをインストール中..."
            npm install -g http-server
        fi
        
        http-server public -p 3000 -o --cors > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        
    else
        # Python HTTPサーバーを使用
        log_info "PythonのHTTPサーバーを使用してフロントエンドを提供..."
        
        cd public
        python3 -m http.server 3000 > ../../frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
    fi
    
    # PIDを保存
    echo $FRONTEND_PID > ../frontend.pid
    
    cd ..
    
    log_success "フロントエンドサーバーが起動されました (PID: $FRONTEND_PID)"
    log_info "ログファイル: frontend.log"
}

# プロセス終了処理
cleanup() {
    log_info "アプリケーションを終了中..."
    
    # バックエンドプロセス終了
    if [ -f "backend.pid" ]; then
        BACKEND_PID=$(cat backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            log_info "バックエンドサーバーを終了しました"
        fi
        rm -f backend.pid
    fi
    
    # フロントエンドプロセス終了
    if [ -f "frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            log_info "フロントエンドサーバーを終了しました"
        fi
        rm -f frontend.pid
    fi
    
    log_success "アプリケーションが正常に終了しました"
}

# シグナルハンドラーの設定
trap cleanup EXIT INT TERM

# 引数処理
INSTALL_DEPS=false
DEV_MODE=false
SKIP_VENV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-deps)
            INSTALL_DEPS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --skip-venv)
            SKIP_VENV=true
            shift
            ;;
        --help)
            echo "使用方法: $0 [オプション]"
            echo ""
            echo "オプション:"
            echo "  --install-deps  依存関係を強制的に再インストール"
            echo "  --dev           開発モード（詳細ログ出力）"
            echo "  --skip-venv     仮想環境の作成をスキップ"
            echo "  --help          このヘルプを表示"
            exit 0
            ;;
        *)
            log_error "不明なオプション: $1"
            log_info "使用方法については --help を参照してください"
            exit 1
            ;;
    esac
done

# メイン実行
main() {
    log_info "🚀 Surgi-Motion Visualizer を起動します..."
    
    # 環境チェック
    check_python
    check_node
    
    # 仮想環境セットアップ
    if [ "$SKIP_VENV" = false ]; then
        setup_venv
    fi
    
    # 依存関係インストール
    if [ "$INSTALL_DEPS" = true ] || [ ! -d "./backend/venv" ]; then
        install_backend_deps
    fi
    
    # サーバー起動
    start_backend
    sleep 2  # バックエンドが完全に起動するまで待機
    start_frontend
    
    echo ""
    log_success "🎉 Surgi-Motion Visualizer が正常に起動しました！"
    echo ""
    echo "================================================================="
    echo "📡 アクセス情報:"
    echo "   フロントエンド: http://localhost:3000"
    echo "   バックエンドAPI: http://localhost:8000"
    echo "   API文書: http://localhost:8000/docs"
    echo ""
    echo "📝 ログファイル:"
    echo "   バックエンド: backend.log"
    echo "   フロントエンド: frontend.log"
    echo ""
    echo "🛑 終了するには Ctrl+C を押してください"
    echo "================================================================="
    
    # アプリケーションの実行を継続
    if [ "$DEV_MODE" = true ]; then
        log_info "開発モード: ログを監視中..."
        tail -f backend.log frontend.log
    else
        # プロセスが生きている限り待機
        while ps -p $(cat backend.pid) > /dev/null 2>&1 && ps -p $(cat frontend.pid) > /dev/null 2>&1; do
            sleep 5
        done
        
        log_warning "プロセスの一部が終了しました"
    fi
}

# メイン実行
main