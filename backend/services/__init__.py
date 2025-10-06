#!/usr/bin/env python3
"""
Services package for Surgi-Motion Visualizer Backend
手術手技分析システム バックエンドサービスパッケージ
"""

__version__ = "2.0.0"
__author__ = "Surgi-Motion Development Team"

# Import main services
try:
    from .sam2_service import sam2_service
    from .roi_tracking_service import roi_tracking_service
    
    __all__ = [
        "sam2_service",
        "roi_tracking_service"
    ]
    
except ImportError as e:
    print(f"Warning: Failed to import some services: {e}")
    __all__ = []