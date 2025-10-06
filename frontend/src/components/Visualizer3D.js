/**
 * 3D Visualizer Component
 * Three.jsを使用した3D可視化コンポーネント
 */

class Visualizer3D {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas element with id '${canvasId}' not found`);
        }

        // Three.js基本要素
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera();
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: this.canvas,
            ...THREE_CONFIG.RENDERER 
        });
        this.controls = null;

        // 解析データとアニメーション
        this.analysisData = null;
        this.currentFrame = 0;
        this.isPlaying = false;
        this.animationId = null;

        // オブジェクト管理
        this.handObjects = new Map(); // handType -> Group
        this.instrumentObjects = new Map(); // instrumentId -> Group
        this.trailObjects = new Map(); // objectId -> Line

        // 表示設定
        this.showHands = true;
        this.showInstruments = true;
        this.showTrails = true;

        // パフォーマンス監視
        this.stats = {
            fps: 0,
            lastTime: 0,
            frameCount: 0
        };

        this.init();
        console.log('🎨 3D Visualizer initialized');
    }

    /**
     * 初期化処理
     */
    init() {
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupControls();
        this.setupEventListeners();
        this.startRenderLoop();
    }

    /**
     * シーンの初期設定
     */
    setupScene() {
        this.scene.background = new THREE.Color(VISUALIZATION_CONFIG.COLORS.BACKGROUND);

        // ライティング設定
        ThreeUtils.setupLighting(this.scene);

        // グリッドと座標軸
        const grid = ThreeUtils.createGrid();
        this.scene.add(grid);

        const axes = ThreeUtils.createAxes();
        this.scene.add(axes);
    }

    /**
     * カメラの初期設定
     */
    setupCamera() {
        const config = VISUALIZATION_CONFIG.CAMERA;
        
        this.camera = new THREE.PerspectiveCamera(
            config.FOV,
            this.canvas.clientWidth / this.canvas.clientHeight,
            config.NEAR,
            config.FAR
        );

        this.camera.position.set(
            config.POSITION.x,
            config.POSITION.y,
            config.POSITION.z
        );
    }

    /**
     * レンダラーの初期設定
     */
    setupRenderer() {
        ThreeUtils.setupRenderer(
            this.renderer,
            this.canvas.clientWidth,
            this.canvas.clientHeight
        );
    }

    /**
     * カメラコントロールの設定
     */
    setupControls() {
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            
            const config = THREE_CONFIG.CONTROLS;
            Object.assign(this.controls, config);

            this.controls.update();
        } else {
            console.warn('⚠️ OrbitControls not available');
        }
    }

    /**
     * イベントリスナーの設定
     */
    setupEventListeners() {
        // リサイズ処理
        window.addEventListener('resize', () => this.handleResize());

        // 表示オプション変更
        const showHandsCheckbox = document.getElementById('show-hands');
        if (showHandsCheckbox) {
            showHandsCheckbox.addEventListener('change', (e) => {
                this.showHands = e.target.checked;
                this.updateVisibility();
            });
        }

        const showInstrumentsCheckbox = document.getElementById('show-instruments');
        if (showInstrumentsCheckbox) {
            showInstrumentsCheckbox.addEventListener('change', (e) => {
                this.showInstruments = e.target.checked;
                this.updateVisibility();
            });
        }

        const showTrailsCheckbox = document.getElementById('show-trails');
        if (showTrailsCheckbox) {
            showTrailsCheckbox.addEventListener('change', (e) => {
                this.showTrails = e.target.checked;
                this.updateVisibility();
            });
        }
    }

    /**
     * レンダリングループの開始
     */
    startRenderLoop() {
        const animate = (time) => {
            this.animationId = requestAnimationFrame(animate);
            
            // FPS計算
            this.updateFPS(time);

            // コントロール更新
            if (this.controls) {
                this.controls.update();
            }

            // レンダリング
            this.renderer.render(this.scene, this.camera);

            // パフォーマンス情報更新
            if (PERFORMANCE_CONFIG.FPS_MONITOR.enabled) {
                this.updatePerformanceInfo();
            }
        };

        animate();
    }

    /**
     * 解析データの設定
     * @param {Object} data - 解析結果データ
     */
    setAnalysisData(data) {
        this.analysisData = data;
        this.currentFrame = 0;
        
        console.log('📊 Analysis data loaded:', {
            totalFrames: data.frames?.length || 0,
            session: data.session?.session_id
        });

        // 初期フレームを表示
        this.updateFrame(0);
    }

    /**
     * 指定フレームの表示更新
     * @param {number} frameIndex - フレーム番号
     */
    updateFrame(frameIndex) {
        if (!this.analysisData || !this.analysisData.frames) {
            return;
        }

        const frames = this.analysisData.frames;
        if (frameIndex < 0 || frameIndex >= frames.length) {
            return;
        }

        this.currentFrame = frameIndex;
        const frameData = frames[frameIndex];

        // UI更新
        this.updateAnalysisInfo(frameData);

        // 既存オブジェクトの削除
        this.clearFrame();

        // 手の描画
        if (this.showHands && frameData.hands) {
            this.renderHands(frameData.hands, frameData.timestamp);
        }

        // 器具の描画
        if (this.showInstruments && frameData.instruments) {
            this.renderInstruments(frameData.instruments, frameData.timestamp);
        }

        // 軌跡の更新
        if (this.showTrails) {
            this.updateTrails(frameIndex);
        }
    }

    /**
     * 手の描画
     * @param {Array} handsData - 手のデータ配列
     * @param {number} timestamp - タイムスタンプ
     */
    renderHands(handsData, timestamp) {
        const videoMetadata = this.analysisData.session?.video_metadata;
        const videoWidth = videoMetadata?.width || 640;
        const videoHeight = videoMetadata?.height || 480;

        handsData.forEach((hand) => {
            if (!hand.landmarks || hand.landmarks.length === 0) {
                return;
            }

            // 手のスケルトン作成
            const handSkeleton = ThreeUtils.createHandSkeleton(
                hand.landmarks,
                hand.hand_type,
                videoWidth,
                videoHeight
            );

            this.scene.add(handSkeleton);
            this.handObjects.set(hand.hand_type, handSkeleton);
        });
    }

    /**
     * 器具の描画
     * @param {Array} instrumentsData - 器具のデータ配列
     * @param {number} timestamp - タイムスタンプ
     */
    renderInstruments(instrumentsData, timestamp) {
        const videoMetadata = this.analysisData.session?.video_metadata;
        const videoWidth = videoMetadata?.width || 640;
        const videoHeight = videoMetadata?.height || 480;

        instrumentsData.forEach((instrument) => {
            if (!instrument.pose) {
                return;
            }

            // 器具メッシュ作成
            const instrumentMesh = ThreeUtils.createInstrumentMesh(
                instrument,
                videoWidth,
                videoHeight
            );

            this.scene.add(instrumentMesh);
            this.instrumentObjects.set(instrument.instrument_id, instrumentMesh);
        });
    }

    /**
     * 軌跡の更新
     * @param {number} currentFrameIndex - 現在のフレーム番号
     */
    updateTrails(currentFrameIndex) {
        const trailLength = VISUALIZATION_CONFIG.ANIMATION.TRAIL_LENGTH;
        const startFrame = Math.max(0, currentFrameIndex - trailLength);

        // 手の軌跡を作成
        this.createHandTrails(startFrame, currentFrameIndex);

        // 器具の軌跡を作成
        this.createInstrumentTrails(startFrame, currentFrameIndex);
    }

    /**
     * 手の軌跡作成
     * @param {number} startFrame - 開始フレーム
     * @param {number} endFrame - 終了フレーム
     */
    createHandTrails(startFrame, endFrame) {
        const handTypes = ['Left', 'Right'];
        const videoMetadata = this.analysisData.session?.video_metadata;
        const videoWidth = videoMetadata?.width || 640;
        const videoHeight = videoMetadata?.height || 480;

        handTypes.forEach((handType) => {
            const positions = [];

            for (let i = startFrame; i <= endFrame; i++) {
                const frameData = this.analysisData.frames[i];
                if (!frameData || !frameData.hands) continue;

                const hand = frameData.hands.find(h => h.hand_type === handType);
                if (hand && hand.landmarks && hand.landmarks.length > 0) {
                    // 手首の位置を使用
                    const wrist = hand.landmarks[0]; // WRIST
                    if (wrist && wrist.position) {
                        const pos = ThreeUtils.videoToThreeCoordinates(
                            wrist.position.x,
                            wrist.position.y,
                            wrist.position.z || 0,
                            videoWidth,
                            videoHeight
                        );
                        positions.push(pos);
                    }
                }
            }

            if (positions.length > 1) {
                // 既存の軌跡を削除
                const existingTrail = this.trailObjects.get(`hand_${handType}`);
                if (existingTrail) {
                    this.scene.remove(existingTrail);
                }

                // 新しい軌跡を作成
                const color = handType === 'Left' ? 
                    VISUALIZATION_CONFIG.COLORS.LEFT_HAND : 
                    VISUALIZATION_CONFIG.COLORS.RIGHT_HAND;
                
                const trail = ThreeUtils.createTrailLine(positions, color);
                if (trail) {
                    this.scene.add(trail);
                    this.trailObjects.set(`hand_${handType}`, trail);
                }
            }
        });
    }

    /**
     * 器具の軌跡作成
     * @param {number} startFrame - 開始フレーム
     * @param {number} endFrame - 終了フレーム
     */
    createInstrumentTrails(startFrame, endFrame) {
        const instrumentIds = new Set();
        const videoMetadata = this.analysisData.session?.video_metadata;
        const videoWidth = videoMetadata?.width || 640;
        const videoHeight = videoMetadata?.height || 480;

        // 器具IDを収集
        for (let i = startFrame; i <= endFrame; i++) {
            const frameData = this.analysisData.frames[i];
            if (frameData && frameData.instruments) {
                frameData.instruments.forEach(inst => {
                    instrumentIds.add(inst.instrument_id);
                });
            }
        }

        instrumentIds.forEach((instrumentId) => {
            const positions = [];

            for (let i = startFrame; i <= endFrame; i++) {
                const frameData = this.analysisData.frames[i];
                if (!frameData || !frameData.instruments) continue;

                const instrument = frameData.instruments.find(inst => 
                    inst.instrument_id === instrumentId
                );

                if (instrument && instrument.pose && instrument.pose.position) {
                    const pos = ThreeUtils.videoToThreeCoordinates(
                        instrument.pose.position.x,
                        instrument.pose.position.y,
                        instrument.pose.position.z || 0,
                        videoWidth,
                        videoHeight
                    );
                    positions.push(pos);
                }
            }

            if (positions.length > 1) {
                // 既存の軌跡を削除
                const existingTrail = this.trailObjects.get(`instrument_${instrumentId}`);
                if (existingTrail) {
                    this.scene.remove(existingTrail);
                }

                // 新しい軌跡を作成
                const trail = ThreeUtils.createTrailLine(
                    positions,
                    VISUALIZATION_CONFIG.COLORS.TRAIL
                );
                
                if (trail) {
                    this.scene.add(trail);
                    this.trailObjects.set(`instrument_${instrumentId}`, trail);
                }
            }
        });
    }

    /**
     * フレームのクリア
     */
    clearFrame() {
        // 手オブジェクトの削除
        this.handObjects.forEach((handGroup) => {
            this.scene.remove(handGroup);
        });
        this.handObjects.clear();

        // 器具オブジェクトの削除
        this.instrumentObjects.forEach((instrumentGroup) => {
            this.scene.remove(instrumentGroup);
        });
        this.instrumentObjects.clear();
    }

    /**
     * 表示設定の更新
     */
    updateVisibility() {
        // 手の表示切り替え
        this.handObjects.forEach((handGroup) => {
            handGroup.visible = this.showHands;
        });

        // 器具の表示切り替え
        this.instrumentObjects.forEach((instrumentGroup) => {
            instrumentGroup.visible = this.showInstruments;
        });

        // 軌跡の表示切り替え
        this.trailObjects.forEach((trailLine) => {
            trailLine.visible = this.showTrails;
        });
    }

    /**
     * 解析情報UIの更新
     * @param {Object} frameData - フレームデータ
     */
    updateAnalysisInfo(frameData) {
        const currentFrameEl = document.getElementById('current-frame');
        const handsDetectedEl = document.getElementById('hands-detected');
        const instrumentsDetectedEl = document.getElementById('instruments-detected');

        if (currentFrameEl) {
            currentFrameEl.textContent = `${frameData.frame_number}`;
        }

        if (handsDetectedEl) {
            handsDetectedEl.textContent = `${frameData.hands?.length || 0}`;
        }

        if (instrumentsDetectedEl) {
            instrumentsDetectedEl.textContent = `${frameData.instruments?.length || 0}`;
        }
    }

    /**
     * リサイズ処理
     */
    handleResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    /**
     * FPS計算更新
     * @param {number} time - 現在時刻
     */
    updateFPS(time) {
        this.stats.frameCount++;
        
        if (time - this.stats.lastTime >= 1000) {
            this.stats.fps = this.stats.frameCount;
            this.stats.frameCount = 0;
            this.stats.lastTime = time;
        }
    }

    /**
     * パフォーマンス情報の更新
     */
    updatePerformanceInfo() {
        if (DEBUG_CONFIG.SHOW_PERFORMANCE) {
            const stats = ThreeUtils.getPerformanceStats(this.renderer);
            
            if (this.stats.fps !== this.lastDisplayedFPS) {
                console.log(`🎯 FPS: ${this.stats.fps}, Geometries: ${stats.geometries}, Calls: ${stats.calls}`);
                this.lastDisplayedFPS = this.stats.fps;
            }
        }
    }

    /**
     * カメラリセット
     */
    resetCamera() {
        if (this.controls) {
            this.controls.reset();
        } else {
            const pos = VISUALIZATION_CONFIG.CAMERA.POSITION;
            this.camera.position.set(pos.x, pos.y, pos.z);
            this.camera.lookAt(0, 0, 0);
        }
    }

    /**
     * シーンのクリア
     */
    clearScene() {
        this.clearFrame();
        
        // 軌跡オブジェクトの削除
        this.trailObjects.forEach((trailLine) => {
            this.scene.remove(trailLine);
        });
        this.trailObjects.clear();

        // 解析データのクリア
        this.analysisData = null;
        this.currentFrame = 0;

        console.log('🧹 3D scene cleared');
    }

    /**
     * リソースの解放
     */
    dispose() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        this.clearScene();

        if (this.controls) {
            this.controls.dispose();
        }

        this.renderer.dispose();
        console.log('🗑️ 3D visualizer disposed');
    }

    /**
     * 現在のフレーム番号を取得
     * @returns {number} フレーム番号
     */
    getCurrentFrame() {
        return this.currentFrame;
    }

    /**
     * 総フレーム数を取得
     * @returns {number} 総フレーム数
     */
    getTotalFrames() {
        return this.analysisData?.frames?.length || 0;
    }
}

// グローバルに公開
window.Visualizer3D = Visualizer3D;