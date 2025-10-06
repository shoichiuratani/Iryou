#!/usr/bin/env python3
"""
System Test Script for Surgi-Motion Visualizer
統合テストスクリプト
"""

import requests
import time
import json
import sys
from pathlib import Path
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# テスト設定
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class SystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        self.test_results = []

    def log_test(self, test_name, success, message=""):
        """テスト結果を記録"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })

    def test_backend_health(self):
        """バックエンドヘルスチェック"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Backend Health Check", True, f"Version: {data.get('version', 'unknown')}")
                return True
            else:
                self.log_test("Backend Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", False, str(e))
            return False

    def test_frontend_accessibility(self):
        """フロントエンドアクセシビリティテスト"""
        try:
            response = self.session.get(FRONTEND_URL)
            if response.status_code == 200:
                # HTMLにアプリケーション要素が含まれているかチェック
                content = response.text
                if "Surgi-Motion Visualizer" in content:
                    self.log_test("Frontend Accessibility", True, "Frontend is accessible")
                    return True
                else:
                    self.log_test("Frontend Accessibility", False, "HTML content incorrect")
                    return False
            else:
                self.log_test("Frontend Accessibility", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", False, str(e))
            return False

    def create_test_video_file(self):
        """テスト用のダミー動画ファイルを作成"""
        try:
            # 簡易的なダミーファイル作成（実際の動画ではないが、アップロードテスト用）
            test_file_path = Path("test_video.mp4")
            
            # ダミーデータでファイル作成（実際のMP4ヘッダーを含む）
            mp4_header = bytes([
                0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,  # ftyp box
                0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00,
                0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x32,
                0x61, 0x76, 0x63, 0x31, 0x6D, 0x70, 0x34, 0x31
            ])
            
            # ダミーデータを追加（1MB程度）
            dummy_data = b"DUMMY_VIDEO_DATA" * 65536  # 1MB程度
            
            with open(test_file_path, 'wb') as f:
                f.write(mp4_header + dummy_data)
            
            self.log_test("Test Video File Creation", True, f"Created {test_file_path}")
            return test_file_path
            
        except Exception as e:
            self.log_test("Test Video File Creation", False, str(e))
            return None

    def test_video_upload(self):
        """動画アップロードテスト"""
        test_file = self.create_test_video_file()
        if not test_file:
            return False

        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('test_video.mp4', f, 'video/mp4')}
                response = self.session.post(f"{BASE_URL}/api/upload", files=files)
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('session_id')
                self.log_test("Video Upload", True, f"Session ID: {self.session_id}")
                return True
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                self.log_test("Video Upload", False, error_msg)
                return False
        except Exception as e:
            self.log_test("Video Upload", False, str(e))
            return False
        finally:
            # テストファイルを削除
            if test_file and test_file.exists():
                test_file.unlink()

    def test_roi_selection(self):
        """ROI選択テスト"""
        if not self.session_id:
            self.log_test("ROI Selection", False, "No session ID available")
            return False

        try:
            roi_data = {
                "frame_number": 0,
                "click_position": {
                    "x": 320.0,
                    "y": 240.0,
                    "z": 0.0
                },
                "selection_type": "instrument",
                "label": "test_instrument"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/roi_selection/{self.session_id}",
                json=roi_data
            )
            
            if response.status_code == 200:
                self.log_test("ROI Selection", True, "ROI selected successfully")
                return True
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                self.log_test("ROI Selection", False, error_msg)
                return False
        except Exception as e:
            self.log_test("ROI Selection", False, str(e))
            return False

    def test_analysis_start(self):
        """解析開始テスト"""
        if not self.session_id:
            self.log_test("Analysis Start", False, "No session ID available")
            return False

        try:
            response = self.session.post(f"{BASE_URL}/api/analyze/{self.session_id}")
            
            if response.status_code == 200:
                self.log_test("Analysis Start", True, "Analysis started successfully")
                return True
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                self.log_test("Analysis Start", False, error_msg)
                return False
        except Exception as e:
            self.log_test("Analysis Start", False, str(e))
            return False

    def test_status_check(self):
        """ステータス確認テスト"""
        if not self.session_id:
            self.log_test("Status Check", False, "No session ID available")
            return False

        try:
            response = self.session.get(f"{BASE_URL}/api/status/{self.session_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', 0)
                self.log_test("Status Check", True, f"Status: {status}, Progress: {progress:.1%}")
                return True
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                self.log_test("Status Check", False, error_msg)
                return False
        except Exception as e:
            self.log_test("Status Check", False, str(e))
            return False

    def test_api_documentation(self):
        """API文書アクセステスト"""
        try:
            # Swagger UI
            response = self.session.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                self.log_test("API Documentation (Swagger)", True, "Swagger UI accessible")
            else:
                self.log_test("API Documentation (Swagger)", False, f"HTTP {response.status_code}")

            # ReDoc
            response = self.session.get(f"{BASE_URL}/redoc")
            if response.status_code == 200:
                self.log_test("API Documentation (ReDoc)", True, "ReDoc accessible")
                return True
            else:
                self.log_test("API Documentation (ReDoc)", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Documentation", False, str(e))
            return False

    def run_comprehensive_test(self):
        """包括的なシステムテスト実行"""
        logger.info("🧪 Starting comprehensive system test...")
        logger.info("=" * 60)

        # 基本テスト
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("API Documentation", self.test_api_documentation),
            ("Video Upload", self.test_video_upload),
            ("ROI Selection", self.test_roi_selection),
            ("Analysis Start", self.test_analysis_start),
            ("Status Check", self.test_status_check),
        ]

        success_count = 0
        for test_name, test_func in tests:
            logger.info(f"\n🔬 Running test: {test_name}")
            try:
                if test_func():
                    success_count += 1
                time.sleep(0.5)  # テスト間の待機
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")

        # 結果サマリー
        total_tests = len(tests)
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {success_count}")
        logger.info(f"Failed: {total_tests - success_count}")
        logger.info(f"Success Rate: {success_count/total_tests:.1%}")

        # 詳細結果
        logger.info("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            logger.info(f"{status} {result['test']}: {result['message']}")

        return success_count == total_tests

    def generate_test_report(self):
        """テストレポートの生成"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for r in self.test_results if r["success"]),
            "failed_tests": sum(1 for r in self.test_results if not r["success"]),
            "results": self.test_results
        }

        report_file = f"test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Test report saved to: {report_file}")
        return report_file


def main():
    """メイン実行"""
    logger.info("🏥 Surgi-Motion Visualizer System Test")
    logger.info("=" * 60)

    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        logger.info("⏳ Waiting for services to start...")
        time.sleep(10)

    tester = SystemTester()
    
    try:
        success = tester.run_comprehensive_test()
        report_file = tester.generate_test_report()
        
        if success:
            logger.info("\n🎉 All tests passed! System is working correctly.")
            sys.exit(0)
        else:
            logger.warning("\n⚠️ Some tests failed. Please check the logs.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Test interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"\n💥 Test execution failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()