"""
Video Processing Service
動画処理・フレーム抽出サービス
"""

import cv2
import os
import numpy as np
from typing import Generator, Tuple, Optional
import logging

import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.data_models import VideoMetadata

logger = logging.getLogger(__name__)


class VideoProcessor:
    """動画処理クラス"""
    
    def __init__(self):
        self.current_video_path = None
        self.cap = None
    
    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """
        動画のメタデータを取得
        
        Args:
            video_path: 動画ファイルパス
            
        Returns:
            VideoMetadata: 動画メタデータ
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"動画ファイルを開けません: {video_path}")
            
            # メタデータ取得
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            file_size = os.path.getsize(video_path)
            filename = os.path.basename(video_path)
            
            cap.release()
            
            metadata = VideoMetadata(
                filename=filename,
                duration=duration,
                fps=fps,
                width=width,
                height=height,
                total_frames=frame_count,
                file_size=file_size
            )
            
            logger.info(f"📹 Video metadata extracted: {filename} ({width}x{height}, {fps}fps, {duration:.2f}s)")
            
            return metadata
            
        except Exception as e:
            logger.error(f"❌ Error extracting video metadata: {str(e)}")
            raise
    
    def open_video(self, video_path: str) -> bool:
        """
        動画ファイルを開く
        
        Args:
            video_path: 動画ファイルパス
            
        Returns:
            bool: 成功/失敗
        """
        try:
            self.cap = cv2.VideoCapture(video_path)
            self.current_video_path = video_path
            
            if not self.cap.isOpened():
                logger.error(f"❌ Failed to open video: {video_path}")
                return False
            
            logger.info(f"✅ Video opened: {video_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error opening video: {str(e)}")
            return False
    
    def close_video(self):
        """動画ファイルを閉じる"""
        if self.cap:
            self.cap.release()
            self.cap = None
            self.current_video_path = None
            logger.info("📹 Video closed")
    
    def get_frame_at_timestamp(self, timestamp: float) -> Optional[np.ndarray]:
        """
        指定タイムスタンプのフレームを取得
        
        Args:
            timestamp: タイムスタンプ（秒）
            
        Returns:
            np.ndarray: フレーム画像、失敗時はNone
        """
        if not self.cap or not self.cap.isOpened():
            logger.error("❌ Video not opened")
            return None
        
        try:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)
            
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning(f"⚠️ Could not read frame at timestamp {timestamp}")
                return None
            
            return frame
            
        except Exception as e:
            logger.error(f"❌ Error getting frame at timestamp {timestamp}: {str(e)}")
            return None
    
    def get_frame_at_number(self, frame_number: int) -> Optional[Tuple[np.ndarray, float]]:
        """
        指定フレーム番号の画像とタイムスタンプを取得
        
        Args:
            frame_number: フレーム番号
            
        Returns:
            Tuple[np.ndarray, float]: (フレーム画像, タイムスタンプ)、失敗時はNone
        """
        if not self.cap or not self.cap.isOpened():
            logger.error("❌ Video not opened")
            return None
        
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.cap.read()
            
            if not ret:
                logger.warning(f"⚠️ Could not read frame number {frame_number}")
                return None
            
            # タイムスタンプ計算
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            timestamp = frame_number / fps if fps > 0 else 0
            
            return frame, timestamp
            
        except Exception as e:
            logger.error(f"❌ Error getting frame number {frame_number}: {str(e)}")
            return None
    
    def extract_frames_generator(
        self, 
        start_frame: int = 0, 
        end_frame: Optional[int] = None,
        step: int = 1
    ) -> Generator[Tuple[int, float, np.ndarray], None, None]:
        """
        フレームを順次取得するジェネレーター
        
        Args:
            start_frame: 開始フレーム番号
            end_frame: 終了フレーム番号（Noneの場合は最後まで）
            step: フレーム間隔
            
        Yields:
            Tuple[int, float, np.ndarray]: (フレーム番号, タイムスタンプ, フレーム画像)
        """
        if not self.cap or not self.cap.isOpened():
            logger.error("❌ Video not opened")
            return
        
        try:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if end_frame is None:
                end_frame = total_frames
            
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            current_frame = start_frame
            
            while current_frame < end_frame:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning(f"⚠️ Could not read frame {current_frame}")
                    break
                
                timestamp = current_frame / fps if fps > 0 else 0
                yield current_frame, timestamp, frame
                
                # 次のフレームにスキップ
                if step > 1:
                    for _ in range(step - 1):
                        ret, _ = self.cap.read()
                        if not ret:
                            return
                    current_frame += step
                else:
                    current_frame += 1
                    
        except Exception as e:
            logger.error(f"❌ Error in frame extraction: {str(e)}")
    
    def extract_frame_batch(
        self, 
        frame_numbers: list[int]
    ) -> dict[int, Tuple[np.ndarray, float]]:
        """
        指定した複数フレームを一括取得
        
        Args:
            frame_numbers: 取得したいフレーム番号のリスト
            
        Returns:
            dict: {フレーム番号: (フレーム画像, タイムスタンプ)}
        """
        if not self.cap or not self.cap.isOpened():
            logger.error("❌ Video not opened")
            return {}
        
        results = {}
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        for frame_num in sorted(frame_numbers):
            try:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = self.cap.read()
                
                if ret:
                    timestamp = frame_num / fps if fps > 0 else 0
                    results[frame_num] = (frame, timestamp)
                else:
                    logger.warning(f"⚠️ Could not read frame {frame_num}")
                    
            except Exception as e:
                logger.error(f"❌ Error reading frame {frame_num}: {str(e)}")
        
        logger.info(f"📊 Extracted {len(results)}/{len(frame_numbers)} frames")
        return results
    
    def preprocess_frame(
        self, 
        frame: np.ndarray, 
        target_size: Optional[Tuple[int, int]] = None,
        normalize: bool = True
    ) -> np.ndarray:
        """
        フレーム前処理
        
        Args:
            frame: 入力フレーム
            target_size: リサイズターゲットサイズ (width, height)
            normalize: 正規化するかどうか
            
        Returns:
            np.ndarray: 前処理済みフレーム
        """
        processed_frame = frame.copy()
        
        try:
            # リサイズ
            if target_size:
                processed_frame = cv2.resize(processed_frame, target_size)
            
            # 正規化
            if normalize:
                processed_frame = processed_frame.astype(np.float32) / 255.0
            
            return processed_frame
            
        except Exception as e:
            logger.error(f"❌ Error preprocessing frame: {str(e)}")
            return frame
    
    def save_frame(
        self, 
        frame: np.ndarray, 
        output_path: str, 
        quality: int = 95
    ) -> bool:
        """
        フレームを画像ファイルとして保存
        
        Args:
            frame: 保存するフレーム
            output_path: 出力パス
            quality: JPEG品質（1-100）
            
        Returns:
            bool: 成功/失敗
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # JPEG品質設定
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            
            success = cv2.imwrite(output_path, frame, encode_param)
            
            if success:
                logger.info(f"💾 Frame saved: {output_path}")
            else:
                logger.error(f"❌ Failed to save frame: {output_path}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error saving frame: {str(e)}")
            return False
    
    def __del__(self):
        """デストラクタ"""
        self.close_video()


# ユーティリティ関数
def create_video_thumbnail(video_path: str, output_path: str, timestamp: float = 1.0) -> bool:
    """
    動画のサムネイルを作成
    
    Args:
        video_path: 動画ファイルパス
        output_path: サムネイル出力パス
        timestamp: サムネイル取得位置（秒）
        
    Returns:
        bool: 成功/失敗
    """
    processor = VideoProcessor()
    
    try:
        if not processor.open_video(video_path):
            return False
        
        frame = processor.get_frame_at_timestamp(timestamp)
        if frame is None:
            return False
        
        return processor.save_frame(frame, output_path)
        
    except Exception as e:
        logger.error(f"❌ Error creating thumbnail: {str(e)}")
        return False
    
    finally:
        processor.close_video()