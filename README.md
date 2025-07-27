# 準リアルタイムチャート表示


技術スタック
- python 3.12
- newsAPI
- yfinaceライブラリ
- postgreSQLデータベース(ローカル)

```.env
NEWS_APIKEY={APIキー}

# Database Configuration
DATABASE_URL=postgresql://{user}:{password}@localhost:5432/stock_analyzer

# Optional: Database connection parameters (alternative to DATABASE_URL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME={postgreSQLデータベース名}
DB_USER={postgreSQLユーザー名}
DB_PASSWORD={postgreSQLパスワード}
```

## アプリ起動

```bash
$ uv sync
$ uv run web_app.py
```

