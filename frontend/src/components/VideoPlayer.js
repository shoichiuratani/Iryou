/**
 * Video Player Component
 * 動画プレイヤーとROI選択機能
 */

class VideoPlayer {
    constructor() {
        // DOM要素の取得
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        this.videoContainer = document.getElementById('video-container');
        this.video = document.getElementById('video-player');
        this.videoSource = document.getElementById('video-source');
        
        // コントロール要素
        this.playBtn = document.getElementById('play-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.timeline = document.getElementById('timeline');
        this.timelineProgress = document.getElementById('timeline-progress');
        this.timeDisplay = document.getElementById('time-display');

        // ROI選択関連
        this.roiSelectBtn = document.getElementById('roi-select-btn');
        this.roiInfo = document.getElementById('roi-info');
        this.roiCoordinates = document.getElementById('roi-coordinates');

        // 状態管理
        this.currentFile = null;
        this.sessionId = null;
        this.isROISelectionMode = false;
        this.selectedROI = null;

        // コールバック
        this.onVideoLoaded = null;
        this.onROISelected = null;
        this.onTimeUpdate = null;

        this.init();
        console.log('📹 Video Player initialized');
    }

    /**
     * 初期化
     */
    init() {
        this.setupEventListeners();
        this.setupDragDrop();
    }

    /**
     * イベントリスナーの設定
     */
    setupEventListeners() {
        // ファイル選択
        this.uploadArea?.addEventListener('click', () => this.fileInput?.click());
        this.fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));

        // 動画コントロール
        this.playBtn?.addEventListener('click', () => this.play());
        this.pauseBtn?.addEventListener('click', () => this.pause());
        
        // タイムライン操作
        this.timeline?.addEventListener('click', (e) => this.seek(e));
        this.video?.addEventListener('timeupdate', () => this.updateTimeline());
        this.video?.addEventListener('loadedmetadata', () => this.onVideoMetadataLoaded());
        this.video?.addEventListener('ended', () => this.onVideoEnded());

        // ROI選択
        this.roiSelectBtn?.addEventListener('click', () => this.toggleROISelectionMode());
        this.video?.addEventListener('click', (e) => this.handleVideoClick(e));

        // キーボードショートカット
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    /**
     * ドラッグ&ドロップの設定
     */
    setupDragDrop() {
        if (!this.uploadArea) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.remove('dragover');
            });
        });

        this.uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });
    }

    /**
     * ファイル選択処理
     * @param {Event} event - ファイル選択イベント
     */
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.handleFile(file);
        }
    }

    /**
     * ファイル処理
     * @param {File} file - 選択されたファイル
     */
    async handleFile(file) {
        try {
            console.log('📁 Processing file:', file.name);

            // ファイルバリデーション
            const validation = ApiUtils.validateFile(file);
            if (!validation.valid) {
                alert(validation.errors.join('\n'));
                return;
            }

            this.currentFile = file;

            // プレビュー表示
            const url = URL.createObjectURL(file);
            this.videoSource.src = url;
            this.video.load();

            // UI更新
            this.uploadArea.style.display = 'none';
            this.videoContainer.style.display = 'flex';

            // ファイルアップロード
            await this.uploadToServer(file);

        } catch (error) {
            console.error('❌ File processing error:', error);
            alert(error.message);
        }
    }

    /**
     * サーバーへのアップロード
     * @param {File} file - アップロードするファイル
     */
    async uploadToServer(file) {
        try {
            const sessionData = await apiService.uploadVideo(file);
            this.sessionId = sessionData.session_id;

            // ROI選択ボタンを有効化
            if (this.roiSelectBtn) {
                this.roiSelectBtn.disabled = false;
            }

            // コールバック実行
            if (this.onVideoLoaded) {
                this.onVideoLoaded(sessionData);
            }

            console.log('✅ Video uploaded successfully, session:', this.sessionId);

        } catch (error) {
            console.error('❌ Upload error:', error);
            alert(error.message);
        }
    }

    /**
     * 動画メタデータ読み込み完了時の処理
     */
    onVideoMetadataLoaded() {
        const duration = this.video.duration;
        console.log('📹 Video metadata loaded, duration:', duration);
        
        this.updateTimeDisplay();
    }

    /**
     * 動画再生
     */
    async play() {
        try {
            await this.video.play();
            this.playBtn.style.display = 'none';
            this.pauseBtn.style.display = 'inline-block';
        } catch (error) {
            console.error('❌ Play error:', error);
        }
    }

    /**
     * 動画一時停止
     */
    pause() {
        this.video.pause();
        this.playBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
    }

    /**
     * シーク処理
     * @param {MouseEvent} event - クリックイベント
     */
    seek(event) {
        if (!this.video.duration) return;

        const rect = this.timeline.getBoundingClientRect();
        const percent = (event.clientX - rect.left) / rect.width;
        const time = percent * this.video.duration;
        
        this.video.currentTime = Math.max(0, Math.min(time, this.video.duration));
    }

    /**
     * タイムライン更新
     */
    updateTimeline() {
        if (!this.video.duration) return;

        const percent = (this.video.currentTime / this.video.duration) * 100;
        this.timelineProgress.style.width = `${percent}%`;
        
        this.updateTimeDisplay();

        // 時間更新コールバック
        if (this.onTimeUpdate) {
            this.onTimeUpdate(this.video.currentTime);
        }
    }

    /**
     * 時間表示の更新
     */
    updateTimeDisplay() {
        const current = this.formatTime(this.video.currentTime || 0);
        const total = this.formatTime(this.video.duration || 0);
        
        if (this.timeDisplay) {
            this.timeDisplay.textContent = `${current} / ${total}`;
        }
    }

    /**
     * 時間のフォーマット
     * @param {number} seconds - 秒数
     * @returns {string} フォーマット済み時間
     */
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * ROI選択モードの切り替え
     */
    toggleROISelectionMode() {
        this.isROISelectionMode = !this.isROISelectionMode;
        
        if (this.isROISelectionMode) {
            this.roiSelectBtn.textContent = 'キャンセル';
            this.roiSelectBtn.className = 'btn btn-primary';
            this.video.style.cursor = 'crosshair';
            
            // 動画を一時停止
            this.pause();
            
            alert('動画上で器具をクリックして選択してください');
        } else {
            this.roiSelectBtn.textContent = '器具を選択（動画上でクリック）';
            this.roiSelectBtn.className = 'btn btn-primary';
            this.video.style.cursor = 'default';
        }
    }

    /**
     * 動画クリック処理（ROI選択）
     * @param {MouseEvent} event - クリックイベント
     */
    async handleVideoClick(event) {
        if (!this.isROISelectionMode) return;

        const rect = this.video.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // 動画座標系に変換
        const videoX = (x / rect.width) * this.video.videoWidth;
        const videoY = (y / rect.height) * this.video.videoHeight;

        console.log('🎯 ROI selected:', { x: videoX, y: videoY });

        try {
            // ROI選択データ作成
            const roiSelection = {
                frame_number: Math.floor(this.video.currentTime * 30), // 仮のフレーム番号
                click_position: {
                    x: videoX,
                    y: videoY,
                    z: this.video.currentTime // タイムスタンプをzに設定
                },
                selection_type: 'instrument',
                label: '手術器具'
            };

            // サーバーに送信
            await apiService.setROISelection(this.sessionId, roiSelection);

            this.selectedROI = roiSelection;

            // UI更新
            this.updateROIDisplay(roiSelection);
            
            // ROI選択モードを終了
            this.isROISelectionMode = false;
            this.roiSelectBtn.textContent = '器具が選択済み ✓';
            this.roiSelectBtn.disabled = false;
            this.video.style.cursor = 'default';

            // コールバック実行
            if (this.onROISelected) {
                this.onROISelected(roiSelection);
            }

        } catch (error) {
            console.error('❌ ROI selection error:', error);
            alert(`ROI選択エラー: ${error.message}`);
            this.isROISelectionMode = false;
            this.video.style.cursor = 'default';
        }
    }

    /**
     * ROI表示の更新
     * @param {Object} roiSelection - ROI選択データ
     */
    updateROIDisplay(roiSelection) {
        if (this.roiInfo && this.roiCoordinates) {
            this.roiInfo.style.display = 'block';
            this.roiCoordinates.textContent = 
                `X: ${Math.round(roiSelection.click_position.x)}, ` +
                `Y: ${Math.round(roiSelection.click_position.y)}, ` +
                `時刻: ${this.formatTime(roiSelection.click_position.z)}`;
        }
    }

    /**
     * キーボードショートカット処理
     * @param {KeyboardEvent} event - キーボードイベント
     */
    handleKeyboard(event) {
        if (!this.video || document.activeElement.tagName === 'INPUT') {
            return;
        }

        switch (event.code) {
            case 'Space':
                event.preventDefault();
                if (this.video.paused) {
                    this.play();
                } else {
                    this.pause();
                }
                break;

            case 'ArrowLeft':
                event.preventDefault();
                this.video.currentTime = Math.max(0, this.video.currentTime - 5);
                break;

            case 'ArrowRight':
                event.preventDefault();
                this.video.currentTime = Math.min(
                    this.video.duration, 
                    this.video.currentTime + 5
                );
                break;

            case 'Home':
                event.preventDefault();
                this.video.currentTime = 0;
                break;

            case 'End':
                event.preventDefault();
                this.video.currentTime = this.video.duration;
                break;
        }
    }

    /**
     * 動画終了時の処理
     */
    onVideoEnded() {
        this.playBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
    }

    /**
     * 現在の動画時間を取得
     * @returns {number} 現在時刻（秒）
     */
    getCurrentTime() {
        return this.video?.currentTime || 0;
    }

    /**
     * 動画の総時間を取得
     * @returns {number} 総時間（秒）
     */
    getDuration() {
        return this.video?.duration || 0;
    }

    /**
     * セッションIDを取得
     * @returns {string|null} セッションID
     */
    getSessionId() {
        return this.sessionId;
    }

    /**
     * ROI選択データを取得
     * @returns {Object|null} ROI選択データ
     */
    getSelectedROI() {
        return this.selectedROI;
    }

    /**
     * コールバック設定
     * @param {string} event - イベント名
     * @param {Function} callback - コールバック関数
     */
    on(event, callback) {
        switch (event) {
            case 'videoLoaded':
                this.onVideoLoaded = callback;
                break;
            case 'roiSelected':
                this.onROISelected = callback;
                break;
            case 'timeUpdate':
                this.onTimeUpdate = callback;
                break;
        }
    }

    /**
     * リセット
     */
    reset() {
        // 動画停止
        if (this.video) {
            this.video.pause();
            this.video.currentTime = 0;
        }

        // UI初期化
        this.uploadArea.style.display = 'block';
        this.videoContainer.style.display = 'none';
        
        if (this.roiInfo) {
            this.roiInfo.style.display = 'none';
        }
        
        if (this.roiSelectBtn) {
            this.roiSelectBtn.disabled = true;
            this.roiSelectBtn.textContent = '器具を選択（動画上でクリック）';
        }

        // 状態クリア
        this.currentFile = null;
        this.sessionId = null;
        this.selectedROI = null;
        this.isROISelectionMode = false;

        console.log('🔄 Video player reset');
    }

    /**
     * 指定時刻にシーク
     * @param {number} time - シーク先の時刻（秒）
     */
    seekTo(time) {
        if (this.video && this.video.duration) {
            this.video.currentTime = Math.max(0, Math.min(time, this.video.duration));
        }
    }

    /**
     * 動画の幅・高さを取得
     * @returns {Object} 動画のサイズ
     */
    getVideoSize() {
        return {
            width: this.video?.videoWidth || 0,
            height: this.video?.videoHeight || 0
        };
    }
}

// グローバルに公開
window.VideoPlayer = VideoPlayer;