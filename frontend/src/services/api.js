/**
 * API Service for Surgi-Motion Visualizer
 * バックエンドAPIとの通信を管理
 */

class ApiService {
    constructor() {
        this.baseUrl = API_CONFIG.BASE_URL;
        this.endpoints = API_CONFIG.ENDPOINTS;
        this.currentSessionId = null;
    }

    /**
     * 動画ファイルのアップロード
     * @param {File} file - アップロードする動画ファイル
     * @returns {Promise<Object>} セッション情報
     */
    async uploadVideo(file) {
        try {
            console.log('📤 Uploading video:', file.name);
            
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${this.baseUrl}${this.endpoints.UPLOAD}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
            }

            const sessionData = await response.json();
            this.currentSessionId = sessionData.session_id;
            
            console.log('✅ Video uploaded successfully:', sessionData);
            return sessionData;

        } catch (error) {
            console.error('❌ Video upload error:', error);
            throw new Error(`${ERROR_MESSAGES.UPLOAD_FAILED}: ${error.message}`);
        }
    }

    /**
     * ROI選択情報の送信
     * @param {string} sessionId - セッションID
     * @param {Object} roiSelection - ROI選択データ
     * @returns {Promise<Object>} レスポンス
     */
    async setROISelection(sessionId, roiSelection) {
        try {
            console.log('🎯 Setting ROI selection:', roiSelection);
            
            const response = await fetch(`${this.baseUrl}${this.endpoints.ROI_SELECTION}/${sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(roiSelection)
            });

            if (!response.ok) {
                throw new Error(`ROI selection failed: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ ROI selection set successfully:', result);
            return result;

        } catch (error) {
            console.error('❌ ROI selection error:', error);
            throw new Error(`ROI選択の送信に失敗しました: ${error.message}`);
        }
    }

    /**
     * 解析処理の開始
     * @param {string} sessionId - セッションID
     * @returns {Promise<Object>} レスポンス
     */
    async startAnalysis(sessionId) {
        try {
            console.log('🚀 Starting analysis for session:', sessionId);
            
            const response = await fetch(`${this.baseUrl}${this.endpoints.ANALYZE}/${sessionId}`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Analysis start failed: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ Analysis started successfully:', result);
            return result;

        } catch (error) {
            console.error('❌ Analysis start error:', error);
            throw new Error(`${ERROR_MESSAGES.ANALYSIS_FAILED}: ${error.message}`);
        }
    }

    /**
     * 処理状況の取得
     * @param {string} sessionId - セッションID
     * @returns {Promise<Object>} 処理状況
     */
    async getProcessingStatus(sessionId) {
        try {
            const response = await fetch(`${this.baseUrl}${this.endpoints.STATUS}/${sessionId}`);

            if (!response.ok) {
                throw new Error(`Status check failed: ${response.status}`);
            }

            const status = await response.json();
            return status;

        } catch (error) {
            console.error('❌ Status check error:', error);
            throw new Error(`処理状況の取得に失敗しました: ${error.message}`);
        }
    }

    /**
     * 解析結果の取得
     * @param {string} sessionId - セッションID
     * @returns {Promise<Object>} 解析結果
     */
    async getAnalysisResults(sessionId) {
        try {
            console.log('📊 Fetching analysis results for session:', sessionId);
            
            const response = await fetch(`${this.baseUrl}${this.endpoints.RESULTS}/${sessionId}`);

            if (!response.ok) {
                throw new Error(`Results fetch failed: ${response.status}`);
            }

            const results = await response.json();
            console.log('✅ Analysis results fetched successfully');
            return results;

        } catch (error) {
            console.error('❌ Results fetch error:', error);
            throw new Error(`解析結果の取得に失敗しました: ${error.message}`);
        }
    }

    /**
     * データの出力
     * @param {Object} exportRequest - 出力リクエスト
     * @returns {Promise<Blob>} 出力ファイル
     */
    async exportData(exportRequest) {
        try {
            console.log('📤 Exporting data:', exportRequest);
            
            const response = await fetch(`${this.baseUrl}${this.endpoints.EXPORT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(exportRequest)
            });

            if (!response.ok) {
                throw new Error(`Export failed: ${response.status}`);
            }

            const blob = await response.blob();
            console.log('✅ Data exported successfully');
            return blob;

        } catch (error) {
            console.error('❌ Export error:', error);
            throw new Error(`データ出力に失敗しました: ${error.message}`);
        }
    }

    /**
     * 処理状況の継続的な監視
     * @param {string} sessionId - セッションID
     * @param {Function} onProgress - 進捗コールバック
     * @param {Function} onComplete - 完了コールバック
     * @param {Function} onError - エラーコールバック
     */
    async monitorAnalysisProgress(sessionId, onProgress, onComplete, onError) {
        const startTime = Date.now();
        const maxWaitTime = UI_CONFIG.STATUS_UPDATE.TIMEOUT;
        
        const checkStatus = async () => {
            try {
                const status = await this.getProcessingStatus(sessionId);
                
                // 進捗コールバック実行
                if (onProgress) {
                    onProgress(status);
                }
                
                // 完了判定
                if (status.status === 'completed') {
                    console.log('✅ Analysis completed');
                    if (onComplete) {
                        const results = await this.getAnalysisResults(sessionId);
                        onComplete(results);
                    }
                    return;
                }
                
                // エラー判定
                if (status.status === 'failed') {
                    const error = new Error(status.error || '解析処理に失敗しました');
                    if (onError) {
                        onError(error);
                    }
                    return;
                }
                
                // タイムアウト判定
                if (Date.now() - startTime > maxWaitTime) {
                    const error = new Error('解析処理がタイムアウトしました');
                    if (onError) {
                        onError(error);
                    }
                    return;
                }
                
                // 処理中の場合は継続
                if (status.status === 'processing') {
                    setTimeout(checkStatus, UI_CONFIG.STATUS_UPDATE.INTERVAL);
                }
                
            } catch (error) {
                console.error('❌ Status monitoring error:', error);
                if (onError) {
                    onError(error);
                }
            }
        };
        
        // 監視開始
        checkStatus();
    }

    /**
     * ヘルスチェック
     * @returns {Promise<boolean>} サーバーの稼働状況
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/`);
            return response.ok;
        } catch (error) {
            console.error('❌ Health check failed:', error);
            return false;
        }
    }

    /**
     * ファイルダウンロード用のヘルパー関数
     * @param {Blob} blob - ダウンロードするファイル
     * @param {string} filename - ファイル名
     */
    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    /**
     * セッションIDのゲッター
     * @returns {string|null} 現在のセッションID
     */
    getCurrentSessionId() {
        return this.currentSessionId;
    }

    /**
     * セッションIDのセッター
     * @param {string} sessionId - セッションID
     */
    setCurrentSessionId(sessionId) {
        this.currentSessionId = sessionId;
    }
}

// ユーティリティ関数
class ApiUtils {
    /**
     * ファイルサイズの妥当性チェック
     * @param {File} file - チェックするファイル
     * @returns {boolean} 妥当性
     */
    static validateFileSize(file) {
        return file.size <= UI_CONFIG.UPLOAD.MAX_FILE_SIZE;
    }

    /**
     * ファイルタイプの妥当性チェック
     * @param {File} file - チェックするファイル
     * @returns {boolean} 妥当性
     */
    static validateFileType(file) {
        return UI_CONFIG.UPLOAD.ALLOWED_TYPES.includes(file.type);
    }

    /**
     * ファイルの完全な妥当性チェック
     * @param {File} file - チェックするファイル
     * @returns {Object} チェック結果
     */
    static validateFile(file) {
        const result = {
            valid: true,
            errors: []
        };

        if (!this.validateFileType(file)) {
            result.valid = false;
            result.errors.push(ERROR_MESSAGES.FILE_TYPE_NOT_SUPPORTED);
        }

        if (!this.validateFileSize(file)) {
            result.valid = false;
            result.errors.push(ERROR_MESSAGES.FILE_TOO_LARGE);
        }

        return result;
    }

    /**
     * エラーレスポンスの処理
     * @param {Response} response - レスポンスオブジェクト
     * @returns {Promise<Error>} エラーオブジェクト
     */
    static async handleErrorResponse(response) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = errorData.detail;
            }
        } catch (e) {
            // JSON解析失敗時は元のメッセージを使用
        }
        
        return new Error(errorMessage);
    }
}

// グローバルに公開
window.ApiService = ApiService;
window.ApiUtils = ApiUtils;

// インスタンス作成（グローバルで利用可能）
window.apiService = new ApiService();