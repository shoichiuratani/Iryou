"""
Surgi-Motion Visualizer - FastAPI Backend
メインアプリケーションエントリーポイント
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import os
import sys
import logging
from typing import List, Optional

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from models.data_models import (
    AnalysisSession, 
    AnalysisResult, 
    ROISelection, 
    ExportRequest, 
    ProcessingStatus,
    VideoMetadata
)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# グローバル変数（実際のプロダクションでは適切なデータベースを使用）
analysis_sessions = {}
processing_status_cache = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーション起動・終了時の処理"""
    logger.info("🚀 Surgi-Motion Visualizer Backend Starting...")
    
    # 起動時処理
    os.makedirs("static/uploads", exist_ok=True)
    os.makedirs("static/exports", exist_ok=True)
    
    yield
    
    # 終了時処理
    logger.info("🛑 Surgi-Motion Visualizer Backend Shutting down...")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="Surgi-Motion Visualizer API",
    description="手術手技3D分析システムのバックエンドAPI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 実際のプロダクションでは適切に制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルサービング
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Surgi-Motion Visualizer API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "upload": "/api/upload",
            "analyze": "/api/analyze/{session_id}",
            "status": "/api/status/{session_id}",
            "results": "/api/results/{session_id}",
            "export": "/api/export"
        }
    }


@app.post("/api/upload", response_model=AnalysisSession)
async def upload_video(file: UploadFile = File(...)):
    """
    動画ファイルのアップロード
    """
    try:
        # ファイル形式チェック
        if not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=400, 
                detail="動画ファイルのみアップロード可能です"
            )
        
        # ファイル保存
        file_path = f"static/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 動画メタデータ取得（OpenCVで実装）
        from services.video_service import VideoProcessor
        video_processor = VideoProcessor()
        metadata = video_processor.get_video_metadata(file_path)
        
        # 解析セッション作成
        session = AnalysisSession(
            video_metadata=metadata,
            status="uploaded"
        )
        
        # セッションをキャッシュに保存
        analysis_sessions[session.session_id] = session
        processing_status_cache[session.session_id] = ProcessingStatus(
            session_id=session.session_id,
            status="uploaded",
            progress=0.0,
            message="動画アップロード完了"
        )
        
        logger.info(f"✅ Video uploaded: {file.filename} -> Session: {session.session_id}")
        
        return session
        
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/roi_selection/{session_id}")
async def set_roi_selection(
    session_id: str, 
    roi_selection: ROISelection
):
    """
    ROI選択情報の設定
    """
    try:
        if session_id not in analysis_sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session = analysis_sessions[session_id]
        session.roi_selections.append(roi_selection.dict())
        
        logger.info(f"🎯 ROI selection set for session: {session_id}")
        
        return {"status": "success", "message": "ROI選択が設定されました"}
        
    except Exception as e:
        logger.error(f"❌ ROI selection error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze/{session_id}")
async def start_analysis(
    session_id: str, 
    background_tasks: BackgroundTasks
):
    """
    解析処理開始
    """
    try:
        if session_id not in analysis_sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session = analysis_sessions[session_id]
        if session.status == "processing":
            raise HTTPException(status_code=400, detail="既に解析処理中です")
        
        # バックグラウンドで解析処理を開始
        background_tasks.add_task(process_video_analysis, session_id)
        
        # ステータス更新
        session.status = "processing"
        processing_status_cache[session_id].status = "processing"
        processing_status_cache[session_id].message = "解析処理を開始しました"
        
        logger.info(f"🔄 Analysis started for session: {session_id}")
        
        return {
            "session_id": session_id,
            "status": "processing",
            "message": "解析処理を開始しました"
        }
        
    except Exception as e:
        logger.error(f"❌ Analysis start error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/{session_id}", response_model=ProcessingStatus)
async def get_processing_status(session_id: str):
    """
    処理状況の取得
    """
    if session_id not in processing_status_cache:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    return processing_status_cache[session_id]


@app.get("/api/results/{session_id}")
async def get_analysis_results(session_id: str):
    """
    解析結果の取得
    """
    try:
        if session_id not in analysis_sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        session = analysis_sessions[session_id]
        if session.status != "completed":
            raise HTTPException(status_code=400, detail="解析がまだ完了していません")
        
        # 結果ファイルの読み込み
        result_file = f"static/exports/{session_id}_results.json"
        if os.path.exists(result_file):
            import json
            with open(result_file, 'r') as f:
                results = json.load(f)
            return results
        else:
            raise HTTPException(status_code=404, detail="解析結果が見つかりません")
        
    except Exception as e:
        logger.error(f"❌ Results retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export")
async def export_data(export_request: ExportRequest):
    """
    データ出力
    """
    try:
        session_id = export_request.session_id
        if session_id not in analysis_sessions:
            raise HTTPException(status_code=404, detail="セッションが見つかりません")
        
        # 出力処理（実装は後ほど）
        from services.export_service import ExportService
        export_service = ExportService()
        
        file_path = export_service.export_analysis_data(
            session_id, 
            export_request
        )
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"❌ Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_video_analysis(session_id: str):
    """
    バックグラウンド動画解析処理
    """
    try:
        logger.info(f"🔄 Starting background analysis for session: {session_id}")
        
        # 解析処理サービスの実行
        from services.analysis_service import AnalysisService
        analysis_service = AnalysisService()
        
        # 処理実行
        results = await analysis_service.process_full_analysis(
            session_id,
            progress_callback=lambda p: update_progress(session_id, p)
        )
        
        # 結果保存
        result_file = f"static/exports/{session_id}_results.json"
        import json
        with open(result_file, 'w') as f:
            json.dump(results.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # ステータス更新
        analysis_sessions[session_id].status = "completed"
        processing_status_cache[session_id].status = "completed"
        processing_status_cache[session_id].progress = 1.0
        processing_status_cache[session_id].message = "解析完了"
        
        logger.info(f"✅ Analysis completed for session: {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Background analysis error: {str(e)}")
        
        # エラー状態に更新
        analysis_sessions[session_id].status = "failed"
        processing_status_cache[session_id].status = "failed"
        processing_status_cache[session_id].error = str(e)


def update_progress(session_id: str, progress: float):
    """進捗更新コールバック"""
    if session_id in processing_status_cache:
        processing_status_cache[session_id].progress = progress
        processing_status_cache[session_id].message = f"解析中... {progress*100:.1f}%"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )