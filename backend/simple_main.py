#!/usr/bin/env python3
"""
Simplified FastAPI Backend for Testing
簡易版バックエンドサーバー
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
import os
from datetime import datetime
from pathlib import Path

# ディレクトリ作成
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/exports", exist_ok=True)

# FastAPI アプリ初期化
app = FastAPI(
    title="Surgi-Motion Visualizer API (Simple)",
    description="手術手技3D分析システムの簡易版API",
    version="1.0.0"
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

# セッションストレージ（簡易版）
sessions = {}

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "🏥 Surgi-Motion Visualizer API (Simplified Version)",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "upload": "POST /api/upload",
            "roi_selection": "POST /api/roi_selection/{session_id}",
            "analyze": "POST /api/analyze/{session_id}",
            "status": "GET /api/status/{session_id}",
            "results": "GET /api/results/{session_id}",
            "demo": "GET /demo"
        }
    }

@app.get("/demo")
async def demo_page():
    """デモページ"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Surgi-Motion Visualizer Demo</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .status-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border-left: 4px solid #28a745;
            }
            .api-test {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
            }
            button {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
            }
            button:hover {
                background: #0056b3;
            }
            .result {
                background: #f1f3f4;
                padding: 10px;
                border-radius: 5px;
                font-family: monospace;
                margin-top: 10px;
                white-space: pre-wrap;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Surgi-Motion Visualizer</h1>
                <h2>手術手技3D分析システム - デモページ</h2>
            </div>

            <div class="status-card">
                <h3>✅ システム稼働状況</h3>
                <p><strong>バックエンドAPI:</strong> 正常動作中</p>
                <p><strong>アクセス時刻:</strong> <span id="current-time"></span></p>
                <p><strong>サーバー:</strong> FastAPI + Uvicorn</p>
            </div>

            <div class="api-test">
                <h3>🔧 API テスト</h3>
                <button onclick="testHealthCheck()">ヘルスチェック</button>
                <button onclick="testFileUpload()">ファイルアップロードテスト</button>
                <button onclick="testAnalysis()">解析テスト</button>
                <div id="api-result" class="result"></div>
            </div>

            <div class="status-card">
                <h3>🚀 アプリケーション起動方法</h3>
                <ol>
                    <li><strong>このAPIサーバー:</strong> 既に起動中 ✅</li>
                    <li><strong>フロントエンド:</strong> 別ターミナルで起動が必要</li>
                </ol>
                
                <h4>📋 手動でフロントエンドを起動:</h4>
                <div class="result">
# 新しいターミナルで実行
cd /home/user/webapp/frontend/public
python3 -m http.server 3000

# または
cd /home/user/webapp
./start_frontend.sh
                </div>
                
                <p><strong>フロントエンドURL:</strong> <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></p>
            </div>

            <div class="status-card">
                <h3>📚 API文書・リソース</h3>
                <p><a href="/docs" target="_blank">📖 Swagger UI</a></p>
                <p><a href="/redoc" target="_blank">📄 ReDoc</a></p>
                <p><a href="/" target="_blank">🔧 API Status</a></p>
            </div>
        </div>

        <script>
            // 現在時刻表示
            document.getElementById('current-time').textContent = new Date().toLocaleString();
            
            // API テスト関数
            async function testHealthCheck() {
                const result = document.getElementById('api-result');
                result.textContent = '🔄 ヘルスチェック実行中...';
                
                try {
                    const response = await fetch('/');
                    const data = await response.json();
                    result.textContent = '✅ ヘルスチェック成功:\\n' + JSON.stringify(data, null, 2);
                } catch (error) {
                    result.textContent = '❌ エラー: ' + error.message;
                }
            }
            
            async function testFileUpload() {
                const result = document.getElementById('api-result');
                result.textContent = '📤 ファイルアップロードテスト中...';
                
                // ダミーファイルを作成
                const dummyFile = new Blob(['dummy video data'], {type: 'video/mp4'});
                const formData = new FormData();
                formData.append('file', dummyFile, 'test.mp4');
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    result.textContent = '✅ アップロード成功:\\n' + JSON.stringify(data, null, 2);
                } catch (error) {
                    result.textContent = '❌ エラー: ' + error.message;
                }
            }
            
            async function testAnalysis() {
                const result = document.getElementById('api-result');
                result.textContent = '🧪 解析テスト実行中...';
                result.textContent = '💡 解析機能はフルバージョンで利用可能です。\\n現在は簡易版APIが動作中です。';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """動画アップロード（簡易版）"""
    try:
        # ファイルサイズチェック
        if file.size and file.size > 500 * 1024 * 1024:  # 500MB制限
            raise HTTPException(status_code=413, detail="ファイルサイズが大きすぎます")
        
        # セッションID生成
        session_id = f"session_{int(datetime.now().timestamp())}"
        
        # ファイル保存
        file_path = f"static/uploads/{file.filename}"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # セッション情報保存
        sessions[session_id] = {
            "session_id": session_id,
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": datetime.now().isoformat(),
            "status": "uploaded"
        }
        
        return {
            "session_id": session_id,
            "filename": file.filename,
            "file_size": len(content),
            "status": "uploaded",
            "message": "動画アップロード完了"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"アップロードエラー: {str(e)}")

@app.post("/api/roi_selection/{session_id}")
async def set_roi_selection(session_id: str, roi_data: dict):
    """ROI選択（簡易版）"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    sessions[session_id]["roi_selection"] = roi_data
    sessions[session_id]["status"] = "roi_selected"
    
    return {"status": "success", "message": "ROI選択完了"}

@app.post("/api/analyze/{session_id}")
async def start_analysis(session_id: str):
    """解析開始（簡易版）"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    sessions[session_id]["status"] = "completed"  # 簡易版では即座に完了
    
    return {"status": "success", "message": "解析完了（簡易版）"}

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """ステータス取得"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    return {
        "session_id": session_id,
        "status": sessions[session_id]["status"],
        "progress": 1.0 if sessions[session_id]["status"] == "completed" else 0.5,
        "message": "処理完了" if sessions[session_id]["status"] == "completed" else "処理中"
    }

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """結果取得（ダミーデータ）"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="セッションが見つかりません")
    
    # ダミーの解析結果
    return {
        "session_id": session_id,
        "analysis_complete": True,
        "frames": [
            {
                "frame_number": 0,
                "timestamp": 0.0,
                "hands": [
                    {
                        "hand_type": "Right",
                        "confidence": 0.95,
                        "landmarks": [
                            {"id": 0, "name": "WRIST", "position": {"x": 320, "y": 240, "z": 0}}
                        ]
                    }
                ],
                "instruments": []
            }
        ],
        "summary": {
            "total_frames": 1,
            "hands_detected": 1,
            "instruments_detected": 0
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Surgi-Motion Visualizer Backend (Simple Version)")
    print("📡 Server will be available at: http://localhost:8000")
    print("📖 API docs: http://localhost:8000/docs")
    print("🎪 Demo page: http://localhost:8000/demo")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )