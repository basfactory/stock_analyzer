import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """PostgreSQLデータベースに接続"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(database_url)
            else:
                self.connection = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', '5432'),
                    database=os.getenv('DB_NAME', 'stock_analyzer'),
                    user=os.getenv('DB_USER', 'user'),
                    password=os.getenv('DB_PASSWORD', 'password')
                )
            logger.info("データベース接続が成功しました")
        except Exception as e:
            logger.error(f"データベース接続エラー: {e}")
            self.connection = None
    
    def create_tables(self):
        """必要なテーブルを作成"""
        if not self.connection:
            logger.error("データベース接続がありません")
            return
        
        try:
            cursor = self.connection.cursor()
            
            # お気に入り銘柄テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS favorite_stocks (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL UNIQUE,
                    company_name VARCHAR(100),
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            cursor.close()
            logger.info("テーブル作成が完了しました")
            
        except Exception as e:
            logger.error(f"テーブル作成エラー: {e}")
            if self.connection:
                self.connection.rollback()
    
    def add_favorite_stock(self, symbol: str, company_name: str = None) -> bool:
        """お気に入り銘柄を追加"""
        if not self.connection:
            logger.error("データベース接続がありません")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # 現在の銘柄数をチェック
            cursor.execute("SELECT COUNT(*) FROM favorite_stocks")
            count = cursor.fetchone()[0]
            
            if count >= 10:
                logger.warning("お気に入り銘柄は最大10個までです")
                cursor.close()
                return False
            
            # 重複チェック
            cursor.execute("SELECT symbol FROM favorite_stocks WHERE symbol = %s", (symbol,))
            if cursor.fetchone():
                logger.warning(f"銘柄 {symbol} は既にお気に入りに登録されています")
                cursor.close()
                return False
            
            # 銘柄を追加
            cursor.execute(
                "INSERT INTO favorite_stocks (symbol, company_name) VALUES (%s, %s)",
                (symbol.upper(), company_name)
            )
            
            self.connection.commit()
            cursor.close()
            logger.info(f"お気に入り銘柄 {symbol} を追加しました")
            return True
            
        except (psycopg2.Error, psycopg2.IntegrityError) as e:
            logger.error(f"お気に入り銘柄追加エラー: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        except Exception as e:
            logger.error(f"予期しないエラー (お気に入り銘柄追加): {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def remove_favorite_stock(self, symbol: str) -> bool:
        """お気に入り銘柄を削除"""
        if not self.connection:
            logger.error("データベース接続がありません")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("DELETE FROM favorite_stocks WHERE symbol = %s", (symbol.upper(),))
            
            if cursor.rowcount > 0:
                self.connection.commit()
                logger.info(f"お気に入り銘柄 {symbol} を削除しました")
                result = True
            else:
                logger.warning(f"銘柄 {symbol} はお気に入りに登録されていません")
                result = False
            
            cursor.close()
            return result
            
        except psycopg2.Error as e:
            logger.error(f"お気に入り銘柄削除エラー: {e}")
            if self.connection:
                self.connection.rollback()
            return False
        except Exception as e:
            logger.error(f"予期しないエラー (お気に入り銘柄削除): {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_favorite_stocks(self) -> List[Dict[str, any]]:
        """お気に入り銘柄一覧を取得"""
        if not self.connection:
            logger.error("データベース接続がありません")
            return []
        
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT symbol, company_name, added_date 
                FROM favorite_stocks 
                ORDER BY added_date ASC
            """)
            
            favorites = cursor.fetchall()
            cursor.close()
            
            return [dict(row) for row in favorites]
            
        except psycopg2.Error as e:
            logger.error(f"お気に入り銘柄取得エラー: {e}")
            return []
        except Exception as e:
            logger.error(f"予期しないエラー (お気に入り銘柄取得): {e}")
            return []
    
    def get_favorite_symbols(self) -> List[str]:
        """お気に入り銘柄のシンボル一覧を取得"""
        favorites = self.get_favorite_stocks()
        return [fav['symbol'] for fav in favorites]
    
    def is_favorite(self, symbol: str) -> bool:
        """指定された銘柄がお気に入りに登録されているかチェック"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM favorite_stocks WHERE symbol = %s", (symbol.upper(),))
            result = cursor.fetchone() is not None
            cursor.close()
            return result
            
        except psycopg2.Error as e:
            logger.error(f"お気に入りチェックエラー: {e}")
            return False
        except Exception as e:
            logger.error(f"予期しないエラー (お気に入りチェック): {e}")
            return False
    
    def get_favorites_count(self) -> int:
        """お気に入り銘柄の数を取得"""
        if not self.connection:
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM favorite_stocks")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
            
        except psycopg2.Error as e:
            logger.error(f"お気に入り数取得エラー: {e}")
            return 0
        except Exception as e:
            logger.error(f"予期しないエラー (お気に入り数取得): {e}")
            return 0
    
    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("データベース接続を閉じました")
    
    def __del__(self):
        """デストラクタでデータベース接続を閉じる"""
        self.close()


class FavoriteStockManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def add_favorite(self, symbol: str, company_name: str = None) -> Dict[str, any]:
        """お気に入り銘柄を追加（結果をDict形式で返す）"""
        if self.db.get_favorites_count() >= 10:
            return {
                'success': False,
                'message': 'お気に入り銘柄は最大10個までです'
            }
        
        if self.db.is_favorite(symbol):
            return {
                'success': False,
                'message': f'銘柄 {symbol} は既にお気に入りに登録されています'
            }
        
        success = self.db.add_favorite_stock(symbol, company_name)
        return {
            'success': success,
            'message': f'銘柄 {symbol} をお気に入りに追加しました' if success else f'銘柄 {symbol} の追加に失敗しました'
        }
    
    def remove_favorite(self, symbol: str) -> Dict[str, any]:
        """お気に入り銘柄を削除（結果をDict形式で返す）"""
        success = self.db.remove_favorite_stock(symbol)
        return {
            'success': success,
            'message': f'銘柄 {symbol} をお気に入りから削除しました' if success else f'銘柄 {symbol} の削除に失敗しました'
        }
    
    def get_favorites(self) -> List[Dict[str, any]]:
        """お気に入り銘柄一覧を取得"""
        return self.db.get_favorite_stocks()
    
    def get_symbols(self) -> List[str]:
        """お気に入り銘柄のシンボル一覧を取得"""
        return self.db.get_favorite_symbols()