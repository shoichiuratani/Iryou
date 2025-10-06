# System Architecture - Surgi-Motion Visualizer

## 🏗️ システム全体構成

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser Frontend                     │
├─────────────────┬───────────────────┬───────────────────────┤
│   Video Player  │  Control Panel   │    3D Visualizer     │
│                 │                  │     (Three.js)       │
│ - Upload UI     │ - ROI Selector   │                       │
│ - Playback      │ - Analysis Start │ - Hand Skeleton       │
│ - Timeline      │ - Export Options │ - Instrument Model    │
│                 │                  │ - Motion Trails       │
└─────────────────┴───────────────────┴───────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend Server                    │
├─────────────────────────────────────────────────────────────┤
│                     API Endpoints                          │
│ /upload      │ /analyze    │ /tracking  │ /export          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Processing Pipeline                       │
├─────────────────┬───────────────────┬───────────────────────┤
│  Video Decoder  │   Hand Tracking   │ Instrument Tracking  │
│                 │                   │                       │
│ - OpenCV        │ - MediaPipe Hands │ - SAM Segmentation    │
│ - Frame Extract │ - 21 Landmarks    │ - PCA Analysis        │
│ - Preprocessing │ - 3D Coordinates  │ - Pose Estimation     │
└─────────────────┴───────────────────┴───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Storage Layer                       │
├─────────────────┬───────────────────┬───────────────────────┤
│  File Storage   │  Analysis Results │    Export Files      │
│                 │                   │                       │
│ - Uploaded      │ - Hand Landmarks  │ - JSON Output         │
│   Videos        │ - Instrument Data │ - CSV Reports         │
│ - Temp Files    │ - Timestamps      │ - 3D Models           │
└─────────────────┴───────────────────┴───────────────────────┘
```

## 🔄 データフロー

### 1. 動画アップロード・処理フロー
```
User Upload Video → FastAPI → OpenCV Processing → Frame Extraction
                                      ↓
                              Video Validation → Storage
```

### 2. 解析処理フロー
```
ROI Selection → SAM Segmentation → Object Tracking
      ↓              ↓                   ↓
Frame Sequence → MediaPipe → Hand Landmarks → 3D Coordinate
      ↓              ↓                   ↓        Calculation
Instrument Detection → Pose Estimation → Time Series Data
```

### 3. 可視化フロー
```
Analysis Results → JSON API → Three.js Frontend → 3D Rendering
        ↓              ↓           ↓               ↓
Time Series Data → WebSocket → Real-time → Interactive
                   Updates     Animation    Visualization
```

## 📋 主要コンポーネント詳細

### Backend Components

#### 1. API Layer (`/backend/app/`)
- **main.py**: FastAPI アプリケーションのエントリーポイント
- **routers/**: REST APIエンドポイント定義
- **middleware/**: CORS、認証、ログ処理

#### 2. Service Layer (`/backend/services/`)
- **video_service.py**: 動画処理・フレーム抽出
- **hand_tracking_service.py**: MediaPipe Handsによる手指トラッキング
- **instrument_tracking_service.py**: SAM + PCAによる器具トラッキング
- **visualization_service.py**: 3Dデータ変換・整形

#### 3. Model Layer (`/backend/models/`)
- **data_models.py**: Pydanticデータモデル定義
- **tracking_models.py**: トラッキング結果のデータ構造

#### 4. Utility Layer (`/backend/utils/`)
- **video_utils.py**: 動画処理ユーティリティ
- **math_utils.py**: 3D座標変換・回転計算
- **export_utils.py**: データエクスポート機能

### Frontend Components

#### 1. UI Components (`/frontend/src/components/`)
- **VideoPlayer.js**: 動画プレイヤー・タイムライン
- **ROISelector.js**: 器具選択インターフェース
- **Visualizer3D.js**: Three.js 3Dビジュアライザー
- **ControlPanel.js**: 解析操作パネル
- **ExportPanel.js**: データ出力UI

#### 2. Service Layer (`/frontend/src/services/`)
- **api.js**: バックエンドAPI通信
- **three_utils.js**: Three.js関連ユーティリティ
- **data_processor.js**: フロントエンドデータ処理

#### 3. Utility Layer (`/frontend/src/utils/`)
- **constants.js**: 定数定義
- **helpers.js**: 汎用ヘルパー関数

## 🔧 技術仕様詳細

### MediaPipe Hands Integration
```python
# Hand Landmark Detection
landmarks = mediapipe_hands.process(frame)
# 21 points per hand: wrist, thumb(4), fingers(16)
# Output: (x, y, z) coordinates + confidence
```

### SAM Integration
```python
# Object Segmentation
mask = sam_model.predict(
    point_coords=user_click_coords,
    point_labels=[1],  # foreground
    multimask_output=False
)
```

### Three.js 3D Rendering
```javascript
// Hand Skeleton Rendering
const handGeometry = new THREE.BufferGeometry();
handGeometry.setFromPoints(landmarks);
const handMaterial = new THREE.LineBasicMaterial({color: 0x00ff00});
const handMesh = new THREE.Line(handGeometry, handMaterial);
```

## 📊 パフォーマンス考慮事項

### Backend Optimization
- **並列処理**: 手と器具のトラッキングを非同期実行
- **メモリ管理**: フレーム単位でのメモリ解放
- **キャッシュ**: 中間結果のキャッシュ機能

### Frontend Optimization
- **WebGL**: ハードウェアアクセラレーション活用
- **フレームレート制御**: 60FPS維持のための最適化
- **LOD**: 距離に応じた詳細度調整

## 🔒 セキュリティ・プライバシー

### データ保護
- **ローカル処理**: 動画データはローカル環境で処理
- **一時ファイル**: 処理完了後の自動削除
- **アクセス制御**: API認証・認可機能

### HIPAA準拠考慮
- **データ暗号化**: 転送時・保存時の暗号化
- **アクセスログ**: 操作履歴の記録
- **データ匿名化**: 患者情報の自動除去

---
*システム設計 v1.0 - 2024年対応*