"""
Analysis Service - 統合解析サービス
手と器具のトラッキングを統合し、完全な解析を実行
"""

import asyncio
import os
import logging
from typing import List, Dict, Any, Callable, Optional
import time

import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.data_models import (
    AnalysisSession, 
    AnalysisResult, 
    FrameAnalysis,
    ProcessingStatus
)
from services.video_service import VideoProcessor
from services.hand_tracking_service import HandTrackingService
from services.instrument_tracking_service import SAMInstrumentTracker

logger = logging.getLogger(__name__)


class AnalysisService:
    """統合解析サービス"""
    
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.hand_tracker = HandTrackingService()
        self.instrument_tracker = SAMInstrumentTracker()
        
        logger.info("🧠 Analysis service initialized")
    
    async def process_full_analysis(
        self,
        session_id: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> AnalysisResult:
        """
        完全な動画解析処理
        
        Args:
            session_id: 解析セッションID
            progress_callback: 進捗コールバック関数
            
        Returns:
            AnalysisResult: 解析結果
        """
        try:
            logger.info(f"🔄 Starting full analysis for session: {session_id}")
            
            # セッション情報読み込み（実際の実装ではDBから取得）
            from app.main import analysis_sessions
            if session_id not in analysis_sessions:
                raise ValueError(f"Session not found: {session_id}")
            
            session = analysis_sessions[session_id]
            video_path = f"static/uploads/{session.video_metadata.filename}"
            
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # 動画を開く
            if not self.video_processor.open_video(video_path):
                raise RuntimeError("Failed to open video file")
            
            # ROI選択情報を確認
            if not session.roi_selections:
                logger.warning("⚠️ No ROI selections found, proceeding without instrument tracking")
            
            # フレーム解析実行
            frame_analyses = await self._process_all_frames(
                session, progress_callback
            )
            
            # 解析サマリー生成
            summary = self._generate_analysis_summary(frame_analyses)
            
            # 結果作成
            result = AnalysisResult(
                session=session,
                frames=frame_analyses,
                summary=summary
            )
            
            logger.info(f"✅ Analysis completed for session: {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis error for session {session_id}: {str(e)}")
            raise
        
        finally:
            self.video_processor.close_video()
    
    async def _process_all_frames(
        self,
        session: AnalysisSession,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[FrameAnalysis]:
        """
        全フレームの処理
        
        Args:
            session: 解析セッション
            progress_callback: 進捗コールバック
            
        Returns:
            List[FrameAnalysis]: フレーム解析結果リスト
        """
        frame_analyses = []
        total_frames = session.video_metadata.total_frames
        
        # フレーム処理間隔（全フレームを処理すると時間がかかるため間引き）
        frame_step = max(1, total_frames // 1000)  # 最大1000フレーム程度に制限
        
        logger.info(f"📊 Processing {total_frames} frames (step={frame_step})")
        
        # 初期ROI設定
        roi_initialized = False
        if session.roi_selections:
            first_roi = session.roi_selections[0]
            roi_frame_number = first_roi.get("frame_number", 0)
        else:
            roi_frame_number = -1
        
        processed_count = 0
        
        # フレーム処理ループ
        for frame_number, timestamp, frame in self.video_processor.extract_frames_generator(
            start_frame=0,
            end_frame=total_frames,
            step=frame_step
        ):
            try:
                start_time = time.time()
                
                # ROI初期化（該当フレームで実行）
                if not roi_initialized and frame_number >= roi_frame_number and session.roi_selections:
                    roi_selection_data = session.roi_selections[0]
                    from models.data_models import ROISelection, Point3D
                    
                    roi_selection = ROISelection(
                        frame_number=roi_selection_data["frame_number"],
                        click_position=Point3D(
                            x=roi_selection_data["click_position"]["x"],
                            y=roi_selection_data["click_position"]["y"],
                            z=roi_selection_data["click_position"]["z"]
                        )
                    )
                    
                    initial_mask = self.instrument_tracker.set_initial_selection(frame, roi_selection)
                    roi_initialized = initial_mask is not None
                    
                    if roi_initialized:
                        logger.info(f"🎯 ROI initialized at frame {frame_number}")
                
                # 手のトラッキング
                hands_data = self.hand_tracker.process_frame(frame)
                
                # 器具のトラッキング
                instruments_data = []
                if roi_initialized:
                    instrument_data = self.instrument_tracker.track_instrument(frame)
                    if instrument_data:
                        instruments_data.append(instrument_data)
                
                processing_time = time.time() - start_time
                
                # フレーム解析結果作成
                frame_analysis = FrameAnalysis(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    hands=hands_data,
                    instruments=instruments_data,
                    processing_time=processing_time
                )
                
                frame_analyses.append(frame_analysis)
                processed_count += 1
                
                # 進捗通知
                if progress_callback and processed_count % 10 == 0:
                    progress = processed_count / (total_frames // frame_step)
                    progress_callback(min(progress, 0.95))
                
                # 非同期処理のため定期的にyield
                if processed_count % 50 == 0:
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"❌ Error processing frame {frame_number}: {str(e)}")
                continue
        
        logger.info(f"📊 Processed {len(frame_analyses)} frames successfully")
        return frame_analyses
    
    def _generate_analysis_summary(
        self, 
        frame_analyses: List[FrameAnalysis]
    ) -> Dict[str, Any]:
        """
        解析サマリー生成
        
        Args:
            frame_analyses: フレーム解析結果リスト
            
        Returns:
            Dict[str, Any]: サマリーデータ
        """
        try:
            if not frame_analyses:
                return {"status": "no_data"}
            
            # 基本統計
            total_frames = len(frame_analyses)
            frames_with_hands = len([f for f in frame_analyses if f.hands])
            frames_with_instruments = len([f for f in frame_analyses if f.instruments])
            
            # 処理時間統計
            processing_times = [f.processing_time for f in frame_analyses if f.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # 手の統計
            hand_summary = self._generate_hand_summary(frame_analyses)
            
            # 器具の統計
            instrument_summary = self._generate_instrument_summary(frame_analyses)
            
            summary = {
                "analysis_metadata": {
                    "total_frames_analyzed": total_frames,
                    "frames_with_hands": frames_with_hands,
                    "frames_with_instruments": frames_with_instruments,
                    "hand_detection_rate": frames_with_hands / total_frames if total_frames > 0 else 0,
                    "instrument_detection_rate": frames_with_instruments / total_frames if total_frames > 0 else 0,
                    "avg_processing_time_per_frame": avg_processing_time
                },
                "hand_analysis": hand_summary,
                "instrument_analysis": instrument_summary,
                "performance_metrics": {
                    "total_processing_time": sum(processing_times),
                    "fps_equivalent": 1.0 / avg_processing_time if avg_processing_time > 0 else 0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating analysis summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _generate_hand_summary(
        self, 
        frame_analyses: List[FrameAnalysis]
    ) -> Dict[str, Any]:
        """手の解析サマリー生成"""
        try:
            all_hands = []
            for frame in frame_analyses:
                all_hands.extend(frame.hands)
            
            if not all_hands:
                return {"status": "no_hand_data"}
            
            # 手の種類別統計
            left_hands = [h for h in all_hands if h.hand_type == "Left"]
            right_hands = [h for h in all_hands if h.hand_type == "Right"]
            
            # 信頼度統計
            confidences = [h.confidence for h in all_hands]
            avg_confidence = sum(confidences) / len(confidences)
            min_confidence = min(confidences)
            
            # 手の動きの軌跡分析
            movement_analysis = self._analyze_hand_movement(frame_analyses)
            
            summary = {
                "detection_counts": {
                    "total_detections": len(all_hands),
                    "left_hand_detections": len(left_hands),
                    "right_hand_detections": len(right_hands)
                },
                "confidence_stats": {
                    "average_confidence": avg_confidence,
                    "minimum_confidence": min_confidence,
                    "high_confidence_rate": len([c for c in confidences if c > 0.8]) / len(confidences)
                },
                "movement_analysis": movement_analysis
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating hand summary: {str(e)}")
            return {"status": "error"}
    
    def _generate_instrument_summary(
        self, 
        frame_analyses: List[FrameAnalysis]
    ) -> Dict[str, Any]:
        """器具の解析サマリー生成"""
        try:
            all_instruments = []
            for frame in frame_analyses:
                all_instruments.extend(frame.instruments)
            
            if not all_instruments:
                return {"status": "no_instrument_data"}
            
            # 信頼度統計
            confidences = [i.confidence for i in all_instruments]
            avg_confidence = sum(confidences) / len(confidences)
            
            # 器具の移動分析
            positions = [i.pose.position for i in all_instruments]
            total_movement = 0
            
            if len(positions) > 1:
                for i in range(1, len(positions)):
                    dx = positions[i].x - positions[i-1].x
                    dy = positions[i].y - positions[i-1].y
                    distance = (dx*dx + dy*dy) ** 0.5
                    total_movement += distance
            
            # 器具の長さ統計
            lengths = [i.pose.length for i in all_instruments if i.pose.length]
            avg_length = sum(lengths) / len(lengths) if lengths else 0
            
            summary = {
                "detection_counts": {
                    "total_detections": len(all_instruments),
                    "successful_tracking_frames": len([i for i in all_instruments if i.confidence > 0.5])
                },
                "confidence_stats": {
                    "average_confidence": avg_confidence,
                    "tracking_success_rate": len([i for i in all_instruments if i.confidence > 0.5]) / len(all_instruments)
                },
                "movement_analysis": {
                    "total_movement_pixels": total_movement,
                    "average_position": {
                        "x": sum(p.x for p in positions) / len(positions),
                        "y": sum(p.y for p in positions) / len(positions)
                    } if positions else {"x": 0, "y": 0}
                },
                "instrument_metrics": {
                    "average_length_pixels": avg_length,
                    "length_variation": max(lengths) - min(lengths) if len(lengths) > 1 else 0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error generating instrument summary: {str(e)}")
            return {"status": "error"}
    
    def _analyze_hand_movement(
        self, 
        frame_analyses: List[FrameAnalysis]
    ) -> Dict[str, Any]:
        """手の動き解析"""
        try:
            left_hand_positions = []
            right_hand_positions = []
            
            for frame in frame_analyses:
                for hand in frame.hands:
                    if hand.landmarks:
                        wrist = hand.landmarks[0]  # WRIST
                        position = (wrist.position.x, wrist.position.y, frame.timestamp)
                        
                        if hand.hand_type == "Left":
                            left_hand_positions.append(position)
                        else:
                            right_hand_positions.append(position)
            
            # 移動距離計算
            left_movement = self._calculate_movement_distance(left_hand_positions)
            right_movement = self._calculate_movement_distance(right_hand_positions)
            
            return {
                "left_hand_movement": left_movement,
                "right_hand_movement": right_movement,
                "total_movement": left_movement + right_movement
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing hand movement: {str(e)}")
            return {}
    
    def _calculate_movement_distance(
        self, 
        positions: List[Tuple[float, float, float]]
    ) -> float:
        """位置リストから総移動距離を計算"""
        if len(positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            distance = (dx*dx + dy*dy) ** 0.5
            total_distance += distance
        
        return total_distance