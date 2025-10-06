/**
 * Control Panel Component
 * 解析制御とステータス管理
 */

class ControlPanel {
    constructor() {
        // DOM要素
        this.startAnalysisBtn = document.getElementById('start-analysis-btn');
        this.exportBtn = document.getElementById('export-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.progressFill = document.getElementById('progress-fill');

        // 状態管理
        this.currentStatus = 'idle';
        this.currentProgress = 0;
        this.sessionId = null;
        this.analysisResults = null;

        // コールバック
        this.onAnalysisComplete = null;
        this.onStatusChange = null;

        this.init();
        console.log('🎛️ Control Panel initialized');
    }

    /**
     * 初期化
     */
    init() {
        this.setupEventListeners();
        this.updateUI();
    }

    /**
     * イベントリスナーの設定
     */
    setupEventListeners() {
        // 解析開始ボタン
        this.startAnalysisBtn?.addEventListener('click', () => this.startAnalysis());

        // エクスポートボタン
        this.exportBtn?.addEventListener('click', () => this.showExportModal());

        // リセットボタン
        this.resetBtn?.addEventListener('click', () => this.reset());
    }

    /**
     * 解析処理の開始
     */
    async startAnalysis() {
        if (!this.sessionId) {
            alert(ERROR_MESSAGES.VIDEO_NOT_LOADED);
            return;
        }

        try {
            console.log('🚀 Starting analysis process...');
            
            // UI状態を解析中に変更
            this.updateStatus('processing', 0, STATUS_MESSAGES.PROCESSING);
            this.startAnalysisBtn.disabled = true;

            // 解析開始API呼び出し
            await apiService.startAnalysis(this.sessionId);

            // 進捗監視開始
            this.startProgressMonitoring();

        } catch (error) {
            console.error('❌ Analysis start error:', error);
            this.updateStatus('failed', 0, error.message);
            this.startAnalysisBtn.disabled = false;
        }
    }

    /**
     * 進捗監視の開始
     */
    startProgressMonitoring() {
        apiService.monitorAnalysisProgress(
            this.sessionId,
            (status) => this.onProgressUpdate(status),
            (results) => this.onAnalysisCompleted(results),
            (error) => this.onAnalysisError(error)
        );
    }

    /**
     * 進捗更新処理
     * @param {Object} status - 進捗ステータス
     */
    onProgressUpdate(status) {
        const progress = status.progress || 0;
        const message = status.message || STATUS_MESSAGES.PROCESSING;
        
        this.updateStatus('processing', progress, message);
        
        console.log(`📊 Analysis progress: ${Math.round(progress * 100)}%`);

        // ステータス変更コールバック
        if (this.onStatusChange) {
            this.onStatusChange(status);
        }
    }

    /**
     * 解析完了処理
     * @param {Object} results - 解析結果
     */
    onAnalysisCompleted(results) {
        console.log('✅ Analysis completed successfully');
        
        this.analysisResults = results;
        this.updateStatus('completed', 1.0, STATUS_MESSAGES.COMPLETED);
        
        // UIの更新
        this.exportBtn.style.display = 'inline-block';
        
        // 完了コールバック
        if (this.onAnalysisComplete) {
            this.onAnalysisComplete(results);
        }
    }

    /**
     * 解析エラー処理
     * @param {Error} error - エラーオブジェクト
     */
    onAnalysisError(error) {
        console.error('❌ Analysis failed:', error);
        
        this.updateStatus('failed', 0, `${STATUS_MESSAGES.FAILED}: ${error.message}`);
        this.startAnalysisBtn.disabled = false;
    }

    /**
     * ステータス更新
     * @param {string} status - ステータス
     * @param {number} progress - 進捗（0-1）
     * @param {string} message - メッセージ
     */
    updateStatus(status, progress = 0, message = '') {
        this.currentStatus = status;
        this.currentProgress = progress;

        // プログレスバーの更新
        if (this.progressFill) {
            this.progressFill.style.width = `${progress * 100}%`;
        }

        // ステータステキストの更新
        if (this.statusText) {
            this.statusText.textContent = message;
        }

        // ステータスインジケーターの表示制御
        if (this.statusIndicator) {
            if (status === 'processing') {
                this.statusIndicator.style.display = 'block';
            } else if (status === 'completed' || status === 'failed') {
                // 2秒後に非表示
                setTimeout(() => {
                    this.statusIndicator.style.display = 'none';
                }, 2000);
            } else {
                this.statusIndicator.style.display = 'none';
            }
        }

        this.updateUI();
    }

    /**
     * UI状態の更新
     */
    updateUI() {
        // 解析開始ボタンの状態
        if (this.startAnalysisBtn) {
            const canStartAnalysis = this.sessionId && 
                                   this.currentStatus !== 'processing' && 
                                   this.currentStatus !== 'completed';
            
            this.startAnalysisBtn.disabled = !canStartAnalysis;
        }

        // エクスポートボタンの状態
        if (this.exportBtn) {
            this.exportBtn.style.display = 
                this.currentStatus === 'completed' ? 'inline-block' : 'none';
        }
    }

    /**
     * エクスポートモーダルの表示
     */
    showExportModal() {
        if (!this.analysisResults) {
            alert(ERROR_MESSAGES.NO_ANALYSIS_DATA);
            return;
        }

        // 簡易的なエクスポート設定ダイアログ
        const format = this.showFormatSelectionDialog();
        if (format) {
            this.exportData(format);
        }
    }

    /**
     * フォーマット選択ダイアログ
     * @returns {string|null} 選択されたフォーマット
     */
    showFormatSelectionDialog() {
        const formats = EXPORT_CONFIG.FORMATS;
        const formatOptions = formats.map((fmt, index) => 
            `${index + 1}. ${fmt.toUpperCase()}`
        ).join('\n');

        const choice = prompt(
            `エクスポート形式を選択してください:\n\n${formatOptions}\n\n番号を入力してください (1-${formats.length}):`
        );

        if (choice) {
            const index = parseInt(choice) - 1;
            if (index >= 0 && index < formats.length) {
                return formats[index];
            }
        }

        return null;
    }

    /**
     * データエクスポート
     * @param {string} format - エクスポート形式
     */
    async exportData(format) {
        try {
            console.log('📤 Exporting data in format:', format);

            const exportRequest = {
                session_id: this.sessionId,
                format: format,
                include_metadata: true,
                include_hands: true,
                include_instruments: true
            };

            // エクスポート実行
            const blob = await apiService.exportData(exportRequest);

            // ファイルダウンロード
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:.]/g, '-');
            const filename = `${EXPORT_CONFIG.FILENAME_PREFIX}_${timestamp}.${format}`;
            
            apiService.downloadFile(blob, filename);

            console.log('✅ Data exported successfully:', filename);
            alert(SUCCESS_MESSAGES.EXPORT_COMPLETE);

        } catch (error) {
            console.error('❌ Export error:', error);
            alert(`エクスポートエラー: ${error.message}`);
        }
    }

    /**
     * セッションIDの設定
     * @param {string} sessionId - セッションID
     */
    setSessionId(sessionId) {
        this.sessionId = sessionId;
        console.log('🆔 Session ID set:', sessionId);
        this.updateUI();
    }

    /**
     * ROI選択の確認
     * @param {Object} roiSelection - ROI選択データ
     */
    onROISelected(roiSelection) {
        console.log('🎯 ROI selection confirmed:', roiSelection);
        this.updateUI();
    }

    /**
     * リセット処理
     */
    reset() {
        if (this.currentStatus === 'processing') {
            const confirm = window.confirm('解析処理中です。リセットしますか？');
            if (!confirm) {
                return;
            }
        }

        console.log('🔄 Resetting control panel...');

        // 状態クリア
        this.sessionId = null;
        this.analysisResults = null;
        this.currentStatus = 'idle';
        this.currentProgress = 0;

        // UI初期化
        this.updateStatus('idle', 0, '');
        
        if (this.startAnalysisBtn) {
            this.startAnalysisBtn.disabled = true;
        }
        
        if (this.exportBtn) {
            this.exportBtn.style.display = 'none';
        }

        console.log('✅ Control panel reset complete');
    }

    /**
     * コールバック設定
     * @param {string} event - イベント名
     * @param {Function} callback - コールバック関数
     */
    on(event, callback) {
        switch (event) {
            case 'analysisComplete':
                this.onAnalysisComplete = callback;
                break;
            case 'statusChange':
                this.onStatusChange = callback;
                break;
        }
    }

    /**
     * 現在のステータス取得
     * @returns {string} 現在のステータス
     */
    getStatus() {
        return this.currentStatus;
    }

    /**
     * 現在の進捗取得
     * @returns {number} 進捗（0-1）
     */
    getProgress() {
        return this.currentProgress;
    }

    /**
     * 解析結果の取得
     * @returns {Object|null} 解析結果
     */
    getAnalysisResults() {
        return this.analysisResults;
    }
}

/**
 * エクスポート設定モーダル（将来の拡張用）
 */
class ExportModal {
    constructor() {
        this.modal = null;
        this.createModal();
    }

    /**
     * モーダルHTML作成
     */
    createModal() {
        const modalHTML = `
        <div id="export-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <h3>📤 データエクスポート設定</h3>
                
                <div class="export-options">
                    <label>
                        <strong>フォーマット:</strong>
                        <select id="export-format">
                            <option value="json">JSON</option>
                            <option value="csv">CSV</option>
                            <option value="xlsx">Excel</option>
                        </select>
                    </label>

                    <div class="checkbox-group">
                        <label><input type="checkbox" id="include-metadata" checked> メタデータを含める</label>
                        <label><input type="checkbox" id="include-hands" checked> 手のデータを含める</label>
                        <label><input type="checkbox" id="include-instruments" checked> 器具のデータを含める</label>
                    </div>

                    <label>
                        <strong>フレーム範囲:</strong>
                        開始: <input type="number" id="start-frame" min="0" value="0">
                        終了: <input type="number" id="end-frame" min="0" value="-1">
                    </label>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-primary" id="export-confirm">エクスポート</button>
                    <button class="btn" id="export-cancel">キャンセル</button>
                </div>
            </div>
        </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modal = document.getElementById('export-modal');
        this.setupModalEvents();
    }

    /**
     * モーダルイベント設定
     */
    setupModalEvents() {
        const confirmBtn = document.getElementById('export-confirm');
        const cancelBtn = document.getElementById('export-cancel');

        confirmBtn?.addEventListener('click', () => this.onConfirm());
        cancelBtn?.addEventListener('click', () => this.hide());

        // モーダル外クリックで閉じる
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });
    }

    /**
     * モーダル表示
     * @param {Object} defaultSettings - デフォルト設定
     */
    show(defaultSettings = {}) {
        if (this.modal) {
            this.modal.style.display = 'flex';
            
            // デフォルト値設定
            if (defaultSettings.totalFrames) {
                const endFrameInput = document.getElementById('end-frame');
                if (endFrameInput) {
                    endFrameInput.value = defaultSettings.totalFrames;
                    endFrameInput.max = defaultSettings.totalFrames;
                }
            }
        }
    }

    /**
     * モーダル非表示
     */
    hide() {
        if (this.modal) {
            this.modal.style.display = 'none';
        }
    }

    /**
     * 確認処理
     */
    onConfirm() {
        const settings = this.getExportSettings();
        
        if (this.onExport) {
            this.onExport(settings);
        }
        
        this.hide();
    }

    /**
     * エクスポート設定取得
     * @returns {Object} エクスポート設定
     */
    getExportSettings() {
        return {
            format: document.getElementById('export-format')?.value || 'json',
            include_metadata: document.getElementById('include-metadata')?.checked || false,
            include_hands: document.getElementById('include-hands')?.checked || false,
            include_instruments: document.getElementById('include-instruments')?.checked || false,
            frame_range: {
                start: parseInt(document.getElementById('start-frame')?.value || '0'),
                end: parseInt(document.getElementById('end-frame')?.value || '-1')
            }
        };
    }

    /**
     * エクスポートコールバック設定
     * @param {Function} callback - コールバック関数
     */
    onExportCallback(callback) {
        this.onExport = callback;
    }
}

// グローバルに公開
window.ControlPanel = ControlPanel;
window.ExportModal = ExportModal;