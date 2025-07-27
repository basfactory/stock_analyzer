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
                    ])
                    
                ], style={
                    'width': '25%',
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'padding': '20px',
                    'background-color': '#f8f9fa',
                    'border-radius': '10px',
                    'margin-right': '20px'
                }),
                
                # 右側のグラフ表示エリア
                html.Div([
                    dcc.Graph(
                        id='stock-chart',
                        style={'height': '600px'}
                    ),
                    html.Div(id='status-message', style={'margin-top': '10px'})
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