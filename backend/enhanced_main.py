#!/usr/bin/env python3
"""
Enhanced FastAPI Backend with SAM2 ROI Tracking
SAM2 ROIトラッキング機能付き拡張バックエンド
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import shutil
from datetime import datetime
from pathlib import Path
import logging
import asyncio

# Import services
from services.roi_tracking_service import roi_tracking_service
from services.sam2_service import sam2_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ディレクトリ作成
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/exports", exist_ok=True)
os.makedirs("static/thumbnails", exist_ok=True)

# FastAPI アプリ初期化
app = FastAPI(
    title="Surgi-Motion Visualizer API Enhanced",
    description="手術手技3D分析システム - SAM2 ROIトラッキング対応",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class ROIData(BaseModel):
    points: List[List[float]]
    roi_type: str = "polygon"  # rectangle, rotated_rectangle, polygon

class TrackingOptions(BaseModel):
    frame_skip: int = 1
    max_frames: Optional[int] = None
    tracking_method: str = "sam2"
    export_formats: List[str] = ["json", "csv"]

class ExportRequest(BaseModel):
    format_type: str = "json"  # json, csv, excel

# セッションストレージ
sessions = {}

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "🏥 Surgi-Motion Visualizer API Enhanced",
        "version": "2.0.0",
        "features": [
            "SAM2 Integration",
            "Interactive ROI Selection",
            "Real-time Instrument Tracking",
            "3D Visualization",
            "Multi-format Export"
        ],
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "upload": "POST /api/upload",
            "create_session": "POST /api/sessions",
            "set_roi": "POST /api/sessions/{session_id}/roi",
            "start_tracking": "POST /api/sessions/{session_id}/tracking/start",
            "get_status": "GET /api/sessions/{session_id}/status",
            "get_results": "GET /api/sessions/{session_id}/results",
            "export_results": "POST /api/sessions/{session_id}/export",
            "update_roi": "PUT /api/sessions/{session_id}/roi"
        }
    }

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """動画アップロード"""
    try:
        # ファイルサイズチェック
        if file.size and file.size > 1000 * 1024 * 1024:  # 1GB制限
            raise HTTPException(status_code=413, detail="ファイルサイズが大きすぎます (最大: 1GB)")
        
        # ファイル形式チェック
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"対応していないファイル形式: {file_ext}")
        
        # セッションID生成
        session_id = f"session_{int(datetime.now().timestamp())}"
        
        # ファイル保存
        file_path = f"static/uploads/{session_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # セッション情報保存
        sessions[session_id] = {
            "session_id": session_id,
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded",
            "file_size": os.path.getsize(file_path)
        }
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "file_size": sessions[session_id]["file_size"],
            "status": "uploaded",
            "message": "動画アップロード完了",
            "next_step": "ROI選択を行ってください"
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"アップロードエラー: {str(e)}")

@app.post("/api/sessions")
async def create_tracking_session(session_id: str):
    """トラッキングセッション作成"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session_info = sessions[session_id]
        video_path = session_info["file_path"]
        
        # ROIトラッキングサービスでセッション作成
        result = roi_tracking_service.create_session(session_id, video_path)
        
        # セッション情報更新
        sessions[session_id].update({
            "video_properties": result["video_properties"],
            "status": "ready_for_roi"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail=f"セッション作成エラー: {str(e)}")

@app.post("/api/sessions/{session_id}/roi")
async def set_roi(session_id: str, roi_data: ROIData):
    """ROI設定"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # ROI設定
        result = roi_tracking_service.set_roi(
            session_id, 
            roi_data.points, 
            roi_data.roi_type
        )
        
        # セッション情報更新
        sessions[session_id]["status"] = "roi_set"
        sessions[session_id]["roi_info"] = result
        
        return result
        
    except Exception as e:
        logger.error(f"ROI setting error: {e}")
        raise HTTPException(status_code=500, detail=f"ROI設定エラー: {str(e)}")

@app.put("/api/sessions/{session_id}/roi")
async def update_roi(session_id: str, roi_data: ROIData):
    """ROI更新"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # ROI更新
        result = roi_tracking_service.update_roi(
            session_id, 
            roi_data.points, 
            roi_data.roi_type
        )
        
        # セッション情報更新
        sessions[session_id]["roi_info"] = result
        
        return result
        
    except Exception as e:
        logger.error(f"ROI update error: {e}")
        raise HTTPException(status_code=500, detail=f"ROI更新エラー: {str(e)}")

@app.post("/api/sessions/{session_id}/tracking/start")
async def start_tracking(
    session_id: str, 
    options: TrackingOptions = TrackingOptions(),
    background_tasks: BackgroundTasks = None
):
    """トラッキング開始"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # トラッキング開始
        result = roi_tracking_service.start_tracking(
            session_id, 
            options.dict()
        )
        
        # セッション情報更新
        sessions[session_id]["status"] = "tracking_started"
        sessions[session_id]["tracking_options"] = options.dict()
        
        return result
        
    except Exception as e:
        logger.error(f"Tracking start error: {e}")
        raise HTTPException(status_code=500, detail=f"トラッキング開始エラー: {str(e)}")

@app.get("/api/sessions/{session_id}/status")
async def get_tracking_status(session_id: str):
    """トラッキング状況取得"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # サービスから状況取得
        status = roi_tracking_service.get_tracking_status(session_id)
        
        # セッション情報と統合
        session_info = sessions[session_id]
        status.update({
            "filename": session_info["filename"],
            "uploaded_at": session_info["uploaded_at"],
            "file_size": session_info.get("file_size", 0)
        })
        
        return status
        
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"状況取得エラー: {str(e)}")

@app.get("/api/sessions/{session_id}/results")
async def get_tracking_results(session_id: str):
    """トラッキング結果取得"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # 結果取得
        results = roi_tracking_service.get_tracking_results(session_id)
        
        return results
        
    except Exception as e:
        logger.error(f"Results retrieval error: {e}")
        raise HTTPException(status_code=500, detail=f"結果取得エラー: {str(e)}")

@app.post("/api/sessions/{session_id}/export")
async def export_results(session_id: str, export_request: ExportRequest):
    """結果エクスポート"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # エクスポート実行
        result = roi_tracking_service.export_results(
            session_id, 
            export_request.format_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"エクスポートエラー: {str(e)}")

@app.get("/api/sessions/{session_id}/export/{filename}")
async def download_export(session_id: str, filename: str):
    """エクスポートファイルダウンロード"""
    try:
        file_path = Path(f"static/exports/{filename}")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=f"ダウンロードエラー: {str(e)}")

@app.get("/api/sessions")
async def list_sessions():
    """全セッション一覧"""
    return {
        "sessions": list(sessions.values()),
        "total_sessions": len(sessions),
        "active_sessions": len([s for s in sessions.values() if s["status"] in ["tracking_started", "roi_set"]])
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """セッション削除"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session_info = sessions[session_id]
        
        # ファイル削除
        if os.path.exists(session_info["file_path"]):
            os.remove(session_info["file_path"])
        
        # セッション削除
        del sessions[session_id]
        
        return {
            "session_id": session_id,
            "message": "セッション削除完了"
        }
        
    except Exception as e:
        logger.error(f"Session deletion error: {e}")
        raise HTTPException(status_code=500, detail=f"セッション削除エラー: {str(e)}")

@app.get("/api/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "sam2_service": "active",
            "roi_tracking_service": "active"
        },
        "memory_usage": "N/A",  # Could add actual memory usage monitoring
        "active_sessions": len(sessions)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced Surgi-Motion Visualizer Backend")
    print("🎯 Features: SAM2 Integration, Interactive ROI, Real-time Tracking")
    print("📡 Server will be available at: http://localhost:8000")
    print("📖 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "enhanced_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )