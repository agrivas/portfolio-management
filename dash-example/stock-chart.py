import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance

def get_data(ticker):
    ticker_data = yfinance.Ticker(ticker)
    hist = ticker_data.history(period='1y')

    hist['diff'] = hist['Close'] - hist['Open']
    hist.loc[hist['diff'] >= 0, 'color'] = 'green'
    hist.loc[hist['diff'] < 0, 'color'] = 'red'

    return hist

def draw_chart(data, ticker):
    hist = data[ticker]
    price_max = hist['Close']
    volume_max = hist['Volume']

    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Candlestick(x = hist.index,
                                open = hist['Open'],
                                high = hist['High'],
                                low = hist['Low'],
                                close = hist['Close'],
                                name = 'Price'), secondary_y = False)
    fig.add_trace(go.Bar(x = hist.index, y = hist['Volume'], marker={'color': hist['color']}, name = 'Volume'), secondary_y = True)
    fig.update_yaxes(range = [0, price_max*1.1], secondary_y=False)
    fig.update_yaxes(range = [0, volume_max*100], secondary_y=True)
    fig.update_yaxes(visible=False, secondary_y=True)
    # fig.update_xaxes(rangebreaks = [
    #     dict(bounds=['sat','mon']),
    #     #dict(bounds=[16, 9.5], pattern='hour'), # for hourly chart, hide non-trading hours (24hr format)
    #     dict(values=["2021-12-25","2022-01-01"]) #hide Xmas and New Year
    # ])

    fig.add_trace(go.Scatter(x = hist.index, y = hist['Close'].rolling(20).mean(), name = '20D-MA'))
    fig.update_layout(title = {'text': ticker}, height = 750)

    return fig

stocks = {
    'TSLA': 'Tesla',
    'AAPL': 'Apple',
    'MSFT': 'Microsoft'}

data = {symbol: get_data(symbol) for symbol in stocks.keys()}

app = dash.Dash()
app.layout = html.Div([
    html.Div('Hello World From Dash.'),
    html.H1('H1 tag here'),
    html.Div(dcc.Dropdown(id='dropdown',
                          options = [{ 'label': name, 'value': ticker } for ticker, name in stocks.items()],
                          value = list(stocks.keys())[0])),
    dcc.Graph(id='fig', figure=draw_chart(data, list(stocks.keys())[0]))
])

@app.callback(Output('fig', 'figure'),
              Input('dropdown', 'value'))

def update_graph(ticker):
    return draw_chart(data, ticker)

app.run_server(debug=True)



