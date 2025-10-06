"""
Hand Tracking Service using MediaPipe Hands
MediaPipe Handsを使用した手指トラッキングサービス
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import List, Optional, Tuple, Dict
import logging

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.data_models import (
    HandData, 
    HandLandmark, 
    Point3D, 
    HAND_LANDMARK_NAMES, 
    HAND_CONNECTIONS
)

logger = logging.getLogger(__name__)


class HandTrackingService:
    """MediaPipe Handsを使用した手指トラッキングサービス"""
    
    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        model_complexity: int = 1
    ):
        """
        初期化
        
        Args:
            max_num_hands: 最大検出手数
            min_detection_confidence: 検出信頼度閾値
            min_tracking_confidence: トラッキング信頼度閾値
            model_complexity: モデル複雑度 (0=Lite, 1=Full)
        """
        self.max_num_hands = max_num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        # MediaPipe Hands初期化
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=model_complexity
        )
        
        logger.info(f"🤲 Hand tracking service initialized (max_hands={max_num_hands})")
    
    def process_frame(self, frame: np.ndarray) -> List[HandData]:
        """
        単一フレームの手指トラッキング処理
        
        Args:
            frame: 入力フレーム（BGR形式）
            
        Returns:
            List[HandData]: 検出された手のデータリスト
        """
        try:
            # BGR→RGB変換
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            
            # MediaPipe処理
            results = self.hands.process(rgb_frame)
            
            hands_data = []
            
            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(
                    results.multi_hand_landmarks, 
                    results.multi_handedness
                ):
                    # 手の種類判定（Left/Right）
                    hand_type = handedness.classification[0].label
                    hand_confidence = handedness.classification[0].score
                    
                    # ランドマーク抽出
                    landmarks = self._extract_landmarks(
                        hand_landmarks, 
                        frame.shape[:2]
                    )
                    
                    # HandDataオブジェクト作成
                    hand_data = HandData(
                        hand_type=hand_type,
                        landmarks=landmarks,
                        confidence=hand_confidence
                    )
                    
                    hands_data.append(hand_data)
            
            return hands_data
            
        except Exception as e:
            logger.error(f"❌ Hand tracking error: {str(e)}")
            return []
    
    def _extract_landmarks(
        self, 
        hand_landmarks, 
        frame_shape: Tuple[int, int]
    ) -> List[HandLandmark]:
        """
        MediaPipeランドマークからHandLandmarkオブジェクトを作成
        
        Args:
            hand_landmarks: MediaPipeのランドマーク結果
            frame_shape: フレームサイズ (height, width)
            
        Returns:
            List[HandLandmark]: ランドマークリスト
        """
        landmarks = []
        height, width = frame_shape
        
        for idx, landmark in enumerate(hand_landmarks.landmark):
            # 正規化座標を実座標に変換
            x = landmark.x * width
            y = landmark.y * height
            z = landmark.z * width  # MediaPipeのzは相対的な奥行き
            
            # HandLandmarkオブジェクト作成
            hand_landmark = HandLandmark(
                id=idx,
                name=HAND_LANDMARK_NAMES[idx],
                position=Point3D(
                    x=x, 
                    y=y, 
                    z=z,
                    confidence=getattr(landmark, 'visibility', None)
                ),
                visibility=getattr(landmark, 'visibility', None)
            )
            
            landmarks.append(hand_landmark)
        
        return landmarks
    
    def calculate_hand_metrics(self, hand_data: HandData) -> Dict[str, float]:
        """
        手の特徴量計算
        
        Args:
            hand_data: 手データ
            
        Returns:
            Dict[str, float]: 計算された特徴量
        """
        try:
            landmarks = {lm.name: lm.position for lm in hand_data.landmarks}
            metrics = {}
            
            # 手首を基準とした各指先の相対位置
            wrist = landmarks["WRIST"]
            
            # 各指先の位置
            fingertips = ["THUMB_TIP", "INDEX_FINGER_TIP", "MIDDLE_FINGER_TIP", 
                         "RING_FINGER_TIP", "PINKY_TIP"]
            
            for tip in fingertips:
                if tip in landmarks:
                    tip_pos = landmarks[tip]
                    distance = np.sqrt(
                        (tip_pos.x - wrist.x)**2 + 
                        (tip_pos.y - wrist.y)**2 + 
                        (tip_pos.z - wrist.z)**2
                    )
                    metrics[f"{tip.lower()}_distance"] = distance
            
            # 手の開き度合い（親指と小指の距離）
            if "THUMB_TIP" in landmarks and "PINKY_TIP" in landmarks:
                thumb = landmarks["THUMB_TIP"]
                pinky = landmarks["PINKY_TIP"]
                hand_span = np.sqrt(
                    (thumb.x - pinky.x)**2 + 
                    (thumb.y - pinky.y)**2 + 
                    (thumb.z - pinky.z)**2
                )
                metrics["hand_span"] = hand_span
            
            # 手のひらの向き（法線ベクトル）
            if all(name in landmarks for name in ["WRIST", "INDEX_FINGER_MCP", "PINKY_MCP"]):
                wrist = landmarks["WRIST"]
                index_mcp = landmarks["INDEX_FINGER_MCP"]
                pinky_mcp = landmarks["PINKY_MCP"]
                
                # 手のひら平面の法線ベクトル計算
                v1 = np.array([index_mcp.x - wrist.x, index_mcp.y - wrist.y, index_mcp.z - wrist.z])
                v2 = np.array([pinky_mcp.x - wrist.x, pinky_mcp.y - wrist.y, pinky_mcp.z - wrist.z])
                normal = np.cross(v1, v2)
                
                if np.linalg.norm(normal) > 0:
                    normal = normal / np.linalg.norm(normal)
                    metrics["palm_normal_x"] = normal[0]
                    metrics["palm_normal_y"] = normal[1]
                    metrics["palm_normal_z"] = normal[2]
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error calculating hand metrics: {str(e)}")
            return {}
    
    def draw_landmarks_on_frame(
        self, 
        frame: np.ndarray, 
        hands_data: List[HandData],
        draw_connections: bool = True,
        draw_labels: bool = False
    ) -> np.ndarray:
        """
        フレームにランドマークを描画
        
        Args:
            frame: 入力フレーム
            hands_data: 手データリスト
            draw_connections: 接続線を描画するかどうか
            draw_labels: ラベルを描画するかどうか
            
        Returns:
            np.ndarray: ランドマーク描画済みフレーム
        """
        annotated_frame = frame.copy()
        
        try:
            for hand_data in hands_data:
                # 色設定（左手: 青、右手: 赤）
                color = (255, 0, 0) if hand_data.hand_type == "Right" else (0, 0, 255)
                
                # ランドマーク描画
                for landmark in hand_data.landmarks:
                    x = int(landmark.position.x)
                    y = int(landmark.position.y)
                    
                    # 点を描画
                    cv2.circle(annotated_frame, (x, y), 5, color, -1)
                    
                    # ラベル描画
                    if draw_labels:
                        cv2.putText(
                            annotated_frame, 
                            str(landmark.id), 
                            (x + 5, y - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            0.3, 
                            color, 
                            1
                        )
                
                # 接続線描画
                if draw_connections:
                    for connection in HAND_CONNECTIONS:
                        start_idx, end_idx = connection
                        
                        if start_idx < len(hand_data.landmarks) and end_idx < len(hand_data.landmarks):
                            start_pos = hand_data.landmarks[start_idx].position
                            end_pos = hand_data.landmarks[end_idx].position
                            
                            start_point = (int(start_pos.x), int(start_pos.y))
                            end_point = (int(end_pos.x), int(end_pos.y))
                            
                            cv2.line(annotated_frame, start_point, end_point, color, 2)
                
                # 手の種類とconfidenceを表示
                if hand_data.landmarks:
                    wrist = hand_data.landmarks[0].position  # WRIST
                    text = f"{hand_data.hand_type} ({hand_data.confidence:.2f})"
                    cv2.putText(
                        annotated_frame, 
                        text, 
                        (int(wrist.x), int(wrist.y - 20)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        color, 
                        2
                    )
            
            return annotated_frame
            
        except Exception as e:
            logger.error(f"❌ Error drawing landmarks: {str(e)}")
            return frame
    
    def export_landmarks_to_dict(self, hands_data: List[HandData]) -> Dict:
        """
        手のランドマークデータを辞書形式にエクスポート
        
        Args:
            hands_data: 手データリスト
            
        Returns:
            Dict: エクスポート用辞書
        """
        export_data = {
            "hands": [],
            "num_hands": len(hands_data)
        }
        
        for hand_data in hands_data:
            hand_dict = {
                "hand_type": hand_data.hand_type,
                "confidence": hand_data.confidence,
                "landmarks": []
            }
            
            for landmark in hand_data.landmarks:
                landmark_dict = {
                    "id": landmark.id,
                    "name": landmark.name,
                    "x": landmark.position.x,
                    "y": landmark.position.y,
                    "z": landmark.position.z,
                    "confidence": landmark.position.confidence,
                    "visibility": landmark.visibility
                }
                hand_dict["landmarks"].append(landmark_dict)
            
            # 手の特徴量も追加
            metrics = self.calculate_hand_metrics(hand_data)
            hand_dict["metrics"] = metrics
            
            export_data["hands"].append(hand_dict)
        
        return export_data
    
    def __del__(self):
        """デストラクタ"""
        if hasattr(self, 'hands') and self.hands:
            self.hands.close()


# ユーティリティ関数
def calculate_gesture_score(hand_data: HandData) -> Dict[str, float]:
    """
    基本的なジェスチャー判定スコア計算
    
    Args:
        hand_data: 手データ
        
    Returns:
        Dict[str, float]: ジェスチャースコア
    """
    try:
        landmarks = {lm.name: lm.position for lm in hand_data.landmarks}
        scores = {}
        
        # 握り度合い（指先と手のひらの距離）
        if "WRIST" in landmarks:
            wrist = landmarks["WRIST"]
            fingertips = ["THUMB_TIP", "INDEX_FINGER_TIP", "MIDDLE_FINGER_TIP", 
                         "RING_FINGER_TIP", "PINKY_TIP"]
            
            total_distance = 0
            valid_tips = 0
            
            for tip_name in fingertips:
                if tip_name in landmarks:
                    tip = landmarks[tip_name]
                    distance = np.sqrt(
                        (tip.x - wrist.x)**2 + 
                        (tip.y - wrist.y)**2
                    )
                    total_distance += distance
                    valid_tips += 1
            
            if valid_tips > 0:
                avg_distance = total_distance / valid_tips
                # 正規化（大きいほど開いている）
                scores["openness"] = min(avg_distance / 200.0, 1.0)
                scores["fist_likelihood"] = 1.0 - scores["openness"]
        
        return scores
        
    except Exception as e:
        logger.error(f"❌ Error calculating gesture scores: {str(e)}")
        return {}