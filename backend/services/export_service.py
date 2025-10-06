"""
Export Service - データ出力サービス
解析結果をJSON/CSV/Excel形式で出力
"""

import json
import csv
import os
import pandas as pd
from typing import Dict, Any, List
import logging
from datetime import datetime

import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.data_models import ExportRequest, AnalysisResult

logger = logging.getLogger(__name__)


class ExportService:
    """データ出力サービス"""
    
    def __init__(self):
        self.export_dir = "static/exports"
        os.makedirs(self.export_dir, exist_ok=True)
        logger.info("📤 Export service initialized")
    
    def export_analysis_data(
        self, 
        session_id: str, 
        export_request: ExportRequest
    ) -> str:
        """
        解析データの出力
        
        Args:
            session_id: セッションID
            export_request: 出力リクエスト
            
        Returns:
            str: 出力ファイルパス
        """
        try:
            # 解析結果読み込み
            result_file = f"{self.export_dir}/{session_id}_results.json"
            if not os.path.exists(result_file):
                raise FileNotFoundError(f"Analysis results not found: {result_file}")
            
            with open(result_file, 'r') as f:
                analysis_data = json.load(f)
            
            # フォーマット別出力
            if export_request.format.lower() == "json":
                return self._export_json(session_id, analysis_data, export_request)
            elif export_request.format.lower() == "csv":
                return self._export_csv(session_id, analysis_data, export_request)
            elif export_request.format.lower() == "xlsx":
                return self._export_excel(session_id, analysis_data, export_request)
            else:
                raise ValueError(f"Unsupported export format: {export_request.format}")
                
        except Exception as e:
            logger.error(f"❌ Export error for session {session_id}: {str(e)}")
            raise
    
    def _export_json(
        self, 
        session_id: str, 
        analysis_data: Dict[str, Any], 
        export_request: ExportRequest
    ) -> str:
        """JSON形式での出力"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_id}_export_{timestamp}.json"
            filepath = os.path.join(self.export_dir, filename)
            
            # フィルタリング処理
            filtered_data = self._filter_data(analysis_data, export_request)
            
            # JSON出力
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"📤 JSON export completed: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ JSON export error: {str(e)}")
            raise
    
    def _export_csv(
        self, 
        session_id: str, 
        analysis_data: Dict[str, Any], 
        export_request: ExportRequest
    ) -> str:
        """CSV形式での出力"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 複数CSVファイルを作成（手データ、器具データ別）
            base_filename = f"{session_id}_export_{timestamp}"
            
            files_created = []
            
            if export_request.include_hands:
                hands_file = self._export_hands_csv(analysis_data, base_filename)
                if hands_file:
                    files_created.append(hands_file)
            
            if export_request.include_instruments:
                instruments_file = self._export_instruments_csv(analysis_data, base_filename)
                if instruments_file:
                    files_created.append(instruments_file)
            
            if export_request.include_metadata:
                metadata_file = self._export_metadata_csv(analysis_data, base_filename)
                if metadata_file:
                    files_created.append(metadata_file)
            
            # メインファイルとして最初のファイルを返す
            main_file = files_created[0] if files_created else None
            
            if main_file:
                logger.info(f"📤 CSV export completed: {len(files_created)} files")
                return main_file
            else:
                raise RuntimeError("No data available for CSV export")
                
        except Exception as e:
            logger.error(f"❌ CSV export error: {str(e)}")
            raise
    
    def _export_hands_csv(
        self, 
        analysis_data: Dict[str, Any], 
        base_filename: str
    ) -> str:
        """手データのCSV出力"""
        try:
            filename = f"{base_filename}_hands.csv"
            filepath = os.path.join(self.export_dir, filename)
            
            hands_data = []
            
            for frame_data in analysis_data.get("frames", []):
                frame_number = frame_data.get("frame_number")
                timestamp = frame_data.get("timestamp")
                
                for hand in frame_data.get("hands", []):
                    hand_type = hand.get("hand_type")
                    confidence = hand.get("confidence")
                    
                    for landmark in hand.get("landmarks", []):
                        row = {
                            "frame_number": frame_number,
                            "timestamp": timestamp,
                            "hand_type": hand_type,
                            "hand_confidence": confidence,
                            "landmark_id": landmark.get("id"),
                            "landmark_name": landmark.get("name"),
                            "x": landmark.get("position", {}).get("x"),
                            "y": landmark.get("position", {}).get("y"),
                            "z": landmark.get("position", {}).get("z"),
                            "landmark_confidence": landmark.get("position", {}).get("confidence"),
                            "visibility": landmark.get("visibility")
                        }
                        hands_data.append(row)
            
            if hands_data:
                df = pd.DataFrame(hands_data)
                df.to_csv(filepath, index=False, encoding='utf-8')
                return filepath
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Hands CSV export error: {str(e)}")
            return None
    
    def _export_instruments_csv(
        self, 
        analysis_data: Dict[str, Any], 
        base_filename: str
    ) -> str:
        """器具データのCSV出力"""
        try:
            filename = f"{base_filename}_instruments.csv"
            filepath = os.path.join(self.export_dir, filename)
            
            instruments_data = []
            
            for frame_data in analysis_data.get("frames", []):
                frame_number = frame_data.get("frame_number")
                timestamp = frame_data.get("timestamp")
                
                for instrument in frame_data.get("instruments", []):
                    pose = instrument.get("pose", {})
                    position = pose.get("position", {})
                    rotation = pose.get("rotation", {})
                    tip_position = pose.get("tip_position", {})
                    base_position = pose.get("base_position", {})
                    
                    row = {
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "instrument_id": instrument.get("instrument_id"),
                        "confidence": instrument.get("confidence"),
                        "segmentation_area": instrument.get("segmentation_area"),
                        "center_x": position.get("x"),
                        "center_y": position.get("y"),
                        "center_z": position.get("z"),
                        "rotation_x": rotation.get("x"),
                        "rotation_y": rotation.get("y"),
                        "rotation_z": rotation.get("z"),
                        "tip_x": tip_position.get("x"),
                        "tip_y": tip_position.get("y"),
                        "tip_z": tip_position.get("z"),
                        "base_x": base_position.get("x"),
                        "base_y": base_position.get("y"),
                        "base_z": base_position.get("z"),
                        "length": pose.get("length")
                    }
                    instruments_data.append(row)
            
            if instruments_data:
                df = pd.DataFrame(instruments_data)
                df.to_csv(filepath, index=False, encoding='utf-8')
                return filepath
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Instruments CSV export error: {str(e)}")
            return None
    
    def _export_metadata_csv(
        self, 
        analysis_data: Dict[str, Any], 
        base_filename: str
    ) -> str:
        """メタデータのCSV出力"""
        try:
            filename = f"{base_filename}_metadata.csv"
            filepath = os.path.join(self.export_dir, filename)
            
            # セッション情報
            session_info = analysis_data.get("session", {})
            video_metadata = session_info.get("video_metadata", {})
            summary = analysis_data.get("summary", {})
            
            metadata_rows = [
                {"category": "video", "key": "filename", "value": video_metadata.get("filename")},
                {"category": "video", "key": "duration", "value": video_metadata.get("duration")},
                {"category": "video", "key": "fps", "value": video_metadata.get("fps")},
                {"category": "video", "key": "width", "value": video_metadata.get("width")},
                {"category": "video", "key": "height", "value": video_metadata.get("height")},
                {"category": "video", "key": "total_frames", "value": video_metadata.get("total_frames")},
                {"category": "analysis", "key": "session_id", "value": session_info.get("session_id")},
                {"category": "analysis", "key": "created_at", "value": session_info.get("created_at")},
                {"category": "analysis", "key": "status", "value": session_info.get("status")},
            ]
            
            # サマリー情報追加
            analysis_metadata = summary.get("analysis_metadata", {})
            for key, value in analysis_metadata.items():
                metadata_rows.append({"category": "summary", "key": key, "value": value})
            
            df = pd.DataFrame(metadata_rows)
            df.to_csv(filepath, index=False, encoding='utf-8')
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Metadata CSV export error: {str(e)}")
            return None
    
    def _export_excel(
        self, 
        session_id: str, 
        analysis_data: Dict[str, Any], 
        export_request: ExportRequest
    ) -> str:
        """Excel形式での出力"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{session_id}_export_{timestamp}.xlsx"
            filepath = os.path.join(self.export_dir, filename)
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # メタデータシート
                if export_request.include_metadata:
                    self._write_metadata_sheet(analysis_data, writer)
                
                # 手データシート
                if export_request.include_hands:
                    self._write_hands_sheet(analysis_data, writer)
                
                # 器具データシート
                if export_request.include_instruments:
                    self._write_instruments_sheet(analysis_data, writer)
                
                # サマリーシート
                self._write_summary_sheet(analysis_data, writer)
            
            logger.info(f"📤 Excel export completed: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Excel export error: {str(e)}")
            raise
    
    def _write_metadata_sheet(self, analysis_data: Dict[str, Any], writer):
        """メタデータシートの作成"""
        session_info = analysis_data.get("session", {})
        video_metadata = session_info.get("video_metadata", {})
        
        metadata_data = {
            "Property": [
                "Session ID", "Filename", "Duration (s)", "FPS", 
                "Width", "Height", "Total Frames", "File Size (bytes)",
                "Created At", "Status"
            ],
            "Value": [
                session_info.get("session_id"),
                video_metadata.get("filename"),
                video_metadata.get("duration"),
                video_metadata.get("fps"),
                video_metadata.get("width"),
                video_metadata.get("height"),
                video_metadata.get("total_frames"),
                video_metadata.get("file_size"),
                session_info.get("created_at"),
                session_info.get("status")
            ]
        }
        
        df = pd.DataFrame(metadata_data)
        df.to_excel(writer, sheet_name="Metadata", index=False)
    
    def _write_hands_sheet(self, analysis_data: Dict[str, Any], writer):
        """手データシートの作成"""
        hands_data = []
        
        for frame_data in analysis_data.get("frames", []):
            frame_number = frame_data.get("frame_number")
            timestamp = frame_data.get("timestamp")
            
            for hand in frame_data.get("hands", []):
                # 手の基本情報
                base_row = {
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "hand_type": hand.get("hand_type"),
                    "confidence": hand.get("confidence")
                }
                
                # ランドマーク情報を列として展開
                landmarks = hand.get("landmarks", [])
                for landmark in landmarks:
                    landmark_name = landmark.get("name", f"landmark_{landmark.get('id')}")
                    position = landmark.get("position", {})
                    
                    base_row[f"{landmark_name}_x"] = position.get("x")
                    base_row[f"{landmark_name}_y"] = position.get("y")
                    base_row[f"{landmark_name}_z"] = position.get("z")
                
                hands_data.append(base_row)
        
        if hands_data:
            df = pd.DataFrame(hands_data)
            df.to_excel(writer, sheet_name="Hands", index=False)
    
    def _write_instruments_sheet(self, analysis_data: Dict[str, Any], writer):
        """器具データシートの作成"""
        instruments_data = []
        
        for frame_data in analysis_data.get("frames", []):
            frame_number = frame_data.get("frame_number")
            timestamp = frame_data.get("timestamp")
            
            for instrument in frame_data.get("instruments", []):
                pose = instrument.get("pose", {})
                
                row = {
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "instrument_id": instrument.get("instrument_id"),
                    "confidence": instrument.get("confidence"),
                    "segmentation_area": instrument.get("segmentation_area"),
                    "center_x": pose.get("position", {}).get("x"),
                    "center_y": pose.get("position", {}).get("y"),
                    "center_z": pose.get("position", {}).get("z"),
                    "rotation_x": pose.get("rotation", {}).get("x"),
                    "rotation_y": pose.get("rotation", {}).get("y"),
                    "rotation_z": pose.get("rotation", {}).get("z"),
                    "tip_x": pose.get("tip_position", {}).get("x"),
                    "tip_y": pose.get("tip_position", {}).get("y"),
                    "tip_z": pose.get("tip_position", {}).get("z"),
                    "base_x": pose.get("base_position", {}).get("x"),
                    "base_y": pose.get("base_position", {}).get("y"),
                    "base_z": pose.get("base_position", {}).get("z"),
                    "length": pose.get("length")
                }
                instruments_data.append(row)
        
        if instruments_data:
            df = pd.DataFrame(instruments_data)
            df.to_excel(writer, sheet_name="Instruments", index=False)
    
    def _write_summary_sheet(self, analysis_data: Dict[str, Any], writer):
        """サマリーシートの作成"""
        summary = analysis_data.get("summary", {})
        
        summary_rows = []
        
        # 解析メタデータ
        analysis_metadata = summary.get("analysis_metadata", {})
        for key, value in analysis_metadata.items():
            summary_rows.append({"Category": "Analysis", "Metric": key, "Value": value})
        
        # 手の解析結果
        hand_analysis = summary.get("hand_analysis", {})
        if isinstance(hand_analysis, dict):
            for category, data in hand_analysis.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        summary_rows.append({"Category": f"Hand_{category}", "Metric": key, "Value": value})
                else:
                    summary_rows.append({"Category": "Hand", "Metric": category, "Value": data})
        
        # 器具の解析結果
        instrument_analysis = summary.get("instrument_analysis", {})
        if isinstance(instrument_analysis, dict):
            for category, data in instrument_analysis.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        summary_rows.append({"Category": f"Instrument_{category}", "Metric": key, "Value": value})
                else:
                    summary_rows.append({"Category": "Instrument", "Metric": category, "Value": data})
        
        if summary_rows:
            df = pd.DataFrame(summary_rows)
            df.to_excel(writer, sheet_name="Summary", index=False)
    
    def _filter_data(
        self, 
        analysis_data: Dict[str, Any], 
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """出力リクエストに基づくデータフィルタリング"""
        filtered_data = {}
        
        # メタデータ
        if export_request.include_metadata:
            filtered_data["session"] = analysis_data.get("session", {})
            filtered_data["summary"] = analysis_data.get("summary", {})
        
        # フレームデータのフィルタリング
        frames = analysis_data.get("frames", [])
        
        # フレーム範囲フィルタリング
        if export_request.frame_range:
            start_frame = export_request.frame_range.get("start", 0)
            end_frame = export_request.frame_range.get("end", len(frames))
            frames = frames[start_frame:end_frame]
        
        # フレーム内容フィルタリング
        filtered_frames = []
        for frame in frames:
            filtered_frame = {
                "frame_number": frame.get("frame_number"),
                "timestamp": frame.get("timestamp"),
                "processing_time": frame.get("processing_time")
            }
            
            if export_request.include_hands:
                filtered_frame["hands"] = frame.get("hands", [])
            
            if export_request.include_instruments:
                filtered_frame["instruments"] = frame.get("instruments", [])
            
            filtered_frames.append(filtered_frame)
        
        filtered_data["frames"] = filtered_frames
        
        return filtered_data


# ユーティリティ関数
def create_analysis_report(analysis_data: Dict[str, Any]) -> str:
    """
    解析レポートテキストの生成
    
    Args:
        analysis_data: 解析データ
        
    Returns:
        str: レポートテキスト
    """
    try:
        session = analysis_data.get("session", {})
        summary = analysis_data.get("summary", {})
        
        report_lines = [
            "# Surgi-Motion Visualizer - 解析レポート",
            f"## セッション情報",
            f"- セッションID: {session.get('session_id')}",
            f"- 動画ファイル: {session.get('video_metadata', {}).get('filename')}",
            f"- 解析日時: {session.get('created_at')}",
            f"",
            f"## 解析結果サマリー"
        ]
        
        analysis_metadata = summary.get("analysis_metadata", {})
        for key, value in analysis_metadata.items():
            report_lines.append(f"- {key}: {value}")
        
        return "\n".join(report_lines)
        
    except Exception as e:
        logger.error(f"❌ Error creating analysis report: {str(e)}")
        return f"レポート生成エラー: {str(e)}"