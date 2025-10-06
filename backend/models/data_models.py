"""
Data models for Surgi-Motion Visualizer
定義するデータ構造：
- 手のランドマークデータ
- 手術器具トラッキングデータ
- 解析結果データ
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class Point3D(BaseModel):
    """3次元座標点"""
    x: float
    y: float
    z: float
    confidence: Optional[float] = None


class HandLandmark(BaseModel):
    """手のランドマーク（MediaPipe準拠）"""
    id: int = Field(..., description="ランドマークID (0-20)")
    name: str = Field(..., description="ランドマーク名")
    position: Point3D
    visibility: Optional[float] = None


class HandData(BaseModel):
    """単一フレームの手データ"""
    hand_type: str = Field(..., description="Left or Right")
    landmarks: List[HandLandmark]
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    
class InstrumentPose(BaseModel):
    """器具の姿勢情報"""
    position: Point3D = Field(..., description="器具の中心位置")
    rotation: Point3D = Field(..., description="回転ベクトル (x, y, z)")
    tip_position: Optional[Point3D] = Field(None, description="器具の先端位置")
    base_position: Optional[Point3D] = Field(None, description="器具の基部位置")
    length: Optional[float] = Field(None, description="器具の長さ（ピクセル）")


class InstrumentData(BaseModel):
    """器具トラッキングデータ"""
    instrument_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pose: InstrumentPose
    confidence: float = Field(..., ge=0.0, le=1.0)
    segmentation_area: Optional[float] = Field(None, description="セグメンテーション領域の面積")


class FrameAnalysis(BaseModel):
    """単一フレームの解析結果"""
    frame_number: int
    timestamp: float = Field(..., description="フレームのタイムスタンプ（秒）")
    hands: List[HandData] = Field(default_factory=list)
    instruments: List[InstrumentData] = Field(default_factory=list)
    processing_time: Optional[float] = Field(None, description="処理時間（秒）")


class VideoMetadata(BaseModel):
    """動画メタデータ"""
    filename: str
    duration: float = Field(..., description="動画の長さ（秒）")
    fps: float = Field(..., description="フレームレート")
    width: int = Field(..., description="動画の幅（ピクセル）")
    height: int = Field(..., description="動画の高さ（ピクセル）")
    total_frames: int = Field(..., description="総フレーム数")
    file_size: int = Field(..., description="ファイルサイズ（バイト）")


class AnalysisSession(BaseModel):
    """解析セッション情報"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_metadata: VideoMetadata
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="pending", description="pending, processing, completed, failed")
    roi_selections: List[Dict[str, Any]] = Field(default_factory=list, description="ROI選択情報")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="処理進捗")
    

class AnalysisResult(BaseModel):
    """完全な解析結果"""
    session: AnalysisSession
    frames: List[FrameAnalysis]
    summary: Optional[Dict[str, Any]] = Field(None, description="解析サマリー")
    export_formats: List[str] = Field(default_factory=lambda: ["json", "csv"])


class ROISelection(BaseModel):
    """ROI選択情報"""
    frame_number: int
    click_position: Point3D = Field(..., description="クリック位置（2D + timestamp）")
    selection_type: str = Field(default="instrument", description="selection type")
    label: Optional[str] = Field(None, description="ユーザー定義ラベル")


class ExportRequest(BaseModel):
    """データ出力リクエスト"""
    session_id: str
    format: str = Field(..., description="json, csv, or xlsx")
    include_metadata: bool = Field(default=True)
    include_hands: bool = Field(default=True)
    include_instruments: bool = Field(default=True)
    frame_range: Optional[Dict[str, int]] = Field(None, description="start, end frame numbers")


class ProcessingStatus(BaseModel):
    """処理ステータス"""
    session_id: str
    status: str = Field(..., description="pending, processing, completed, failed")
    progress: float = Field(..., ge=0.0, le=1.0)
    current_frame: Optional[int] = None
    total_frames: Optional[int] = None
    estimated_remaining_time: Optional[float] = Field(None, description="推定残り時間（秒）")
    message: Optional[str] = None
    error: Optional[str] = None


# MediaPipe Handsのランドマーク名定義
HAND_LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP",
    "MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP",
    "RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP"
]


# 手指接続関係（スケルトン描画用）
HAND_CONNECTIONS = [
    # 親指
    (0, 1), (1, 2), (2, 3), (3, 4),
    # 人差し指
    (0, 5), (5, 6), (6, 7), (7, 8),
    # 中指
    (0, 9), (9, 10), (10, 11), (11, 12),
    # 薬指
    (0, 13), (13, 14), (14, 15), (15, 16),
    # 小指
    (0, 17), (17, 18), (18, 19), (19, 20)
]