/**
 * Main Application Entry Point
 * Surgi-Motion Visualizer メインアプリケーション
 */

class SurgiMotionApp {
    constructor() {
        // コンポーネント
        this.videoPlayer = null;
        this.visualizer3D = null;
        this.controlPanel = null;

        // 状態管理
        this.currentSessionId = null;
        this.analysisResults = null;
        this.isAnalysisComplete = false;

        console.log('🚀 Surgi-Motion Visualizer starting...');
    }

    /**
     * アプリケーション初期化
     */
    async init() {
        try {
            // バックエンド接続確認
            await this.checkBackendConnection();

            // コンポーネント初期化
            this.initComponents();

            // イベント設定
            this.setupEventHandlers();

            console.log('✅ Application initialized successfully');

        } catch (error) {
            console.error('❌ Application initialization failed:', error);
            this.showError('アプリケーションの初期化に失敗しました: ' + error.message);
        }
    }

    /**
     * バックエンド接続確認
     */
    async checkBackendConnection() {
        console.log('🔗 Checking backend connection...');
        
        const isHealthy = await apiService.healthCheck();
        
        if (!isHealthy) {
            throw new Error('バックエンドサーバーに接続できません');
        }

        console.log('✅ Backend connection established');
    }

    /**
     * コンポーネント初期化
     */
    initComponents() {
        console.log('🔧 Initializing components...');

        // 動画プレイヤー初期化
        this.videoPlayer = new VideoPlayer();

        // 3D可視化初期化
        this.visualizer3D = new Visualizer3D('three-canvas');

        // コントロールパネル初期化
        this.controlPanel = new ControlPanel();

        console.log('✅ All components initialized');
    }

    /**
     * イベントハンドラー設定
     */
    setupEventHandlers() {
        // 動画プレイヤーイベント
        this.videoPlayer.on('videoLoaded', (sessionData) => {
            this.onVideoLoaded(sessionData);
        });

        this.videoPlayer.on('roiSelected', (roiSelection) => {
            this.onROISelected(roiSelection);
        });

        this.videoPlayer.on('timeUpdate', (currentTime) => {
            this.onVideoTimeUpdate(currentTime);
        });

        // コントロールパネルイベント
        this.controlPanel.on('analysisComplete', (results) => {
            this.onAnalysisComplete(results);
        });

        this.controlPanel.on('statusChange', (status) => {
            this.onStatusChange(status);
        });

        // グローバルイベント
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });

        console.log('📡 Event handlers configured');
    }

    /**
     * 動画読み込み完了処理
     * @param {Object} sessionData - セッションデータ
     */
    onVideoLoaded(sessionData) {
        console.log('📹 Video loaded:', sessionData);

        this.currentSessionId = sessionData.session_id;
        
        // コントロールパネルにセッションIDを設定
        this.controlPanel.setSessionId(this.currentSessionId);

        // APIサービスにもセッションIDを設定
        apiService.setCurrentSessionId(this.currentSessionId);

        this.showMessage(SUCCESS_MESSAGES.UPLOAD_COMPLETE, 'success');
    }

    /**
     * ROI選択完了処理
     * @param {Object} roiSelection - ROI選択データ
     */
    onROISelected(roiSelection) {
        console.log('🎯 ROI selected:', roiSelection);

        // コントロールパネルに通知
        this.controlPanel.onROISelected(roiSelection);

        this.showMessage(SUCCESS_MESSAGES.ROI_SELECTED, 'success');
    }

    /**
     * 動画時間更新処理
     * @param {number} currentTime - 現在時刻
     */
    onVideoTimeUpdate(currentTime) {
        // 解析完了後は3D表示を同期
        if (this.isAnalysisComplete && this.analysisResults) {
            this.syncVisualizationWithVideo(currentTime);
        }
    }

    /**
     * 解析完了処理
     * @param {Object} results - 解析結果
     */
    onAnalysisComplete(results) {
        console.log('🎊 Analysis completed:', results);

        this.analysisResults = results;
        this.isAnalysisComplete = true;

        // 3D可視化に解析データを設定
        this.visualizer3D.setAnalysisData(results);

        // 初期フレームを表示
        this.visualizer3D.updateFrame(0);

        this.showMessage(SUCCESS_MESSAGES.ANALYSIS_COMPLETE, 'success');
    }

    /**
     * ステータス変更処理
     * @param {Object} status - ステータス情報
     */
    onStatusChange(status) {
        // ここでグローバルなステータス表示を更新できます
        if (DEBUG_CONFIG.ENABLED) {
            console.log('📊 Status update:', status);
        }
    }

    /**
     * 3D表示と動画の同期
     * @param {number} videoTime - 動画時刻（秒）
     */
    syncVisualizationWithVideo(videoTime) {
        if (!this.analysisResults || !this.analysisResults.frames) {
            return;
        }

        // 動画時刻に対応するフレーム番号を計算
        const videoMetadata = this.analysisResults.session?.video_metadata;
        const fps = videoMetadata?.fps || 30;
        const targetFrame = Math.floor(videoTime * fps);

        // 解析データ内のフレーム番号と照合
        const frames = this.analysisResults.frames;
        let closestFrameIndex = 0;
        let minDiff = Infinity;

        frames.forEach((frame, index) => {
            const diff = Math.abs(frame.frame_number - targetFrame);
            if (diff < minDiff) {
                minDiff = diff;
                closestFrameIndex = index;
            }
        });

        // 3D表示を更新
        this.visualizer3D.updateFrame(closestFrameIndex);
    }

    /**
     * メッセージ表示
     * @param {string} message - メッセージ
     * @param {string} type - タイプ ('success', 'error', 'info')
     */
    showMessage(message, type = 'info') {
        // 簡易的なメッセージ表示（実際の実装ではトーストライブラリなどを使用）
        const className = type === 'error' ? 'alert-error' : 
                         type === 'success' ? 'alert-success' : 'alert-info';

        // 既存のメッセージがあれば削除
        const existingAlert = document.querySelector('.app-alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        // 新しいメッセージを表示
        const alertDiv = document.createElement('div');
        alertDiv.className = `app-alert ${className}`;
        alertDiv.textContent = message;
        alertDiv.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            background: ${type === 'error' ? '#e74c3c' : 
                        type === 'success' ? '#27ae60' : '#3498db'};
            color: white;
            padding: 15px 20px;
            border-radius: 6px;
            z-index: 1001;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(alertDiv);

        // 3秒後に自動削除
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);

        console.log(`📢 ${type.toUpperCase()}: ${message}`);
    }

    /**
     * エラー表示
     * @param {string} error - エラーメッセージ
     */
    showError(error) {
        this.showMessage(error, 'error');
    }

    /**
     * リセット処理
     */
    reset() {
        console.log('🔄 Resetting application...');

        // 各コンポーネントをリセット
        if (this.videoPlayer) {
            this.videoPlayer.reset();
        }

        if (this.visualizer3D) {
            this.visualizer3D.clearScene();
        }

        if (this.controlPanel) {
            this.controlPanel.reset();
        }

        // 状態クリア
        this.currentSessionId = null;
        this.analysisResults = null;
        this.isAnalysisComplete = false;

        console.log('✅ Application reset complete');
    }

    /**
     * クリーンアップ処理
     */
    cleanup() {
        console.log('🧹 Cleaning up application...');

        if (this.visualizer3D) {
            this.visualizer3D.dispose();
        }

        // その他のリソース解放処理
        console.log('✅ Cleanup complete');
    }

    /**
     * エラーハンドリング
     * @param {Error} error - エラーオブジェクト
     * @param {string} context - エラーのコンテキスト
     */
    handleError(error, context = 'Unknown') {
        console.error(`❌ Error in ${context}:`, error);
        this.showError(`${context}でエラーが発生しました: ${error.message}`);

        // エラー統計（将来の拡張用）
        if (DEBUG_CONFIG.ENABLED) {
            this.logErrorStats(error, context);
        }
    }

    /**
     * エラー統計ログ
     * @param {Error} error - エラーオブジェクト
     * @param {string} context - コンテキスト
     */
    logErrorStats(error, context) {
        const errorInfo = {
            timestamp: new Date().toISOString(),
            context: context,
            message: error.message,
            stack: error.stack,
            userAgent: navigator.userAgent,
            sessionId: this.currentSessionId
        };

        console.table(errorInfo);
    }

    /**
     * パフォーマンス監視
     */
    startPerformanceMonitoring() {
        if (!PERFORMANCE_CONFIG.FPS_MONITOR.enabled) {
            return;
        }

        setInterval(() => {
            const memInfo = performance.memory;
            if (memInfo) {
                const usedMB = Math.round(memInfo.usedJSHeapSize / 1024 / 1024);
                const totalMB = Math.round(memInfo.totalJSHeapSize / 1024 / 1024);

                if (usedMB > PERFORMANCE_CONFIG.MEMORY_MONITOR.warningThreshold / (1024 * 1024)) {
                    console.warn(`⚠️ High memory usage: ${usedMB}MB / ${totalMB}MB`);
                }
            }
        }, PERFORMANCE_CONFIG.MEMORY_MONITOR.updateInterval);
    }
}

/**
 * アプリケーション起動
 */
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // CSS アニメーション定義追加
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            .app-alert {
                animation: slideIn 0.3s ease-out;
            }

            .modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }

            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 10px;
                min-width: 400px;
                max-width: 600px;
            }

            .export-options label {
                display: block;
                margin-bottom: 15px;
            }

            .checkbox-group label {
                display: block;
                margin-bottom: 8px;
            }

            .modal-actions {
                margin-top: 20px;
                text-align: right;
            }

            .modal-actions .btn {
                margin-left: 10px;
            }
        `;
        document.head.appendChild(style);

        // アプリケーション起動
        const app = new SurgiMotionApp();
        await app.init();

        // パフォーマンス監視開始
        app.startPerformanceMonitoring();

        // グローバル変数として公開（デバッグ用）
        window.surgiMotionApp = app;

        console.log('🎉 Surgi-Motion Visualizer is ready!');

    } catch (error) {
        console.error('💥 Application startup failed:', error);
        
        // フォールバック UI表示
        document.body.innerHTML = `
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                flex-direction: column;
                font-family: sans-serif;
                text-align: center;
                color: #e74c3c;
            ">
                <h1>🚨 アプリケーションエラー</h1>
                <p>Surgi-Motion Visualizerの起動に失敗しました。</p>
                <p><strong>エラー:</strong> ${error.message}</p>
                <button onclick="location.reload()" style="
                    margin-top: 20px;
                    padding: 10px 20px;
                    background: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                ">ページを再読み込み</button>
            </div>
        `;
    }
});