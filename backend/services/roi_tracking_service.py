#!/usr/bin/env python3
"""
ROI Selection and Tracking Service
ROI選択・トラッキングサービス
"""

import numpy as np
import cv2
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from pathlib import Path
from .sam2_service import sam2_service

logger = logging.getLogger(__name__)

class ROITrackingService:
    """Service for ROI selection and instrument tracking"""
    
    def __init__(self):
        """Initialize ROI tracking service"""
        self.sam2_service = sam2_service
        self.active_sessions = {}
    
    def create_session(self, session_id: str, video_path: str) -> Dict:
        """
        Create a new tracking session
        
        Args:
            session_id: Unique session identifier
            video_path: Path to the video file
            
        Returns:
            Session metadata
        """
        try:
            # Load video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Cannot open video file: {video_path}")
            
            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Read first frame for ROI selection
            ret, first_frame = cap.read()
            if not ret:
                raise ValueError("Cannot read first frame from video")
            
            cap.release()
            
            # Store session data
            session_data = {
                "session_id": session_id,
                "video_path": video_path,
                "video_properties": {
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "frame_count": frame_count,
                    "duration": frame_count / fps if fps > 0 else 0
                },
                "first_frame": first_frame,
                "roi_data": None,
                "tracking_results": {},
                "status": "ready_for_roi"
            }
            
            self.active_sessions[session_id] = session_data
            
            return {
                "session_id": session_id,
                "video_properties": session_data["video_properties"],
                "status": "ready_for_roi",
                "message": "Session created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise
    
    def set_roi(
        self, 
        session_id: str, 
        roi_points: List[List[float]], 
        roi_type: str = "polygon"
    ) -> Dict:
        """
        Set ROI for tracking
        
        Args:
            session_id: Session identifier
            roi_points: List of [x, y] coordinates defining ROI
            roi_type: Type of ROI ("rectangle", "rotated_rectangle", "polygon")
            
        Returns:
            ROI confirmation data
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Validate ROI points
        if not roi_points or len(roi_points) < 2:
            raise ValueError("ROI must have at least 2 points")
        
        # Convert to integer coordinates
        roi_points_int = [(int(point[0]), int(point[1])) for point in roi_points]
        
        # Validate coordinates are within frame bounds
        width, height = session["video_properties"]["width"], session["video_properties"]["height"]
        for x, y in roi_points_int:
            if x < 0 or x >= width or y < 0 or y >= height:
                raise ValueError(f"ROI point ({x}, {y}) is outside frame bounds")
        
        # Create ROI mask
        roi_mask = self.sam2_service.create_roi_from_points(
            roi_points_int, 
            roi_type, 
            (height, width)
        )
        
        # Extract initial instruments from first frame
        first_frame = session["first_frame"]
        initial_detection = self.sam2_service.extract_masks_from_roi(
            first_frame, roi_points_int, roi_type
        )
        
        # Store ROI data
        roi_data = {
            "points": roi_points_int,
            "type": roi_type,
            "mask": roi_mask,
            "area": np.sum(roi_mask > 0),
            "initial_detection": initial_detection
        }
        
        session["roi_data"] = roi_data
        session["status"] = "roi_set"
        
        return {
            "session_id": session_id,
            "roi_area": roi_data["area"],
            "instruments_detected": len(initial_detection["masks"]),
            "instrument_types": [inst["type"] for inst in initial_detection["masks"]],
            "confidence_scores": initial_detection["confidence_scores"],
            "status": "roi_set",
            "message": "ROI set successfully"
        }
    
    def start_tracking(self, session_id: str, options: Dict = None) -> Dict:
        """
        Start instrument tracking in the specified ROI
        
        Args:
            session_id: Session identifier
            options: Tracking options
            
        Returns:
            Tracking start confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        if session["status"] != "roi_set":
            raise ValueError("ROI must be set before starting tracking")
        
        # Set default tracking options
        default_options = {
            "frame_skip": 1,  # Process every frame
            "max_frames": None,  # Process all frames
            "tracking_method": "sam2",
            "export_format": ["json", "csv"]
        }
        
        if options:
            default_options.update(options)
        
        session["tracking_options"] = default_options
        session["status"] = "tracking_started"
        
        # Start background tracking process
        self._run_tracking(session_id)
        
        return {
            "session_id": session_id,
            "status": "tracking_started",
            "tracking_options": default_options,
            "message": "Tracking started successfully"
        }
    
    def _run_tracking(self, session_id: str):
        """Run the tracking process"""
        try:
            session = self.active_sessions[session_id]
            video_path = session["video_path"]
            roi_data = session["roi_data"]
            options = session["tracking_options"]
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Cannot open video file")
            
            # Tracking results
            tracking_results = {
                "frames": [],
                "instruments": {},
                "summary": {
                    "total_frames_processed": 0,
                    "instruments_tracked": 0,
                    "processing_time": 0
                }
            }
            
            frame_idx = 0
            max_frames = options.get("max_frames")
            frame_skip = options.get("frame_skip", 1)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames if needed
                if frame_idx % frame_skip != 0:
                    frame_idx += 1
                    continue
                
                # Check max frames limit
                if max_frames and len(tracking_results["frames"]) >= max_frames:
                    break
                
                # Process frame
                frame_result = self.sam2_service.extract_masks_from_roi(
                    frame, roi_data["points"], roi_data["type"]
                )
                
                # Add timestamp and frame info
                frame_result["frame_index"] = frame_idx
                frame_result["timestamp"] = frame_idx / session["video_properties"]["fps"]
                
                tracking_results["frames"].append(frame_result)
                
                # Update progress
                progress = min(1.0, frame_idx / session["video_properties"]["frame_count"])
                session["progress"] = progress
                
                frame_idx += 1
            
            cap.release()
            
            # Update summary
            tracking_results["summary"]["total_frames_processed"] = len(tracking_results["frames"])
            tracking_results["summary"]["instruments_tracked"] = len(
                set(inst["type"] for frame in tracking_results["frames"] for inst in frame["masks"])
            )
            
            # Store results
            session["tracking_results"] = tracking_results
            session["status"] = "tracking_completed"
            session["progress"] = 1.0
            
        except Exception as e:
            logger.error(f"Tracking error for session {session_id}: {e}")
            session["status"] = "tracking_error"
            session["error"] = str(e)
    
    def get_tracking_status(self, session_id: str) -> Dict:
        """
        Get current tracking status
        
        Args:
            session_id: Session identifier
            
        Returns:
            Status information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "progress": session.get("progress", 0.0),
            "frames_processed": len(session.get("tracking_results", {}).get("frames", [])),
            "error": session.get("error"),
            "video_properties": session["video_properties"]
        }
    
    def get_tracking_results(self, session_id: str) -> Dict:
        """
        Get tracking results
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete tracking results
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        if session["status"] != "tracking_completed":
            raise ValueError("Tracking not completed yet")
        
        return {
            "session_id": session_id,
            "tracking_results": session["tracking_results"],
            "roi_data": {
                "points": session["roi_data"]["points"],
                "type": session["roi_data"]["type"],
                "area": session["roi_data"]["area"]
            },
            "video_properties": session["video_properties"]
        }
    
    def export_results(self, session_id: str, format_type: str = "json") -> Dict:
        """
        Export tracking results in specified format
        
        Args:
            session_id: Session identifier
            format_type: Export format ("json", "csv", "excel")
            
        Returns:
            Export information
        """
        results = self.get_tracking_results(session_id)
        
        # Create export directory
        export_dir = Path("static/exports")
        export_dir.mkdir(exist_ok=True)
        
        filename = f"{session_id}_tracking_results"
        
        if format_type.lower() == "json":
            filepath = export_dir / f"{filename}.json"
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        
        elif format_type.lower() == "csv":
            filepath = export_dir / f"{filename}.csv"
            self._export_to_csv(results, filepath)
        
        elif format_type.lower() == "excel":
            filepath = export_dir / f"{filename}.xlsx"
            self._export_to_excel(results, filepath)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        return {
            "session_id": session_id,
            "export_format": format_type,
            "filepath": str(filepath),
            "file_size": filepath.stat().st_size,
            "message": f"Results exported to {format_type.upper()} successfully"
        }
    
    def _export_to_csv(self, results: Dict, filepath: Path):
        """Export results to CSV format"""
        import csv
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'frame_index', 'timestamp', 'instrument_id', 'instrument_type',
                'center_x', 'center_y', 'area', 'confidence', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h'
            ])
            
            # Write data
            for frame in results["tracking_results"]["frames"]:
                frame_idx = frame["frame_index"]
                timestamp = frame["timestamp"]
                
                for inst in frame["masks"]:
                    writer.writerow([
                        frame_idx, timestamp, inst["id"], inst["type"],
                        inst["center"][0], inst["center"][1], inst["area"], inst["confidence"],
                        inst["bbox"][0], inst["bbox"][1], inst["bbox"][2], inst["bbox"][3]
                    ])
    
    def _export_to_excel(self, results: Dict, filepath: Path):
        """Export results to Excel format"""
        try:
            import pandas as pd
            
            # Prepare data for Excel
            data = []
            for frame in results["tracking_results"]["frames"]:
                frame_idx = frame["frame_index"]
                timestamp = frame["timestamp"]
                
                for inst in frame["masks"]:
                    data.append({
                        'frame_index': frame_idx,
                        'timestamp': timestamp,
                        'instrument_id': inst["id"],
                        'instrument_type': inst["type"],
                        'center_x': inst["center"][0],
                        'center_y': inst["center"][1],
                        'area': inst["area"],
                        'confidence': inst["confidence"],
                        'bbox_x': inst["bbox"][0],
                        'bbox_y': inst["bbox"][1],
                        'bbox_w': inst["bbox"][2],
                        'bbox_h': inst["bbox"][3]
                    })
            
            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False)
            
        except ImportError:
            # Fallback to CSV if pandas not available
            self._export_to_csv(results, filepath.with_suffix('.csv'))
    
    def update_roi(
        self, 
        session_id: str, 
        roi_points: List[List[float]], 
        roi_type: str = "polygon"
    ) -> Dict:
        """
        Update ROI during tracking
        
        Args:
            session_id: Session identifier
            roi_points: New ROI points
            roi_type: ROI type
            
        Returns:
            Update confirmation
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        # Update ROI data
        result = self.set_roi(session_id, roi_points, roi_type)
        
        # If tracking was in progress, restart it
        session = self.active_sessions[session_id]
        if session["status"] in ["tracking_started", "tracking_completed"]:
            session["status"] = "roi_updated"
            result["message"] += " - Tracking will restart with new ROI"
        
        return result

# Export service instance
roi_tracking_service = ROITrackingService()