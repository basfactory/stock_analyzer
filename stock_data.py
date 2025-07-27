import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import FavoriteStockManager
from news_api import NewsManager


class StockDataManager:
    def __init__(self):
        self.cache = {}
        self.favorites_manager = FavoriteStockManager()
        self.news_manager = NewsManager()
    
    def get_stock_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        株価データを取得する
        
        Args:
            symbol: 株価コード (例: "AAPL", "7203.T")
            period: 期間 ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        
        Returns:
            pandas.DataFrame: 株価データ
        """
        try:
            cache_key = f"{symbol}_{period}"
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                return None
            
            self.cache[cache_key] = data
            return data
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None
    
    def get_stock_data_range(self, symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        指定期間の株価データを取得する
        
        Args:
            symbol: 株価コード
            start_date: 開始日 ("YYYY-MM-DD")
            end_date: 終了日 ("YYYY-MM-DD")
        
        Returns:
            pandas.DataFrame: 株価データ
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                return None
                
            return data
            
        except Exception as e:
            print(f"Error fetching data for {symbol} ({start_date} to {end_date}): {e}")
            return None
    
    def get_company_info(self, symbol: str) -> Dict:
        """
        会社情報を取得する
        
        Args:
            symbol: 株価コード
        
        Returns:
            Dict: 会社情報
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'shortName': info.get('shortName', symbol),
                'longName': info.get('longName', symbol),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'Unknown')
            }
        except Exception as e:
            print(f"Error fetching info for {symbol}: {e}")
            return {'shortName': symbol, 'longName': symbol, 'currency': 'USD', 'exchange': 'Unknown'}
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        株価コードの有効性を検証する
        
        Args:
            symbol: 株価コード
        
        Returns:
            bool: 有効な場合True
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            return not data.empty
        except:
            return False
    
    def calculate_moving_average(self, data: pd.DataFrame, window: int = 20) -> pd.Series:
        """
        移動平均線を計算する
        
        Args:
            data: 株価データ
            window: 移動平均の期間（デフォルト: 20日）
        
        Returns:
            pd.Series: 移動平均データ
        """
        return data['Close'].rolling(window=window).mean()
    
    def calculate_bollinger_bands(self, data: pd.DataFrame, window: int = 20, std_dev: int = 2) -> Dict:
        """
        ボリンジャーバンドを計算する
        
        Args:
            data: 株価データ
            window: 移動平均の期間（デフォルト: 20日）
            std_dev: 標準偏差の倍数（デフォルト: 2）
        
        Returns:
            Dict: ボリンジャーバンドデータ（upper, lower, middle）
        """
        sma = data['Close'].rolling(window=window).mean()
        std = data['Close'].rolling(window=window).std()
        
        return {
            'upper': sma + (std * std_dev),
            'lower': sma - (std * std_dev),
            'middle': sma
        }
    
    def add_favorite_stock(self, symbol: str) -> Dict[str, any]:
        """お気に入り銘柄を追加"""
        # 銘柄の有効性をチェック
        if not self.validate_symbol(symbol):
            return {
                'success': False,
                'message': f'銘柄コード "{symbol}" は無効です'
            }
        
        # 会社名を取得
        company_info = self.get_company_info(symbol)
        company_name = company_info.get('shortName', symbol)
        
        # お気に入りに追加
        return self.favorites_manager.add_favorite(symbol, company_name)
    
    def remove_favorite_stock(self, symbol: str) -> Dict[str, any]:
        """お気に入り銘柄を削除"""
        return self.favorites_manager.remove_favorite(symbol)
    
    def get_favorite_stocks(self) -> List[Dict[str, any]]:
        """お気に入り銘柄一覧を取得"""
        return self.favorites_manager.get_favorites()
    
    def get_favorite_symbols(self) -> List[str]:
        """お気に入り銘柄のシンボル一覧を取得"""
        return self.favorites_manager.get_symbols()
    
    def get_favorites_news(self, page_size: int = 5) -> Dict[str, any]:
        """お気に入り銘柄のニュースを取得"""
        favorite_symbols = self.get_favorite_symbols()
        return self.news_manager.get_favorites_news(favorite_symbols, page_size)
    
    def format_news_for_display(self, articles: List[Dict]) -> str:
        """ニュース記事を表示用にフォーマット"""
        return self.news_manager.format_news_for_display(articles)