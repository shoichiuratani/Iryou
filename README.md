# Surgi-Motion Visualizer 🏥
## 手術手技3D分析ツール

熟練医師の手術手技を撮影した動画から、術者の「手」と「使用器具」の動きを3次元データとして抽出し、インタラクティブに可視化・分析できるWebアプリケーションです。

### 🎯 目的
- 若手医師のトレーニング支援
- 手技の定量的な評価
- 手術技能の標準化と教育

### ✨ 主要機能

#### 1. 動画処理・分析
- 手術動画ファイル（MP4形式）のアップロード
- リアルタイム動画フレーム処理

#### 2. 手のトラッキング 🖐️
- **MediaPipe Hands**を使用した高精度手指トラッキング
- 21個の3Dランドマーク座標（x, y, z）の時系列抽出
- 両手対応

#### 3. 手術器具トラッキング・姿勢推定 ✂️
- **SAM (Segment Anything Model)**による器具セグメンテーション
- ユーザーによるROI指定（1クリック指定）
- 主成分分析（PCA）による器具の向き推定
- 3次元位置・回転ベクトル算出

#### 4. 3Dビジュアライゼーション 🎬
- **Three.js**による高品質3Dレンダリング
- 手のスケルトン表示
- 器具の3Dモデル表示
- 動きの軌跡可視化
- インタラクティブな視点操作

#### 5. データ出力
- 3D座標データのJSON/CSV出力
- 解析レポート生成

### 🏗️ システム構成

```
Surgi-Motion Visualizer/
├── backend/              # Python FastAPI バックエンド
│   ├── app/             # メインアプリケーション
│   ├── models/          # データモデル
│   ├── services/        # ビジネスロジック
│   └── utils/           # ユーティリティ
├── frontend/            # JavaScript フロントエンド
│   ├── src/            # ソースコード
│   ├── public/         # 静的ファイル
│   └── assets/         # アセット
├── docs/               # ドキュメント
└── tests/              # テストコード
```

### 🚀 技術スタック

#### バックエンド
- **Framework**: FastAPI (Python)
- **AI/ML**: MediaPipe, SAM, OpenCV, NumPy
- **Data Processing**: Pandas, scikit-learn

#### フロントエンド
- **3D Graphics**: Three.js
- **UI Framework**: HTML5, CSS3, JavaScript ES6+
- **Video Processing**: Web Video API

#### 主要ライブラリ
- **MediaPipe Hands**: 手指ランドマーク検出
- **SAM (Segment Anything Model)**: オブジェクトセグメンテーション
- **Three.js**: 3Dビジュアライゼーション
- **OpenCV**: 画像・動画処理

### 📋 使用フロー

1. **動画アップロード**: 手術動画をシステムにアップロード
2. **器具指定**: 追跡したい器具を動画上で1クリック指定
3. **自動解析**: AIが手と器具の動きを自動抽出・分析
4. **3D可視化**: 抽出されたデータを3D空間で可視化
5. **データ出力**: 解析結果をJSON/CSV形式で出力

### 🎛️ UI構成

#### 2ペインレイアウト
- **左ペイン**: オリジナル動画プレイヤー + 操作パネル
- **右ペイン**: 3Dビジュアライザー + 分析結果

### 🔧 開発・実行方法

#### バックエンド起動
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### フロントエンド起動
```bash
cd frontend
# 簡単なHTTPサーバーで起動
python -m http.server 3000
```

### 📊 データ形式

#### 手のランドマーク出力例
```json
{
  "timestamp": 0.033,
  "hands": {
    "left": {
      "landmarks": [
        {"x": 0.5, "y": 0.3, "z": -0.1, "id": "wrist"},
        {"x": 0.52, "y": 0.25, "z": -0.08, "id": "thumb_tip"}
      ]
    }
  }
}
```

#### 器具トラッキング出力例
```json
{
  "timestamp": 0.033,
  "instrument": {
    "position": {"x": 150.2, "y": 200.5, "z": -50.3},
    "rotation": {"x": 0.1, "y": 0.8, "z": 0.2},
    "confidence": 0.95
  }
}
```

### 🎓 医療応用

- **教育**: 熟練医師の手技の定量化・標準化
- **評価**: 技能習得度の客観的評価
- **研究**: 手術効率・安全性の向上に向けた研究
- **トレーニング**: VR/AR環境への応用

---
**Version**: 1.0.0  
**Author**: AI Development Team  
**License**: MIT