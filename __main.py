import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta
from stock_data import StockDataManager


class StockChartGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("株価チャート表示アプリ")
        self.root.geometry("1200x800")
        
        # データマネージャーの初期化
        self.stock_manager = StockDataManager()
        
        # 株式データの保存用
        self.stock_data = {}
        
        # GUIコンポーネントの初期化
        self.setup_gui()
        
        # デフォルトの色設定
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    def setup_gui(self):
        """GUIコンポーネントをセットアップ"""
        # メインフレーム
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側のコントロールパネル
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 銘柄入力セクション
        self.setup_stock_inputs(control_frame)
        
        # 期間選択セクション
        self.setup_period_selection(control_frame)
        
        # 実行ボタン
        self.setup_action_buttons(control_frame)
        
        # 右側のグラフ表示エリア
        self.setup_chart_area(main_frame)
    
    def setup_stock_inputs(self, parent):
        """株式入力フィールドをセットアップ"""
        # 銘柄入力フレーム
        stock_frame = ttk.LabelFrame(parent, text="銘柄入力（最大4社）", padding="10")
        stock_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stock_entries = []
        self.stock_labels = []
        
        for i in range(4):
            # ラベル
            label = ttk.Label(stock_frame, text=f"銘柄 {i+1}:")
            label.grid(row=i, column=0, sticky=tk.W, pady=2)
            
            # 入力フィールド
            entry = ttk.Entry(stock_frame, width=15)
            entry.grid(row=i, column=1, padx=(5, 0), pady=2)
            
            self.stock_entries.append(entry)
            self.stock_labels.append(label)
        
        # サンプル入力例
        self.stock_entries[0].insert(0, "AAPL")
        self.stock_entries[1].insert(0, "GOOGL")
    
    def setup_period_selection(self, parent):
        """期間選択をセットアップ"""
        period_frame = ttk.LabelFrame(parent, text="表示期間", padding="10")
        period_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 期間選択のラジオボタン
        self.period_var = tk.StringVar(value="1y")
        
        periods = [
            ("1日", "1d"),
            ("5日", "5d"),
            ("1ヶ月", "1mo"),
            ("3ヶ月", "3mo"),
            ("6ヶ月", "6mo"),
            ("1年", "1y"),
            ("2年", "2y"),
            ("5年", "5y")
        ]
        
        for i, (text, value) in enumerate(periods):
            rb = ttk.Radiobutton(period_frame, text=text, variable=self.period_var, value=value)
            rb.grid(row=i//2, column=i%2, sticky=tk.W, pady=1)
    
    def setup_action_buttons(self, parent):
        """アクションボタンをセットアップ"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # グラフ更新ボタン
        update_btn = ttk.Button(button_frame, text="グラフ更新", command=self.update_chart)
        update_btn.pack(fill=tk.X, pady=2)
        
        # クリアボタン
        clear_btn = ttk.Button(button_frame, text="クリア", command=self.clear_chart)
        clear_btn.pack(fill=tk.X, pady=2)
    
    def setup_chart_area(self, parent):
        """チャート表示エリアをセットアップ"""
        # グラフフレーム
        chart_frame = ttk.Frame(parent)
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # matplotlib figureの作成
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # キャンバスの作成
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 初期グラフの設定
        self.ax.set_title("株価チャート")
        self.ax.set_xlabel("日付")
        self.ax.set_ylabel("株価")
        self.ax.grid(True, alpha=0.3)
    
    def get_valid_symbols(self):
        """入力された有効な銘柄コードを取得"""
        symbols = []
        for entry in self.stock_entries:
            symbol = entry.get().strip().upper()
            if symbol:
                symbols.append(symbol)
        return symbols
    
    def update_chart(self):
        """チャートを更新"""
        symbols = self.get_valid_symbols()
        
        if not symbols:
            messagebox.showwarning("警告", "少なくとも1つの銘柄コードを入力してください。")
            return
        
        period = self.period_var.get()
        
        # グラフをクリア
        self.ax.clear()
        self.ax.set_title("株価チャート")
        self.ax.set_xlabel("日付")
        self.ax.set_ylabel("株価")
        self.ax.grid(True, alpha=0.3)
        
        # データを取得してプロット
        valid_data_count = 0
        for i, symbol in enumerate(symbols):
            try:
                # データ取得
                data = self.stock_manager.get_stock_data(symbol, period)
                
                if data is not None and not data.empty:
                    # 会社情報を取得
                    company_info = self.stock_manager.get_company_info(symbol)
                    company_name = company_info.get('shortName', symbol)
                    
                    # グラフにプロット
                    color = self.colors[i % len(self.colors)]
                    self.ax.plot(data.index, data['Close'], 
                               label=f"{company_name} ({symbol})", 
                               color=color, 
                               linewidth=2)
                    
                    valid_data_count += 1
                    
                else:
                    messagebox.showwarning("警告", f"銘柄コード '{symbol}' のデータを取得できませんでした。")
                    
            except Exception as e:
                messagebox.showerror("エラー", f"銘柄 '{symbol}' の処理中にエラーが発生しました: {str(e)}")
        
        if valid_data_count > 0:
            # 凡例を表示
            self.ax.legend(loc='upper left')
            
            # 日付軸の回転
            self.figure.autofmt_xdate()
            
            # グラフを更新
            self.canvas.draw()
        else:
            messagebox.showerror("エラー", "有効なデータを取得できませんでした。")
    
    def clear_chart(self):
        """チャートをクリア"""
        # 入力フィールドをクリア
        for entry in self.stock_entries:
            entry.delete(0, tk.END)
        
        # グラフをクリア
        self.ax.clear()
        self.ax.set_title("株価チャート")
        self.ax.set_xlabel("日付")
        self.ax.set_ylabel("株価")
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # データキャッシュもクリア
        self.stock_data.clear()


def main():
    # WSL環境でのGUI表示設定
    import os
    if os.environ.get('WSL_DISTRO_NAME'):
        import matplotlib
        matplotlib.use('TkAgg')
    
    root = tk.Tk()
    app = StockChartGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()