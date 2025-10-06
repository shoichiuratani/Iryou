/**
 * Fixed Constants for Sandbox Environment
 * サンドボックス環境用の修正された定数定義
 */

// APIエンドポイント（サンドボックス用URL）
const API_CONFIG = {
    BASE_URL: 'https://8000-ifsp0ufrb6mp7lags2c00-6532622b.e2b.dev',
    ENDPOINTS: {
        UPLOAD: '/api/upload',
        ROI_SELECTION: '/api/roi_selection',
        ANALYZE: '/api/analyze',
        STATUS: '/api/status',
        RESULTS: '/api/results',
        EXPORT: '/api/export'
    }
};

// MediaPipe Handsランドマーク定義
const HAND_LANDMARKS = {
    WRIST: 0,
    THUMB_CMC: 1,
    THUMB_MCP: 2,
    THUMB_IP: 3,
    THUMB_TIP: 4,
    INDEX_FINGER_MCP: 5,
    INDEX_FINGER_PIP: 6,
    INDEX_FINGER_DIP: 7,
    INDEX_FINGER_TIP: 8,
    MIDDLE_FINGER_MCP: 9,
    MIDDLE_FINGER_PIP: 10,
    MIDDLE_FINGER_DIP: 11,
    MIDDLE_FINGER_TIP: 12,
    RING_FINGER_MCP: 13,
    RING_FINGER_PIP: 14,
    RING_FINGER_DIP: 15,
    RING_FINGER_TIP: 16,
    PINKY_MCP: 17,
    PINKY_PIP: 18,
    PINKY_DIP: 19,
    PINKY_TIP: 20
};

// 手指の接続関係（スケルトン描画用）
const HAND_CONNECTIONS = [
    // 親指
    [0, 1], [1, 2], [2, 3], [3, 4],
    // 人差し指
    [0, 5], [5, 6], [6, 7], [7, 8],
    // 中指
    [0, 9], [9, 10], [10, 11], [11, 12],
    // 薬指
    [0, 13], [13, 14], [14, 15], [15, 16],
    // 小指
    [0, 17], [17, 18], [18, 19], [19, 20]
];

// 3Dビジュアライゼーション設定
const VISUALIZATION_CONFIG = {
    // カメラ設定
    CAMERA: {
        FOV: 75,
        NEAR: 0.1,
        FAR: 1000,
        POSITION: {
            x: 0,
            y: 0,
            z: 100
        }
    },
    
    // ライティング設定
    LIGHTING: {
        AMBIENT: {
            color: 0x404040,
            intensity: 0.4
        },
        DIRECTIONAL: {
            color: 0xffffff,
            intensity: 0.8,
            position: {
                x: 10,
                y: 10,
                z: 5
            }
        }
    },
    
    // 色設定
    COLORS: {
        LEFT_HAND: 0x0000ff,    // 青
        RIGHT_HAND: 0xff0000,   // 赤
        INSTRUMENT: 0x00ff00,   // 緑
        TRAIL: 0xffff00,        // 黄
        BACKGROUND: 0x000000    // 黒
    },
    
    // サイズ設定
    SIZES: {
        LANDMARK_SPHERE: 0.8,
        CONNECTION_LINE: 0.3,
        INSTRUMENT_CYLINDER: {
            radius: 0.5,
            height: 20
        },
        TRAIL_LINE: 0.2
    },
    
    // アニメーション設定
    ANIMATION: {
        FRAME_RATE: 30,
        TRAIL_LENGTH: 50,  // 軌跡の長さ（フレーム数）
        SMOOTH_FACTOR: 0.1  // スムージング係数
    }
};

// UI設定
const UI_CONFIG = {
    // ファイルアップロード
    UPLOAD: {
        MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB（サンドボックス用に縮小）
        ALLOWED_TYPES: ['video/mp4', 'video/avi', 'video/mov'],
        DRAG_DROP_TIMEOUT: 100
    },
    
    // 動画プレイヤー
    VIDEO_PLAYER: {
        UPDATE_INTERVAL: 100, // ms
        SEEK_STEP: 1 // seconds
    },
    
    // 処理状況更新
    STATUS_UPDATE: {
        INTERVAL: 1000, // ms
        TIMEOUT: 300000 // 5分
    },
    
    // 3D表示更新
    RENDER_UPDATE: {
        INTERVAL: 33 // ~30fps
    }
};

// エラーメッセージ
const ERROR_MESSAGES = {
    FILE_TOO_LARGE: 'ファイルサイズが大きすぎます（最大100MB）',
    FILE_TYPE_NOT_SUPPORTED: 'サポートされていないファイル形式です',
    UPLOAD_FAILED: 'ファイルのアップロードに失敗しました',
    ANALYSIS_FAILED: '解析処理に失敗しました',
    NETWORK_ERROR: 'ネットワークエラーが発生しました',
    SERVER_ERROR: 'サーバーエラーが発生しました',
    ROI_NOT_SELECTED: 'まず器具を選択してください',
    VIDEO_NOT_LOADED: '動画が読み込まれていません',
    NO_ANALYSIS_DATA: '解析データがありません'
};

// 成功メッセージ
const SUCCESS_MESSAGES = {
    UPLOAD_COMPLETE: '動画のアップロードが完了しました',
    ROI_SELECTED: '器具が選択されました',
    ANALYSIS_COMPLETE: '解析が完了しました（簡易版）',
    EXPORT_COMPLETE: 'データの出力が完了しました'
};

// 処理状況メッセージ
const STATUS_MESSAGES = {
    UPLOADING: 'アップロード中...',
    PROCESSING: '解析処理中...',
    GENERATING_RESULTS: '結果生成中...',
    COMPLETED: '完了',
    FAILED: 'エラー'
};

// デバッグ設定
const DEBUG_CONFIG = {
    ENABLED: true,
    LOG_LEVEL: 'info', // 'debug', 'info', 'warn', 'error'
    SHOW_PERFORMANCE: false, // サンドボックス用に無効化
    SHOW_COORDINATES: true
};

// Three.js関連の追加定数
const THREE_CONFIG = {
    RENDERER: {
        antialias: true,
        alpha: true,
        clearColor: 0x000000,
        clearAlpha: 1.0
    },
    
    CONTROLS: {
        enableDamping: true,
        dampingFactor: 0.05,
        enableZoom: true,
        enablePan: true,
        enableRotate: true,
        autoRotate: false,
        autoRotateSpeed: 2.0,
        minDistance: 10,
        maxDistance: 500
    },
    
    GRID: {
        size: 200,
        divisions: 20,
        colorCenterLine: 0x444444,
        colorGrid: 0x222222
    }
};

// 座標変換設定
const COORDINATE_CONFIG = {
    // 動画座標からThree.js座標への変換
    VIDEO_TO_3D: {
        scale: 0.1,
        offset: {
            x: -50,
            y: 30,
            z: 0
        }
    },
    
    // MediaPipeの正規化座標から実座標への変換
    MEDIAPIPE_SCALE: {
        width: 640,   // 標準幅
        height: 480   // 標準高さ
    }
};

// エクスポート設定
const EXPORT_CONFIG = {
    FORMATS: ['json', 'csv'],
    DEFAULT_FORMAT: 'json',
    FILENAME_PREFIX: 'surgi_motion_analysis',
    INCLUDE_OPTIONS: {
        metadata: true,
        hands: true,
        instruments: true
    }
};

// パフォーマンス監視設定
const PERFORMANCE_CONFIG = {
    FPS_MONITOR: {
        enabled: false, // サンドボックス用に無効化
        updateInterval: 1000
    },
    
    MEMORY_MONITOR: {
        enabled: false, // サンドボックス用に無効化
        updateInterval: 5000,
        warningThreshold: 50 * 1024 * 1024 // 50MB
    }
};

// グローバル変数として公開
window.API_CONFIG = API_CONFIG;
window.HAND_LANDMARKS = HAND_LANDMARKS;
window.HAND_CONNECTIONS = HAND_CONNECTIONS;
window.VISUALIZATION_CONFIG = VISUALIZATION_CONFIG;
window.UI_CONFIG = UI_CONFIG;
window.ERROR_MESSAGES = ERROR_MESSAGES;
window.SUCCESS_MESSAGES = SUCCESS_MESSAGES;
window.STATUS_MESSAGES = STATUS_MESSAGES;
window.DEBUG_CONFIG = DEBUG_CONFIG;
window.THREE_CONFIG = THREE_CONFIG;
window.COORDINATE_CONFIG = COORDINATE_CONFIG;
window.EXPORT_CONFIG = EXPORT_CONFIG;
window.PERFORMANCE_CONFIG = PERFORMANCE_CONFIG;

console.log('✅ Constants loaded for sandbox environment');
console.log('🔗 Backend URL:', API_CONFIG.BASE_URL);