/**
 * Three.js Utilities for Surgi-Motion Visualizer
 * Three.js関連のユーティリティクラス
 */

class ThreeUtils {
    /**
     * 座標変換：動画座標からThree.js 3D座標へ
     * @param {number} x - 動画X座標
     * @param {number} y - 動画Y座標
     * @param {number} z - 動画Z座標（奥行き）
     * @param {number} videoWidth - 動画幅
     * @param {number} videoHeight - 動画高さ
     * @returns {THREE.Vector3} Three.js座標
     */
    static videoToThreeCoordinates(x, y, z = 0, videoWidth = 640, videoHeight = 480) {
        const config = COORDINATE_CONFIG.VIDEO_TO_3D;
        
        // 動画座標を正規化（0-1範囲）
        const normalizedX = x / videoWidth;
        const normalizedY = y / videoHeight;
        
        // Three.js座標系に変換（中央を原点とし、Y軸を反転）
        const threeX = (normalizedX - 0.5) * videoWidth * config.scale;
        const threeY = -(normalizedY - 0.5) * videoHeight * config.scale;
        const threeZ = z * config.scale;
        
        return new THREE.Vector3(
            threeX + config.offset.x,
            threeY + config.offset.y,
            threeZ + config.offset.z
        );
    }

    /**
     * 手のスケルトンメッシュ作成
     * @param {Array} landmarks - ランドマーク配列
     * @param {string} handType - 手の種類（Left/Right）
     * @param {number} videoWidth - 動画幅
     * @param {number} videoHeight - 動画高さ
     * @returns {THREE.Group} 手のスケルトングループ
     */
    static createHandSkeleton(landmarks, handType, videoWidth = 640, videoHeight = 480) {
        const handGroup = new THREE.Group();
        const color = handType === 'Left' ? 
            VISUALIZATION_CONFIG.COLORS.LEFT_HAND : 
            VISUALIZATION_CONFIG.COLORS.RIGHT_HAND;

        // ランドマーク点の作成
        const sphereGeometry = new THREE.SphereGeometry(VISUALIZATION_CONFIG.SIZES.LANDMARK_SPHERE, 8, 6);
        const sphereMaterial = new THREE.MeshLambertMaterial({ color: color });

        landmarks.forEach((landmark, index) => {
            if (landmark && landmark.position) {
                const position = this.videoToThreeCoordinates(
                    landmark.position.x,
                    landmark.position.y,
                    landmark.position.z || 0,
                    videoWidth,
                    videoHeight
                );

                const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
                sphere.position.copy(position);
                sphere.userData = {
                    landmarkId: landmark.id,
                    landmarkName: landmark.name,
                    handType: handType
                };

                handGroup.add(sphere);
            }
        });

        // 接続線の作成
        const lineMaterial = new THREE.LineBasicMaterial({ 
            color: color,
            linewidth: VISUALIZATION_CONFIG.SIZES.CONNECTION_LINE
        });

        HAND_CONNECTIONS.forEach(([startIdx, endIdx]) => {
            if (landmarks[startIdx] && landmarks[endIdx] &&
                landmarks[startIdx].position && landmarks[endIdx].position) {
                
                const startPos = this.videoToThreeCoordinates(
                    landmarks[startIdx].position.x,
                    landmarks[startIdx].position.y,
                    landmarks[startIdx].position.z || 0,
                    videoWidth,
                    videoHeight
                );

                const endPos = this.videoToThreeCoordinates(
                    landmarks[endIdx].position.x,
                    landmarks[endIdx].position.y,
                    landmarks[endIdx].position.z || 0,
                    videoWidth,
                    videoHeight
                );

                const geometry = new THREE.BufferGeometry().setFromPoints([startPos, endPos]);
                const line = new THREE.Line(geometry, lineMaterial);
                line.userData = {
                    connection: [startIdx, endIdx],
                    handType: handType
                };

                handGroup.add(line);
            }
        });

        handGroup.userData = {
            type: 'hand',
            handType: handType
        };

        return handGroup;
    }

    /**
     * 器具メッシュの作成
     * @param {Object} instrumentData - 器具データ
     * @param {number} videoWidth - 動画幅
     * @param {number} videoHeight - 動画高さ
     * @returns {THREE.Group} 器具グループ
     */
    static createInstrumentMesh(instrumentData, videoWidth = 640, videoHeight = 480) {
        const instrumentGroup = new THREE.Group();
        const pose = instrumentData.pose;
        
        if (!pose || !pose.position) {
            return instrumentGroup;
        }

        // 器具の中心位置
        const centerPos = this.videoToThreeCoordinates(
            pose.position.x,
            pose.position.y,
            pose.position.z || 0,
            videoWidth,
            videoHeight
        );

        // 器具の長さ（ピクセル→3D座標スケール変換）
        const length = (pose.length || 20) * COORDINATE_CONFIG.VIDEO_TO_3D.scale;

        // 円柱ジオメトリで器具を表現
        const cylinderGeometry = new THREE.CylinderGeometry(
            VISUALIZATION_CONFIG.SIZES.INSTRUMENT_CYLINDER.radius,
            VISUALIZATION_CONFIG.SIZES.INSTRUMENT_CYLINDER.radius,
            length,
            8
        );

        const cylinderMaterial = new THREE.MeshLambertMaterial({ 
            color: VISUALIZATION_CONFIG.COLORS.INSTRUMENT,
            transparent: true,
            opacity: 0.8
        });

        const cylinder = new THREE.Mesh(cylinderGeometry, cylinderMaterial);
        cylinder.position.copy(centerPos);

        // 回転の適用
        if (pose.rotation) {
            cylinder.rotation.x = pose.rotation.x || 0;
            cylinder.rotation.y = pose.rotation.y || 0;
            cylinder.rotation.z = pose.rotation.z || 0;
        }

        // 先端・後端のマーカー
        if (pose.tip_position && pose.base_position) {
            const tipPos = this.videoToThreeCoordinates(
                pose.tip_position.x,
                pose.tip_position.y,
                pose.tip_position.z || 0,
                videoWidth,
                videoHeight
            );

            const basePos = this.videoToThreeCoordinates(
                pose.base_position.x,
                pose.base_position.y,
                pose.base_position.z || 0,
                videoWidth,
                videoHeight
            );

            // 先端マーカー（赤い球）
            const tipGeometry = new THREE.SphereGeometry(1.5, 8, 6);
            const tipMaterial = new THREE.MeshLambertMaterial({ color: 0xff0000 });
            const tipSphere = new THREE.Mesh(tipGeometry, tipMaterial);
            tipSphere.position.copy(tipPos);
            instrumentGroup.add(tipSphere);

            // 後端マーカー（青い球）
            const baseGeometry = new THREE.SphereGeometry(1.2, 8, 6);
            const baseMaterial = new THREE.MeshLambertMaterial({ color: 0x0000ff });
            const baseSphere = new THREE.Mesh(baseGeometry, baseMaterial);
            baseSphere.position.copy(basePos);
            instrumentGroup.add(baseSphere);
        }

        instrumentGroup.add(cylinder);

        // 信頼度による透明度調整
        const opacity = Math.max(0.3, instrumentData.confidence || 0.5);
        instrumentGroup.children.forEach(child => {
            if (child.material) {
                child.material.opacity = opacity;
            }
        });

        instrumentGroup.userData = {
            type: 'instrument',
            instrumentId: instrumentData.instrument_id,
            confidence: instrumentData.confidence
        };

        return instrumentGroup;
    }

    /**
     * 軌跡線の作成
     * @param {Array} positions - 位置配列
     * @param {number} color - 線の色
     * @returns {THREE.Line} 軌跡線
     */
    static createTrailLine(positions, color = VISUALIZATION_CONFIG.COLORS.TRAIL) {
        if (positions.length < 2) {
            return null;
        }

        const geometry = new THREE.BufferGeometry().setFromPoints(positions);
        const material = new THREE.LineBasicMaterial({ 
            color: color,
            linewidth: VISUALIZATION_CONFIG.SIZES.TRAIL_LINE,
            transparent: true,
            opacity: 0.7
        });

        const line = new THREE.Line(geometry, material);
        line.userData = {
            type: 'trail'
        };

        return line;
    }

    /**
     * グリッドの作成
     * @returns {THREE.GridHelper} グリッドヘルパー
     */
    static createGrid() {
        const grid = new THREE.GridHelper(
            THREE_CONFIG.GRID.size,
            THREE_CONFIG.GRID.divisions,
            THREE_CONFIG.GRID.colorCenterLine,
            THREE_CONFIG.GRID.colorGrid
        );

        grid.rotateX(Math.PI / 2); // XY平面に配置
        grid.userData = {
            type: 'grid'
        };

        return grid;
    }

    /**
     * 座標軸の作成
     * @returns {THREE.AxesHelper} 座標軸ヘルパー
     */
    static createAxes() {
        const axes = new THREE.AxesHelper(50);
        axes.userData = {
            type: 'axes'
        };
        return axes;
    }

    /**
     * ライティングセットアップ
     * @param {THREE.Scene} scene - Three.jsシーン
     */
    static setupLighting(scene) {
        // 環境光
        const ambientLight = new THREE.AmbientLight(
            VISUALIZATION_CONFIG.LIGHTING.AMBIENT.color,
            VISUALIZATION_CONFIG.LIGHTING.AMBIENT.intensity
        );
        scene.add(ambientLight);

        // 指向性ライト
        const directionalLight = new THREE.DirectionalLight(
            VISUALIZATION_CONFIG.LIGHTING.DIRECTIONAL.color,
            VISUALIZATION_CONFIG.LIGHTING.DIRECTIONAL.intensity
        );

        const lightPos = VISUALIZATION_CONFIG.LIGHTING.DIRECTIONAL.position;
        directionalLight.position.set(lightPos.x, lightPos.y, lightPos.z);
        directionalLight.castShadow = true;

        // シャドウマップ設定
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;

        scene.add(directionalLight);

        return { ambientLight, directionalLight };
    }

    /**
     * オブジェクトのスムーズな位置更新
     * @param {THREE.Object3D} object - 更新するオブジェクト
     * @param {THREE.Vector3} targetPosition - 目標位置
     * @param {number} smoothFactor - スムーシング係数
     */
    static smoothUpdatePosition(object, targetPosition, smoothFactor = VISUALIZATION_CONFIG.ANIMATION.SMOOTH_FACTOR) {
        object.position.lerp(targetPosition, smoothFactor);
    }

    /**
     * カメラの初期設定
     * @param {THREE.PerspectiveCamera} camera - カメラオブジェクト
     * @param {number} width - 画面幅
     * @param {number} height - 画面高さ
     */
    static setupCamera(camera, width, height) {
        camera.aspect = width / height;
        camera.updateProjectionMatrix();

        const cameraPos = VISUALIZATION_CONFIG.CAMERA.POSITION;
        camera.position.set(cameraPos.x, cameraPos.y, cameraPos.z);
    }

    /**
     * レンダラーの初期設定
     * @param {THREE.WebGLRenderer} renderer - レンダラーオブジェクト
     * @param {number} width - 画面幅
     * @param {number} height - 画面高さ
     */
    static setupRenderer(renderer, width, height) {
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);

        const config = THREE_CONFIG.RENDERER;
        renderer.setClearColor(config.clearColor, config.clearAlpha);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }

    /**
     * オブジェクトの一括削除
     * @param {THREE.Scene} scene - シーン
     * @param {string} type - 削除するオブジェクトタイプ
     */
    static removeObjectsByType(scene, type) {
        const objectsToRemove = [];
        
        scene.traverse((child) => {
            if (child.userData && child.userData.type === type) {
                objectsToRemove.push(child);
            }
        });

        objectsToRemove.forEach((obj) => {
            scene.remove(obj);
            
            // メモリ解放
            if (obj.geometry) {
                obj.geometry.dispose();
            }
            if (obj.material) {
                if (Array.isArray(obj.material)) {
                    obj.material.forEach(material => material.dispose());
                } else {
                    obj.material.dispose();
                }
            }
        });
    }

    /**
     * パフォーマンス監視用の統計情報取得
     * @param {THREE.WebGLRenderer} renderer - レンダラー
     * @returns {Object} 統計情報
     */
    static getPerformanceStats(renderer) {
        return {
            geometries: renderer.info.memory.geometries,
            textures: renderer.info.memory.textures,
            programs: renderer.info.programs?.length || 0,
            calls: renderer.info.render.calls,
            triangles: renderer.info.render.triangles,
            points: renderer.info.render.points
        };
    }

    /**
     * 色の補間
     * @param {number} color1 - 開始色
     * @param {number} color2 - 終了色
     * @param {number} factor - 補間係数（0-1）
     * @returns {THREE.Color} 補間された色
     */
    static lerpColor(color1, color2, factor) {
        const c1 = new THREE.Color(color1);
        const c2 = new THREE.Color(color2);
        return c1.lerp(c2, factor);
    }
}

// グローバルに公開
window.ThreeUtils = ThreeUtils;