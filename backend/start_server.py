#!/usr/bin/env python3
"""
Surgi-Motion Visualizer Backend Server Launcher
バックエンドサーバー起動スクリプト
"""

import sys
import os
import subprocess
import argparse
import logging
from pathlib import Path

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
    """Python バージョンチェック"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8以上が必要です")
        sys.exit(1)
    logger.info(f"✅ Python {sys.version} detected")


def install_dependencies():
    """依存関係のインストール"""
    logger.info("📦 Installing dependencies...")
    
    requirements_file = PROJECT_ROOT / "requirements.txt"
    if not requirements_file.exists():
        logger.error("requirements.txt not found")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        logger.info("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e.stderr}")
        return False


def create_directories():
    """必要なディレクトリの作成"""
    dirs = [
        PROJECT_ROOT / "static" / "uploads",
        PROJECT_ROOT / "static" / "exports"
    ]
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Directory created: {directory}")


def check_dependencies():
    """重要な依存関係のチェック"""
    logger.info("🔍 Checking dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "opencv-python",
        "mediapipe",
        "numpy",
        "pandas",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"⚠️ Missing packages: {', '.join(missing_packages)}")
        return False
    
    logger.info("✅ All required packages are available")
    return True


def start_server(host="0.0.0.0", port=8000, reload=True, log_level="info"):
    """サーバーの起動"""
    logger.info(f"🚀 Starting Surgi-Motion Visualizer backend server...")
    logger.info(f"📡 Server will be available at: http://{host}:{port}")
    
    # 環境変数設定
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    
    try:
        # FastAPIサーバー起動
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", host,
            "--port", str(port),
            "--log-level", log_level,
            "--reload" if reload else "--no-reload"
        ], cwd=PROJECT_ROOT, env=env, check=True)
        
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="Surgi-Motion Visualizer Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error"])
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies before starting")
    parser.add_argument("--check-only", action="store_true", help="Only check dependencies and exit")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏥 Surgi-Motion Visualizer Backend Server")
    print("=" * 60)
    
    # Python バージョンチェック
    check_python_version()
    
    # ディレクトリ作成
    create_directories()
    
    # 依存関係のインストール
    if args.install_deps:
        if not install_dependencies():
            sys.exit(1)
    
    # 依存関係チェック
    if not check_dependencies():
        logger.error("❌ Some required packages are missing")
        logger.info("💡 Run with --install-deps to install missing packages")
        if not args.check_only:
            sys.exit(1)
    
    if args.check_only:
        logger.info("✅ Dependency check completed")
        return
    
    # サーバー起動
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()