import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsAPIClient:
    def __init__(self):
        self.api_key = os.getenv('NEWS_APIKEY')
        if not self.api_key or self.api_key == 'your_news_api_key_here':
            logger.warning("NEWS_APIKEY が設定されていません。.envファイルを確認してください。")
        
        self.base_url = "https://newsapi.org/v2"
        self.cache = {}
    
    def get_stock_news(self, symbols: List[str], language: str = 'ja', page_size: int = 10) -> List[Dict]:
        """
        指定された銘柄のニュースを取得
        
        Args:
            symbols: 銘柄コードのリスト
            language: 言語設定（デフォルト: 'ja'）
            page_size: 取得する記事数（デフォルト: 10）
        
        Returns:
            List[Dict]: ニュース記事のリスト
        """
        if not self.api_key or self.api_key == 'your_news_api_key_here':
            return [{
                'title': 'NewsAPI キーが設定されていません',
                'description': '.env ファイルで NEWS_APIKEY を設定してください。',
                'publishedAt': datetime.now().isoformat(),
                'url': '',
                'symbol': 'ERROR'
            }]
        
        all_articles = []
        
        for symbol in symbols:
            try:
                # キャッシュキーを作成
                cache_key = f"{symbol}_{language}_{page_size}"
                
                # キャッシュをチェック（5分間有効）
                if cache_key in self.cache:
                    cache_time, cached_data = self.cache[cache_key]
                    if datetime.now() - cache_time < timedelta(minutes=5):
                        logger.info(f"キャッシュから {symbol} のニュースを取得")
                        all_articles.extend(cached_data)
                        continue
                
                # 検索クエリを構築（日本の銘柄コードと企業名を考慮）
                query = self._build_search_query(symbol)
                
                # APIリクエストを送信
                articles = self._fetch_news_from_api(query, language, page_size)
                
                # 記事に銘柄情報を追加
                for article in articles:
                    article['symbol'] = symbol
                    article['formatted_date'] = self._format_date(article.get('publishedAt', ''))
                
                # キャッシュに保存
                self.cache[cache_key] = (datetime.now(), articles)
                
                all_articles.extend(articles)
                logger.info(f"{symbol} のニュース {len(articles)} 件を取得")
                
            except Exception as e:
                logger.error(f"{symbol} のニュース取得エラー: {e}")
                # エラーの場合は空の記事を追加
                all_articles.append({
                    'title': f'{symbol} のニュース取得エラー',
                    'description': f'エラー: {str(e)}',
                    'publishedAt': datetime.now().isoformat(),
                    'formatted_date': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
                    'url': '',
                    'symbol': symbol
                })
        
        # 日付順でソート（新しい順）
        all_articles.sort(key=lambda x: x.get('publishedAt', ''), reverse=True)
        
        return all_articles
    
    def _build_search_query(self, symbol: str) -> str:
        """銘柄コードに基づいて検索クエリを構築"""
        # 日本の銘柄コード（例: 7203.T）の場合
        if '.T' in symbol:
            base_symbol = symbol.replace('.T', '')
            # 有名企業のマッピング
            company_map = {
                '7203': 'トヨタ自動車',
                '9984': 'ソフトバンクグループ',
                '6758': 'ソニーグループ',
                '8035': '東京エレクトロン',
                '4689': 'LINEヤフー',
                '6861': 'キーエンス',
                '9434': 'Softbank',
                '4502': '武田薬品工業',
                '8058': '三菱商事',
                '9432': 'NTT'
            }
            
            if base_symbol in company_map:
                return f'"{company_map[base_symbol]}" OR "{symbol}" OR "{base_symbol}"'
            else:
                return f'"{symbol}" OR "{base_symbol}" OR "銘柄コード {base_symbol}"'
        
        # 米国株などの場合
        else:
            # 有名企業のマッピング
            company_map = {
                'AAPL': 'Apple',
                'GOOGL': 'Google',
                'MSFT': 'Microsoft',
                'AMZN': 'Amazon',
                'TSLA': 'Tesla',
                'META': 'Meta',
                'NFLX': 'Netflix',
                'NVDA': 'NVIDIA'
            }
            
            if symbol in company_map:
                return f'"{company_map[symbol]}" OR "{symbol}"'
            else:
                return f'"{symbol}"'
    
    def _fetch_news_from_api(self, query: str, language: str, page_size: int) -> List[Dict]:
        """NewsAPIからニュースを取得"""
        url = f"{self.base_url}/everything"
        
        params = {
            'q': query,
            'language': language,
            'sortBy': 'publishedAt',
            'pageSize': min(page_size, 20),  # APIの制限
            'apiKey': self.api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'ok':
            return data.get('articles', [])
        else:
            logger.error(f"NewsAPI エラー: {data.get('message', 'Unknown error')}")
            return []
    
    def _format_date(self, date_string: str) -> str:
        """日付文字列を日本語形式にフォーマット"""
        try:
            if not date_string:
                return datetime.now().strftime('%Y年%m月%d日 %H:%M')
            
            # ISO形式の日付をパース
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            
            # 日本時間に変換（簡易版 - 9時間を加算）
            dt_jst = dt + timedelta(hours=9)
            
            return dt_jst.strftime('%Y年%m月%d日 %H:%M')
        
        except Exception as e:
            logger.error(f"日付フォーマットエラー: {e}")
            return datetime.now().strftime('%Y年%m月%d日 %H:%M')
    
    def get_news_for_symbol(self, symbol: str, language: str = 'ja', page_size: int = 5) -> List[Dict]:
        """単一銘柄のニュースを取得"""
        return self.get_stock_news([symbol], language, page_size)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache.clear()
        logger.info("ニュースキャッシュをクリアしました")


class NewsManager:
    def __init__(self):
        self.news_client = NewsAPIClient()
    
    def get_favorites_news(self, favorite_symbols: List[str], page_size: int = 5) -> Dict[str, any]:
        """
        お気に入り銘柄のニュースを取得
        
        Args:
            favorite_symbols: お気に入り銘柄のリスト
            page_size: 銘柄あたりの記事数
        
        Returns:
            Dict: ニュース取得結果
        """
        if not favorite_symbols:
            return {
                'success': False,
                'message': 'お気に入り銘柄が登録されていません',
                'articles': []
            }
        
        try:
            articles = self.news_client.get_stock_news(favorite_symbols, page_size=page_size)
            
            return {
                'success': True,
                'message': f'{len(favorite_symbols)} 銘柄のニュース {len(articles)} 件を取得しました',
                'articles': articles,
                'symbols': favorite_symbols
            }
        
        except Exception as e:
            logger.error(f"ニュース取得エラー: {e}")
            return {
                'success': False,
                'message': f'ニュース取得に失敗しました: {str(e)}',
                'articles': []
            }
    
    def format_news_for_display(self, articles: List[Dict]) -> str:
        """ニュース記事を表示用にフォーマット"""
        if not articles:
            return "ニュース記事がありません。"
        
        formatted_news = []
        
        for i, article in enumerate(articles[:20], 1):  # 最大20件
            title = article.get('title', 'タイトルなし')
            description = article.get('description', '')
            date = article.get('formatted_date', '')
            symbol = article.get('symbol', '')
            url = article.get('url', '')
            
            # 説明文を短縮
            if description and len(description) > 100:
                description = description[:97] + '...'
            
            news_item = f"""
**{i}. [{symbol}] {title}**
📅 {date}
📰 {description}
🔗 [記事を読む]({url})
---"""
            
            formatted_news.append(news_item)
        
        return '\n'.join(formatted_news)