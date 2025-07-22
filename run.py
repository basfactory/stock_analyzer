#!/usr/bin/env python3
"""
株価チャート表示アプリケーション実行スクリプト
Windows 11 + WSL環境対応
"""

import os
import sys
import webbrowser
import time

def main():
    """メイン実行関数"""
    print("株価チャート表示アプリケーションを起動中...")
    print("WSL環境でのtkinter問題を回避するため、Webアプリ版を起動します。")
    
    try:
        # Webアプリケーションを実行
        from web_app import main as web_app_main
        
        # ブラウザを自動起動（WSL環境対応）
        def open_browser():
            time.sleep(2)  # サーバー起動を待つ
            if os.environ.get('WSL_DISTRO_NAME'):
                # WSL環境では Windows のデフォルトブラウザを使用
                os.system('cmd.exe /c start http://127.0.0.1:8050')
            else:
                webbrowser.open('http://127.0.0.1:8050')
        
        import threading
        threading.Timer(1.0, open_browser).start()
        
        web_app_main()
        
    except ImportError as e:
        print(f"インポートエラー: {e}")
        print("必要な依存関係がインストールされているか確認してください。")
        print("実行コマンド: uv sync")
        sys.exit(1)
    except Exception as e:
        print(f"アプリケーション実行エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()