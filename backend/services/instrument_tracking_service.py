"""
Instrument Tracking Service using SAM (Segment Anything Model)
SAMを使用した手術器具トラッキング・姿勢推定サービス
"""

import cv2
import numpy as np
import torch
from typing import List, Optional, Tuple, Dict, Any
import logging
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
import math

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.data_models import (
    InstrumentData, 
    InstrumentPose, 
    Point3D, 
    ROISelection
)

logger = logging.getLogger(__name__)


class SAMInstrumentTracker:
    """SAMを使用した器具トラッキングクラス"""
    
    def __init__(
        self,
        model_type: str = "vit_h",
        checkpoint_path: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            model_type: SAMモデルタイプ ("vit_h", "vit_l", "vit_b")
            checkpoint_path: チェックポイントファイルパス
            device: 計算デバイス ("cuda", "cpu", None=自動選択)
        """
        self.model_type = model_type
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        # SAM初期化（実際の実装では適切なモデル読み込み）
        self._initialize_sam(checkpoint_path)
        
        # トラッキング用の変数
        self.current_mask = None
        self.previous_masks = []
        self.tracking_history = []
        
        logger.info(f"🔧 SAM Instrument Tracker initialized (device={self.device})")
    
    def _initialize_sam(self, checkpoint_path: Optional[str]):
        """SAMモデルの初期化"""
        try:
            # 注意: 実際の実装ではSAMのインストールと適切な初期化が必要
            # ここではダミーの実装として、OpenCVベースのセグメンテーションを使用
            
            # SAMが利用可能な場合の実装例:
            # from segment_anything import sam_model_registry, SamPredictor
            # sam = sam_model_registry[self.model_type](checkpoint=checkpoint_path)
            # sam.to(device=self.device)
            # self.predictor = SamPredictor(sam)
            
            # ダミー実装（OpenCVベース）
            self.predictor = None
            self.use_opencv_fallback = True
            
            logger.warning("⚠️ Using OpenCV fallback for instrument segmentation (SAM not available)")
            
        except Exception as e:
            logger.error(f"❌ SAM initialization failed: {str(e)}")
            self.predictor = None
            self.use_opencv_fallback = True
    
    def set_initial_selection(
        self, 
        frame: np.ndarray, 
        roi_selection: ROISelection
    ) -> Optional[np.ndarray]:
        """
        初期ROI選択による器具セグメンテーション
        
        Args:
            frame: 入力フレーム
            roi_selection: ROI選択情報
            
        Returns:
            np.ndarray: セグメンテーションマスク（成功時）
        """
        try:
            click_x = int(roi_selection.click_position.x)
            click_y = int(roi_selection.click_position.y)
            
            if self.predictor and not self.use_opencv_fallback:
                # SAM使用の場合
                mask = self._sam_segmentation(frame, click_x, click_y)
            else:
                # OpenCVフォールバック
                mask = self._opencv_segmentation(frame, click_x, click_y)
            
            if mask is not None:
                self.current_mask = mask
                self.previous_masks.append(mask.copy())
                logger.info(f"✅ Initial segmentation completed at ({click_x}, {click_y})")
            
            return mask
            
        except Exception as e:
            logger.error(f"❌ Initial selection error: {str(e)}")
            return None
    
    def _sam_segmentation(
        self, 
        frame: np.ndarray, 
        click_x: int, 
        click_y: int
    ) -> Optional[np.ndarray]:
        """
        SAMによるセグメンテーション
        
        Args:
            frame: 入力フレーム
            click_x, click_y: クリック座標
            
        Returns:
            np.ndarray: セグメンテーションマスク
        """
        try:
            # SAMの実際の実装
            # self.predictor.set_image(frame)
            # input_point = np.array([[click_x, click_y]])
            # input_label = np.array([1])  # foreground
            # 
            # masks, scores, logits = self.predictor.predict(
            #     point_coords=input_point,
            #     point_labels=input_label,
            #     multimask_output=False,
            # )
            # 
            # return masks[0].astype(np.uint8) * 255
            
            # ダミー実装
            return self._opencv_segmentation(frame, click_x, click_y)
            
        except Exception as e:
            logger.error(f"❌ SAM segmentation error: {str(e)}")
            return None
    
    def _opencv_segmentation(
        self, 
        frame: np.ndarray, 
        click_x: int, 
        click_y: int,
        region_size: int = 50
    ) -> Optional[np.ndarray]:
        """
        OpenCVによるセグメンテーション（フォールバック）
        
        Args:
            frame: 入力フレーム
            click_x, click_y: クリック座標
            region_size: 初期領域サイズ
            
        Returns:
            np.ndarray: セグメンテーションマスク
        """
        try:
            h, w = frame.shape[:2]
            mask = np.zeros((h, w), dtype=np.uint8)
            
            # クリック位置周辺の色情報を取得
            x1 = max(0, click_x - region_size // 2)
            y1 = max(0, click_y - region_size // 2)
            x2 = min(w, click_x + region_size // 2)
            y2 = min(h, click_y + region_size // 2)
            
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                return None
            
            # 色ベースのセグメンテーション
            # 平均色と標準偏差を計算
            mean_color = np.mean(roi.reshape(-1, 3), axis=0)
            std_color = np.std(roi.reshape(-1, 3), axis=0)
            
            # 色の閾値設定（2σ範囲）
            lower_bound = np.maximum(0, mean_color - 2 * std_color).astype(np.uint8)
            upper_bound = np.minimum(255, mean_color + 2 * std_color).astype(np.uint8)
            
            # 色ベースマスク作成
            color_mask = cv2.inRange(frame, lower_bound, upper_bound)
            
            # モルフォロジー処理でノイズ除去
            kernel = np.ones((5, 5), np.uint8)
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
            color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
            
            # 連結成分分析でクリック位置に最も近い領域を選択
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(color_mask)
            
            if num_labels > 1:
                # クリック位置に最も近い連結成分を選択
                min_distance = float('inf')
                target_label = 0
                
                for i in range(1, num_labels):  # 0はバックグラウンド
                    centroid = centroids[i]
                    distance = np.sqrt(
                        (centroid[0] - click_x)**2 + (centroid[1] - click_y)**2
                    )
                    
                    if distance < min_distance:
                        min_distance = distance
                        target_label = i
                
                # 選択された領域のマスクを作成
                mask = (labels == target_label).astype(np.uint8) * 255
            else:
                mask = color_mask
            
            return mask
            
        except Exception as e:
            logger.error(f"❌ OpenCV segmentation error: {str(e)}")
            return None
    
    def track_instrument(self, frame: np.ndarray) -> Optional[InstrumentData]:
        """
        フレーム間での器具トラッキング
        
        Args:
            frame: 入力フレーム
            
        Returns:
            InstrumentData: トラッキング結果
        """
        try:
            if self.current_mask is None:
                logger.warning("⚠️ No initial mask available for tracking")
                return None
            
            # テンプレートマッチングベースのトラッキング
            updated_mask = self._template_matching_tracking(frame)
            
            if updated_mask is not None:
                self.current_mask = updated_mask
                self.previous_masks.append(updated_mask.copy())
                
                # マスクから姿勢推定
                pose = self._estimate_pose_from_mask(updated_mask, frame.shape[:2])
                
                if pose:
                    # セグメンテーション面積計算
                    segmentation_area = np.sum(updated_mask > 0)
                    confidence = min(segmentation_area / 10000.0, 1.0)  # 正規化
                    
                    instrument_data = InstrumentData(
                        pose=pose,
                        confidence=confidence,
                        segmentation_area=float(segmentation_area)
                    )
                    
                    self.tracking_history.append(instrument_data)
                    return instrument_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Instrument tracking error: {str(e)}")
            return None
    
    def _template_matching_tracking(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        テンプレートマッチングベースのトラッキング
        
        Args:
            frame: 入力フレーム
            
        Returns:
            np.ndarray: 更新されたマスク
        """
        try:
            if self.current_mask is None:
                return None
            
            # 前フレームのマスクをテンプレートとして使用
            template_mask = self.current_mask
            
            # マスク領域の外接矩形を取得
            contours, _ = cv2.findContours(
                template_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(contours) == 0:
                return None
            
            # 最大面積の輪郭を選択
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # テンプレート領域が有効かチェック
            if w < 10 or h < 10:
                return None
            
            # テンプレート画像作成
            template = frame[y:y+h, x:x+w]
            template_mask_roi = template_mask[y:y+h, x:x+w]
            
            # テンプレートマッチング実行
            result = cv2.matchTemplate(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                cv2.cvtColor(template, cv2.COLOR_BGR2GRAY),
                cv2.TM_CCOEFF_NORMED,
                mask=template_mask_roi
            )
            
            # 最適な位置を検出
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.3:  # 信頼度閾値
                # 新しい位置にマスクを移動
                new_x, new_y = max_loc
                new_mask = np.zeros_like(template_mask)
                
                # 移動量計算
                dx = new_x - x
                dy = new_y - y
                
                # マスクを新しい位置に配置
                mask_h, mask_w = template_mask_roi.shape
                new_y_end = min(new_y + mask_h, new_mask.shape[0])
                new_x_end = min(new_x + mask_w, new_mask.shape[1])
                
                roi_h = new_y_end - new_y
                roi_w = new_x_end - new_x
                
                new_mask[new_y:new_y_end, new_x:new_x_end] = template_mask_roi[:roi_h, :roi_w]
                
                return new_mask
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Template matching tracking error: {str(e)}")
            return None
    
    def _estimate_pose_from_mask(
        self, 
        mask: np.ndarray, 
        frame_shape: Tuple[int, int]
    ) -> Optional[InstrumentPose]:
        """
        マスクから器具の姿勢推定
        
        Args:
            mask: セグメンテーションマスク
            frame_shape: フレームサイズ (height, width)
            
        Returns:
            InstrumentPose: 推定された姿勢
        """
        try:
            # マスクから輪郭抽出
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if len(contours) == 0:
                return None
            
            # 最大面積の輪郭を選択
            largest_contour = max(contours, key=cv2.contourArea)
            
            if cv2.contourArea(largest_contour) < 100:  # 最小面積閾値
                return None
            
            # 輪郭の重心計算
            M = cv2.moments(largest_contour)
            if M["m00"] == 0:
                return None
            
            center_x = M["m10"] / M["m00"]
            center_y = M["m01"] / M["m00"]
            
            # PCAによる主軸方向推定
            points = largest_contour.reshape(-1, 2).astype(np.float32)
            pca = PCA(n_components=2)
            pca.fit(points)
            
            # 主軸ベクトル
            main_axis = pca.components_[0]
            
            # 器具の回転角度計算
            rotation_angle = math.atan2(main_axis[1], main_axis[0])
            
            # 器具の先端・後端推定
            # 主軸方向に沿って最も遠い点を探す
            projected = np.dot(points - np.array([center_x, center_y]), main_axis)
            min_proj_idx = np.argmin(projected)
            max_proj_idx = np.argmax(projected)
            
            tip_point = points[max_proj_idx]
            base_point = points[min_proj_idx]
            
            # 器具の長さ計算
            instrument_length = np.linalg.norm(tip_point - base_point)
            
            # 3D座標推定（簡易的な奥行き推定）
            # 実際の実装ではカメラキャリブレーション情報を使用
            z_estimate = -instrument_length * 0.1  # 簡易的な奥行き推定
            
            pose = InstrumentPose(
                position=Point3D(
                    x=float(center_x),
                    y=float(center_y),
                    z=float(z_estimate)
                ),
                rotation=Point3D(
                    x=0.0,  # X軸回転
                    y=0.0,  # Y軸回転
                    z=float(rotation_angle)  # Z軸回転
                ),
                tip_position=Point3D(
                    x=float(tip_point[0]),
                    y=float(tip_point[1]),
                    z=float(z_estimate)
                ),
                base_position=Point3D(
                    x=float(base_point[0]),
                    y=float(base_point[1]),
                    z=float(z_estimate)
                ),
                length=float(instrument_length)
            )
            
            return pose
            
        except Exception as e:
            logger.error(f"❌ Pose estimation error: {str(e)}")
            return None
    
    def draw_tracking_result(
        self, 
        frame: np.ndarray, 
        instrument_data: InstrumentData
    ) -> np.ndarray:
        """
        トラッキング結果をフレームに描画
        
        Args:
            frame: 入力フレーム
            instrument_data: 器具データ
            
        Returns:
            np.ndarray: 描画済みフレーム
        """
        annotated_frame = frame.copy()
        
        try:
            pose = instrument_data.pose
            
            # 中心点を描画
            center = (int(pose.position.x), int(pose.position.y))
            cv2.circle(annotated_frame, center, 8, (0, 255, 0), -1)
            
            # 先端・後端を描画
            if pose.tip_position and pose.base_position:
                tip = (int(pose.tip_position.x), int(pose.tip_position.y))
                base = (int(pose.base_position.x), int(pose.base_position.y))
                
                cv2.circle(annotated_frame, tip, 6, (0, 0, 255), -1)  # 赤: 先端
                cv2.circle(annotated_frame, base, 6, (255, 0, 0), -1)  # 青: 後端
                
                # 器具のラインを描画
                cv2.line(annotated_frame, tip, base, (255, 255, 0), 3)
            
            # 信頼度と長さを表示
            text = f"Conf: {instrument_data.confidence:.2f}, Len: {pose.length:.1f}px"
            cv2.putText(
                annotated_frame,
                text,
                (center[0] + 10, center[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )
            
            # 回転角度を表示
            rotation_deg = math.degrees(pose.rotation.z)
            angle_text = f"Angle: {rotation_deg:.1f}°"
            cv2.putText(
                annotated_frame,
                angle_text,
                (center[0] + 10, center[1] + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1
            )
            
            return annotated_frame
            
        except Exception as e:
            logger.error(f"❌ Error drawing tracking result: {str(e)}")
            return frame
    
    def get_tracking_summary(self) -> Dict[str, Any]:
        """
        トラッキング結果のサマリー取得
        
        Returns:
            Dict[str, Any]: トラッキングサマリー
        """
        try:
            if not self.tracking_history:
                return {"status": "no_tracking_data"}
            
            # 統計情報計算
            confidences = [data.confidence for data in self.tracking_history]
            positions = [data.pose.position for data in self.tracking_history]
            
            avg_confidence = np.mean(confidences)
            min_confidence = np.min(confidences)
            
            # 器具の移動距離計算
            total_distance = 0
            if len(positions) > 1:
                for i in range(1, len(positions)):
                    prev_pos = positions[i-1]
                    curr_pos = positions[i]
                    distance = np.sqrt(
                        (curr_pos.x - prev_pos.x)**2 + 
                        (curr_pos.y - prev_pos.y)**2
                    )
                    total_distance += distance
            
            summary = {
                "total_frames": len(self.tracking_history),
                "avg_confidence": float(avg_confidence),
                "min_confidence": float(min_confidence),
                "total_movement_distance": float(total_distance),
                "tracking_success_rate": len([c for c in confidences if c > 0.5]) / len(confidences)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating tracking summary: {str(e)}")
            return {"status": "error", "message": str(e)}


# ユーティリティ関数
def calculate_instrument_velocity(
    current_pose: InstrumentPose, 
    previous_pose: InstrumentPose, 
    time_delta: float
) -> Tuple[float, float]:
    """
    器具の速度計算
    
    Args:
        current_pose: 現在の姿勢
        previous_pose: 前フレームの姿勢
        time_delta: 時間差（秒）
        
    Returns:
        Tuple[float, float]: (線速度, 角速度)
    """
    try:
        # 線速度計算
        dx = current_pose.position.x - previous_pose.position.x
        dy = current_pose.position.y - previous_pose.position.y
        dz = current_pose.position.z - previous_pose.position.z
        
        linear_velocity = math.sqrt(dx*dx + dy*dy + dz*dz) / time_delta
        
        # 角速度計算
        angle_diff = current_pose.rotation.z - previous_pose.rotation.z
        # 角度差を-π〜πの範囲に正規化
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        angular_velocity = abs(angle_diff) / time_delta
        
        return linear_velocity, angular_velocity
        
    except Exception as e:
        logger.error(f"❌ Error calculating instrument velocity: {str(e)}")
        return 0.0, 0.0