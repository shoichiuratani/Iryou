# Deployment Guide - Surgi-Motion Visualizer

## 🚀 デプロイメント・実行ガイド

### 📋 システム要件

#### 最小要件
- **OS**: Linux/macOS/Windows 10+
- **Python**: 3.8以上
- **RAM**: 4GB以上（8GB推奨）
- **ストレージ**: 2GB以上の空き容量
- **GPU**: CUDA対応GPU（推奨、CPUでも動作）

#### 推奨要件
- **Python**: 3.9以上
- **RAM**: 16GB以上
- **GPU**: NVIDIA GPU with 4GB+ VRAM
- **ストレージ**: SSD 5GB以上

### 📦 インストール・セットアップ

#### 1. リポジトリのクローン/ダウンロード
```bash
# GitHubからクローン（例）
git clone https://github.com/your-org/surgi-motion-visualizer.git
cd surgi-motion-visualizer

# または、ファイルを直接配置
```

#### 2. 自動セットアップ（推奨）
```bash
# 一括起動スクリプト実行
./start_app.sh --install-deps

# 初回実行時は依存関係が自動インストールされます
```

#### 3. 手動セットアップ
```bash
# Python仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# バックエンド依存関係インストール
cd backend
pip install -r requirements.txt

# フロントエンド用HTTPサーバー（オプション）
npm install -g http-server  # Node.jsがある場合
```

### 🏃 実行方法

#### 方法1: 統合起動スクリプト（推奨）
```bash
# 基本起動
./start_app.sh

# 開発モード（詳細ログ）
./start_app.sh --dev

# 依存関係再インストール
./start_app.sh --install-deps

# ヘルプ表示
./start_app.sh --help
```

#### 方法2: 個別起動
```bash
# ターミナル1: バックエンドサーバー
cd backend
python3 start_server.py

# ターミナル2: フロントエンドサーバー
cd frontend/public
python3 -m http.server 3000
```

### 🌐 アクセス方法

起動完了後、以下のURLにアクセス:

- **メインアプリケーション**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API文書（Swagger）**: http://localhost:8000/docs
- **API文書（ReDoc）**: http://localhost:8000/redoc

### 🔧 設定・カスタマイズ

#### ポート変更
```bash
# バックエンドポート変更
cd backend
python3 start_server.py --port 8080

# フロントエンドポート変更
cd frontend/public
python3 -m http.server 3001
```

#### 設定ファイル
- **バックエンド設定**: `backend/app/main.py`
- **フロントエンド設定**: `frontend/src/utils/constants.js`

### 📊 使用方法

#### 基本ワークフロー
1. **動画アップロード**
   - 手術動画ファイル（MP4推奨）をドラッグ&ドロップ
   - 最大ファイルサイズ: 500MB

2. **器具選択**
   - 動画再生中に「器具を選択」ボタンをクリック
   - 追跡したい器具を動画上でクリック

3. **解析実行**
   - 「解析開始」ボタンをクリック
   - 進捗バーで処理状況を確認

4. **3D可視化**
   - 右パネルで3D解析結果を表示
   - 動画再生と3D表示が同期

5. **データ出力**
   - 解析完了後、「データ出力」ボタンでエクスポート
   - JSON、CSV、Excelフォーマット対応

### 🐛 トラブルシューティング

#### よくある問題と解決方法

##### 1. Python関連エラー
```bash
# 問題: ModuleNotFoundError
# 解決: 仮想環境の確認と依存関係再インストール
source venv/bin/activate
pip install -r backend/requirements.txt

# 問題: Python バージョンエラー
# 解決: Python 3.8以上をインストール
python3 --version
```

##### 2. メモリエラー
```bash
# 問題: Out of Memory
# 解決: 動画サイズの縮小、またはRAM増設
# 一時的対策: 小さい動画でテスト
```

##### 3. GPU関連エラー
```bash
# 問題: CUDA not available
# 解決: CPU版PyTorchを使用（自動フォールバック）
# MediaPipeはCPUでも高速動作
```

##### 4. ポート競合エラー
```bash
# 問題: Port already in use
# 解決: 他のポートを使用
python3 start_server.py --port 8001

# 使用中ポート確認
netstat -tlnp | grep :8000
```

##### 5. CORS エラー
```bash
# 問題: Cross-Origin Request Blocked
# 解決: 
# 1. フロントエンドとバックエンドを同じマシンで実行
# 2. backend/app/main.py のCORS設定を確認
```

##### 6. ファイルアップロードエラー
```bash
# 問題: File upload failed
# 解決:
# 1. ファイルサイズ確認（最大500MB）
# 2. ファイル形式確認（MP4推奨）
# 3. ディスクスペース確認
```

### 📈 パフォーマンス最適化

#### 1. ハードウェア最適化
- **GPU使用**: CUDA対応GPUを使用
- **RAM**: 16GB以上を推奨
- **ストレージ**: SSDを推奨

#### 2. ソフトウェア最適化
```bash
# OpenCVの最適化
export OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS=0

# NumPyスレッド数制限
export OMP_NUM_THREADS=4
```

#### 3. 動画前処理
- 解像度を1080p以下に縮小
- フレームレートを30fps以下に設定
- 不要な部分をトリミング

### 🔒 セキュリティ考慮事項

#### 本番環境への展開時
1. **認証・認可の実装**
2. **HTTPS通信の設定**
3. **ファイルアップロード制限の強化**
4. **ログ監視の実装**
5. **定期的なセキュリティ更新**

### 📝 ログ・監視

#### ログファイル場所
- **バックエンドログ**: `backend.log`
- **フロントエンドログ**: `frontend.log`

#### ログレベル設定
```bash
# 詳細ログ出力
python3 start_server.py --log-level debug

# エラーのみ
python3 start_server.py --log-level error
```

### 🔄 更新・メンテナンス

#### アプリケーション更新
```bash
# コードの更新
git pull origin main

# 依存関係の更新
./start_app.sh --install-deps
```

#### 定期メンテナンス
- ログファイルのローテーション
- 一時ファイルの削除
- データベースの最適化（将来実装時）

### 🆘 サポート・問い合わせ

#### 技術サポート
- **ドキュメント**: `docs/` ディレクトリ
- **システム設計**: `docs/system_architecture.md`
- **API仕様**: http://localhost:8000/docs

#### 問題報告
1. エラーメッセージの記録
2. ログファイルの確認
3. システム環境情報の収集
4. 再現手順の記録

### 📚 関連ドキュメント
- [システム設計書](system_architecture.md)
- [README](../README.md)
- [API仕様](http://localhost:8000/docs)

---

*最終更新: 2024年10月*