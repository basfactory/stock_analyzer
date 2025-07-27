import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime, timedelta
from stock_data import StockDataManager


class StockChartWebApp:
    def __init__(self):
        self.app = dash.Dash(__name__)
        self.stock_manager = StockDataManager()
        self.setup_layout()
        self.setup_callbacks()
        
        # デフォルトの色設定
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    def setup_layout(self):
        """Webアプリのレイアウトを設定"""
        self.app.layout = html.Div([
            html.H1("株価チャート表示アプリ", style={'text-align': 'center', 'margin-bottom': '30px'}),
            
            html.Div([
                # 左側のコントロールパネル
                html.Div([
                    # お気に入り銘柄管理セクション
                    html.Div([
                        html.H3("⭐ お気に入り銘柄"),
                        html.Div([
                            dcc.Input(
                                id='favorite-input',
                                type='text',
                                placeholder='銘柄コード (例: AAPL, 7203.T)',
                                style={'width': '150px', 'margin-right': '5px'}
                            ),
                            html.Button(
                                '追加', 
                                id='add-favorite-button', 
                                n_clicks=0,
                                style={
                                    'background-color': '#28a745',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '5px 10px',
                                    'border-radius': '3px',
                                    'cursor': 'pointer'
                                }
                            )
                        ], style={'margin-bottom': '10px'}),
                        
                        html.Div(id='favorites-list', style={
                            'max-height': '150px',
                            'overflow-y': 'auto',
                            'border': '1px solid #ddd',
                            'border-radius': '5px',
                            'padding': '10px',
                            'background-color': '#f9f9f9'
                        }),
                        
                        html.Div(id='favorites-status', style={
                            'margin-top': '10px',
                            'font-size': '12px',
                            'color': '#666'
                        })
                    ], style={'margin-bottom': '30px'}),
                    # 銘柄入力セクション
                    html.Div([
                        html.H3("銘柄入力（最大4社）"),
                        *[html.Div([
                            html.Label(f"銘柄 {i+1}:", style={'display': 'block', 'margin-bottom': '5px'}),
                            dcc.Input(
                                id=f'stock-input-{i}',
                                type='text',
                                placeholder='例: AAPL, 7203.T',
                                style={'width': '200px', 'margin-bottom': '10px'}
                            )
                        ]) for i in range(4)]
                    ], style={'margin-bottom': '30px'}),
                    
                    # 期間選択セクション
                    html.Div([
                        html.H3("表示期間"),
                        dcc.RadioItems(
                            id='period-selector',
                            options=[
                                {'label': '1日', 'value': '1d'},
                                {'label': '5日', 'value': '5d'},
                                {'label': '1ヶ月', 'value': '1mo'},
                                {'label': '3ヶ月', 'value': '3mo'},
                                {'label': '6ヶ月', 'value': '6mo'},
                                {'label': '1年', 'value': '1y'},
                                {'label': '2年', 'value': '2y'},
                                {'label': '5年', 'value': '5y'}
                            ],
                            value='1y',
                            labelStyle={'display': 'block', 'margin-bottom': '5px'}
                        )
                    ], style={'margin-bottom': '30px'}),
                    
                    # テクニカル指標セクション
                    html.Div([
                        html.H3("📊 テクニカル指標"),
                        
                        # 移動平均線
                        html.Div([
                            dcc.Checklist(
                                id='ma-checkbox',
                                options=[{'label': ' 移動平均線', 'value': 'show'}],
                                value=[],
                                style={'margin-bottom': '10px'}
                            ),
                            html.Div([
                                html.Label("期間: ", style={'margin-right': '5px'}),
                                dcc.Input(
                                    id='ma-period',
                                    type='number',
                                    value=20,
                                    min=1,
                                    max=100,
                                    style={'width': '60px', 'margin-right': '5px'}
                                ),
                                html.Label("日", style={'margin-right': '10px'})
                            ], style={'margin-left': '20px', 'margin-bottom': '15px'})
                        ]),
                        
                        # ボリンジャーバンド
                        html.Div([
                            dcc.Checklist(
                                id='bb-checkbox',
                                options=[{'label': ' ボリンジャーバンド', 'value': 'show'}],
                                value=[],
                                style={'margin-bottom': '10px'}
                            ),
                            html.Div([
                                html.Label("期間: ", style={'margin-right': '5px'}),
                                dcc.Input(
                                    id='bb-period',
                                    type='number',
                                    value=20,
                                    min=1,
                                    max=100,
                                    style={'width': '60px', 'margin-right': '5px'}
                                ),
                                html.Label("日", style={'margin-right': '10px'}),
                                html.Label("σ: ", style={'margin-right': '5px'}),
                                dcc.Input(
                                    id='bb-std',
                                    type='number',
                                    value=2,
                                    min=1,
                                    max=3,
                                    step=0.1,
                                    style={'width': '60px', 'margin-right': '5px'}
                                )
                            ], style={'margin-left': '20px', 'margin-bottom': '15px'})
                        ])
                        
                    ], style={'margin-bottom': '30px'}),
                    
                    # アクションボタン
                    html.Div([
                        html.Button(
                            'グラフ更新', 
                            id='update-button', 
                            n_clicks=0,
                            style={
                                'background-color': '#007bff',
                                'color': 'white',
                                'border': 'none',
                                'padding': '10px 20px',
                                'border-radius': '5px',
                                'cursor': 'pointer',
                                'margin-right': '10px'
                            }
                        ),
                        html.Button(
                            'クリア', 
                            id='clear-button', 
                            n_clicks=0,
                            style={
                                'background-color': '#6c757d',
                                'color': 'white',
                                'border': 'none',
                                'padding': '10px 20px',
                                'border-radius': '5px',
                                'cursor': 'pointer'
                            }
                        )
                    ]),
                    
                    # ニュース取得セクション
                    html.Div([
                        html.H3("📰 ニュース取得"),
                        html.Div([
                            html.Button(
                                'お気に入り銘柄のニュースを取得', 
                                id='get-news-button', 
                                n_clicks=0,
                                style={
                                    'background-color': '#17a2b8',
                                    'color': 'white',
                                    'border': 'none',
                                    'padding': '10px 15px',
                                    'border-radius': '5px',
                                    'cursor': 'pointer',
                                    'width': '100%'
                                }
                            )
                        ], style={'margin-bottom': '10px'}),
                        
                        html.Div(id='news-status', style={
                            'font-size': '12px',
                            'color': '#666',
                            'margin-bottom': '10px'
                        })
                    ], style={'margin-bottom': '20px'})
                    
                ], style={
                    'width': '25%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '20px',
                    'background-color': '#f8f9fa',
                    'border-radius': '10px',
                    'margin-right': '20px'
                }),
                
                # 右側のグラフ・ニュース表示エリア
                html.Div([
                    # グラフエリア
                    html.Div([
                        dcc.Graph(
                            id='stock-chart',
                            style={'height': '400px'}
                        ),
                        html.Div(id='status-message', style={'margin-top': '10px'})
                    ], style={'margin-bottom': '20px'}),
                    
                    # ニュース表示エリア
                    html.Div([
                        html.H3("📰 最新ニュース", style={'margin-bottom': '15px'}),
                        html.Div(
                            id='news-display',
                            style={
                                'height': '300px',
                                'overflow-y': 'auto',
                                'border': '1px solid #ddd',
                                'border-radius': '5px',
                                'padding': '15px',
                                'background-color': '#f8f9fa'
                            },
                            children="お気に入り銘柄を追加して「ニュース取得」ボタンをクリックしてください。"
                        )
                    ])
                ], style={
                    'width': '70%',
                    'display': 'inline-block',
                    'vertical-align': 'top'
                })
                
            ], style={'margin': '20px'})
        ])
    
    def setup_callbacks(self):
        """コールバック関数を設定"""
        
        @callback(
            [Output('stock-chart', 'figure'),
             Output('status-message', 'children')],
            [Input('update-button', 'n_clicks')],
            [State('stock-input-0', 'value'),
             State('stock-input-1', 'value'),
             State('stock-input-2', 'value'),
             State('stock-input-3', 'value'),
             State('period-selector', 'value'),
             State('ma-checkbox', 'value'),
             State('ma-period', 'value'),
             State('bb-checkbox', 'value'),
             State('bb-period', 'value'),
             State('bb-std', 'value')]
        )
        def update_chart(n_clicks, stock1, stock2, stock3, stock4, period, ma_enabled, ma_period, bb_enabled, bb_period, bb_std):
            if n_clicks == 0:
                # 初期表示
                fig = go.Figure()
                fig.update_layout(
                    title="株価チャート",
                    xaxis_title="日付",
                    yaxis_title="株価",
                    template="plotly_white"
                )
                return fig, "銘柄を入力して「グラフ更新」をクリックしてください。"
            
            # 入力された銘柄を収集
            symbols = []
            for stock in [stock1, stock2, stock3, stock4]:
                if stock and stock.strip():
                    symbols.append(stock.strip().upper())
            
            if not symbols:
                fig = go.Figure()
                fig.update_layout(
                    title="株価チャート",
                    xaxis_title="日付",
                    yaxis_title="株価",
                    template="plotly_white"
                )
                return fig, "少なくとも1つの銘柄コードを入力してください。"
            
            # グラフを作成
            fig = go.Figure()
            
            valid_data_count = 0
            error_messages = []
            
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
                        
                        fig.add_trace(go.Scatter(
                            x=data.index,
                            y=data['Close'],
                            mode='lines',
                            name=f"{company_name} ({symbol})",
                            line=dict(color=color, width=2)
                        ))
                        
                        valid_data_count += 1
                        
                    else:
                        error_messages.append(f"銘柄コード '{symbol}' のデータを取得できませんでした。")
                        
                except Exception as e:
                    error_messages.append(f"銘柄 '{symbol}' の処理中にエラーが発生しました: {str(e)}")
            
            # テクニカル指標を追加
            if valid_data_count > 0:
                # 最初の有効な銘柄のデータを使用してテクニカル指標を計算
                for i, symbol in enumerate(symbols):
                    try:
                        data = self.stock_manager.get_stock_data(symbol, period)
                        if data is not None and not data.empty:
                            
                            # 移動平均線を追加
                            if ma_enabled and 'show' in ma_enabled:
                                ma_data = self.stock_manager.calculate_moving_average(data, ma_period)
                                color = self.colors[i % len(self.colors)]
                                
                                fig.add_trace(go.Scatter(
                                    x=data.index,
                                    y=ma_data,
                                    mode='lines',
                                    name=f"MA({ma_period}) - {symbol}",
                                    line=dict(color=color, width=1, dash='dash'),
                                    opacity=0.8
                                ))
                            
                            # ボリンジャーバンドを追加
                            if bb_enabled and 'show' in bb_enabled:
                                bb_data = self.stock_manager.calculate_bollinger_bands(data, bb_period, bb_std)
                                color = self.colors[i % len(self.colors)]
                                
                                # 上限線
                                fig.add_trace(go.Scatter(
                                    x=data.index,
                                    y=bb_data['upper'],
                                    mode='lines',
                                    name=f"BB上限({bb_period},{bb_std}σ) - {symbol}",
                                    line=dict(color=color, width=1, dash='dot'),
                                    opacity=0.6
                                ))
                                
                                # 下限線
                                fig.add_trace(go.Scatter(
                                    x=data.index,
                                    y=bb_data['lower'],
                                    mode='lines',
                                    name=f"BB下限({bb_period},{bb_std}σ) - {symbol}",
                                    line=dict(color=color, width=1, dash='dot'),
                                    opacity=0.6,
                                    fill='tonexty',
                                    fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1)'
                                ))
                                
                                # 中央線（移動平均）
                                fig.add_trace(go.Scatter(
                                    x=data.index,
                                    y=bb_data['middle'],
                                    mode='lines',
                                    name=f"BB中央({bb_period}) - {symbol}",
                                    line=dict(color=color, width=1, dash='dash'),
                                    opacity=0.7
                                ))
                                
                    except Exception as e:
                        error_messages.append(f"テクニカル指標の計算中にエラーが発生しました: {str(e)}")
            
            # グラフのレイアウトを更新
            fig.update_layout(
                title="株価チャート",
                xaxis_title="日付",
                yaxis_title="株価",
                template="plotly_white",
                hovermode='x unified'
            )
            
            # ステータスメッセージを生成
            if valid_data_count > 0:
                status_msg = f"{valid_data_count}社のデータを表示中"
                if error_messages:
                    status_msg += f" (エラー: {len(error_messages)}件)"
            else:
                status_msg = "有効なデータを取得できませんでした。"
            
            if error_messages:
                status_msg += " - " + "; ".join(error_messages[:2])  # 最初の2つのエラーのみ表示
            
            return fig, status_msg
        
        @callback(
            [Output('stock-input-0', 'value'),
             Output('stock-input-1', 'value'),
             Output('stock-input-2', 'value'),
             Output('stock-input-3', 'value')],
            [Input('clear-button', 'n_clicks')]
        )
        def clear_inputs(n_clicks):
            if n_clicks > 0:
                return '', '', '', ''
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update
        
        @callback(
            [Output('favorites-list', 'children'),
             Output('favorites-status', 'children'),
             Output('favorite-input', 'value')],
            [Input('add-favorite-button', 'n_clicks'),
             Input('favorites-list', 'n_clicks')],
            [State('favorite-input', 'value')]
        )
        def update_favorites(add_clicks, list_clicks, symbol_input):
            ctx = dash.callback_context
            
            if not ctx.triggered:
                favorites = self.stock_manager.get_favorite_stocks()
                return self.render_favorites_list(favorites), f"お気に入り: {len(favorites)}/10", ""
            
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            if trigger_id == 'add-favorite-button' and add_clicks > 0 and symbol_input:
                result = self.stock_manager.add_favorite_stock(symbol_input.strip().upper())
                favorites = self.stock_manager.get_favorite_stocks()
                
                status_style = {'color': 'green' if result['success'] else 'red'}
                status_message = html.Div([
                    html.Span(f"お気に入り: {len(favorites)}/10", style={'color': '#666'}),
                    html.Br(),
                    html.Span(result['message'], style=status_style)
                ])
                
                return self.render_favorites_list(favorites), status_message, ""
            
            favorites = self.stock_manager.get_favorite_stocks()
            return self.render_favorites_list(favorites), f"お気に入り: {len(favorites)}/10", dash.no_update
        
        @callback(
            [Output('news-display', 'children'),
             Output('news-status', 'children')],
            [Input('get-news-button', 'n_clicks')]
        )
        def update_news(n_clicks):
            if n_clicks == 0:
                return "お気に入り銘柄を追加して「ニュース取得」ボタンをクリックしてください。", ""
            
            try:
                news_result = self.stock_manager.get_favorites_news(page_size=10)
                
                if news_result['success']:
                    if news_result['articles']:
                        news_components = self.render_news_list(news_result['articles'])
                        status = html.Div(news_result['message'], style={'color': 'green'})
                    else:
                        news_components = "ニュース記事が見つかりませんでした。"
                        status = html.Div("ニュースが見つかりませんでした", style={'color': 'orange'})
                else:
                    news_components = f"エラー: {news_result['message']}"
                    status = html.Div(news_result['message'], style={'color': 'red'})
                
                return news_components, status
                
            except Exception as e:
                error_msg = f"ニュース取得中にエラーが発生しました: {str(e)}"
                return error_msg, html.Div(error_msg, style={'color': 'red'})
        
        @callback(
            [Output('favorites-list', 'children', allow_duplicate=True),
             Output('favorites-status', 'children', allow_duplicate=True)],
            [Input({'type': 'remove-favorite', 'index': dash.dependencies.ALL}, 'n_clicks')],
            prevent_initial_call=True
        )
        def remove_favorite(n_clicks_list):
            ctx = dash.callback_context
            
            if not ctx.triggered or not any(n_clicks_list):
                raise dash.exceptions.PreventUpdate
            
            # どのボタンがクリックされたかを特定
            button_id = ctx.triggered[0]['prop_id']
            import json
            button_data = json.loads(button_id.split('.')[0])
            symbol_to_remove = button_data['index']
            
            # お気に入りから削除
            result = self.stock_manager.remove_favorite_stock(symbol_to_remove)
            favorites = self.stock_manager.get_favorite_stocks()
            
            status_style = {'color': 'green' if result['success'] else 'red'}
            status_message = html.Div([
                html.Span(f"お気に入り: {len(favorites)}/10", style={'color': '#666'}),
                html.Br(),
                html.Span(result['message'], style=status_style)
            ])
            
            return self.render_favorites_list(favorites), status_message
    
    def render_favorites_list(self, favorites):
        """お気に入り銘柄リストを描画"""
        if not favorites:
            return html.Div("お気に入り銘柄がありません", style={'color': '#999', 'font-style': 'italic'})
        
        items = []
        for fav in favorites:
            symbol = fav['symbol']
            company_name = fav.get('company_name', symbol)
            added_date = fav.get('added_date', '')
            
            if added_date:
                try:
                    from datetime import datetime
                    if isinstance(added_date, str):
                        date_obj = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                    else:
                        date_obj = added_date
                    formatted_date = date_obj.strftime('%m/%d')
                except:
                    formatted_date = ""
            else:
                formatted_date = ""
            
            item = html.Div([
                html.Span(f"{symbol}", style={'font-weight': 'bold', 'margin-right': '5px'}),
                html.Span(f"({company_name})", style={'font-size': '12px', 'color': '#666', 'margin-right': '5px'}),
                html.Span(formatted_date, style={'font-size': '10px', 'color': '#999', 'margin-right': '10px'}),
                html.Button(
                    '×',
                    id={'type': 'remove-favorite', 'index': symbol},
                    n_clicks=0,
                    style={
                        'background-color': '#dc3545',
                        'color': 'white',
                        'border': 'none',
                        'border-radius': '50%',
                        'width': '20px',
                        'height': '20px',
                        'font-size': '10px',
                        'cursor': 'pointer',
                        'float': 'right'
                    }
                )
            ], style={'margin-bottom': '5px', 'padding': '5px', 'border-bottom': '1px solid #eee'})
            
            items.append(item)
        
        return items
    
    def render_news_list(self, articles):
        """ニュース記事リストを描画"""
        if not articles:
            return "ニュース記事がありません。"
        
        news_items = []
        for i, article in enumerate(articles[:15], 1):  # 最大15件
            title = article.get('title', 'タイトルなし')
            description = article.get('description', '')
            date = article.get('formatted_date', article.get('publishedAt', ''))
            symbol = article.get('symbol', '')
            url = article.get('url', '')
            
            # 説明文を短縮
            if description and len(description) > 150:
                description = description[:147] + '...'
            
            news_item = html.Div([
                html.Div([
                    html.Span(f"[{symbol}]", style={
                        'background-color': '#e9ecef',
                        'padding': '2px 6px',
                        'border-radius': '3px',
                        'font-size': '11px',
                        'margin-right': '8px'
                    }),
                    html.Span(date, style={'font-size': '11px', 'color': '#666'})
                ], style={'margin-bottom': '5px'}),
                
                html.A(
                    title,
                    href=url,
                    target='_blank',
                    style={
                        'font-weight': 'bold',
                        'color': '#007bff',
                        'text-decoration': 'none',
                        'font-size': '14px',
                        'display': 'block',
                        'margin-bottom': '5px'
                    }
                ),
                
                html.P(description, style={
                    'font-size': '12px',
                    'color': '#555',
                    'margin': '0',
                    'line-height': '1.4'
                })
                
            ], style={
                'margin-bottom': '15px',
                'padding': '10px',
                'border-left': '3px solid #007bff',
                'background-color': '#f8f9fa'
            })
            
            news_items.append(news_item)
        
        return news_items
    
    def run(self, debug=True, host='127.0.0.1', port=8050):
        """Webアプリケーションを起動"""
        print(f"株価チャート表示アプリを起動中...")
        print(f"ブラウザで http://{host}:{port} を開いてください")
        self.app.run(debug=debug, host=host, port=port)


def main():
    """メイン実行関数"""
    app = StockChartWebApp()
    app.run()


if __name__ == "__main__":
    main()