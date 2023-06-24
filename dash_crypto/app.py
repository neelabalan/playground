import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash_html_components.Div import Div
from pycoingecko import CoinGeckoAPI

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, update_title=None)
cg = CoinGeckoAPI()
text_style = {
    "textAlign": "center",
    "fontFamily": "DejaVu Sans Mono",
}
app.layout = html.Div(
    [
        dcc.Interval(
            id="interval-component", interval=10000, n_intervals=0  # in milliseconds
        ),
        html.H1(
            children="0",
            id="live-price-update",
            style=text_style,
        ),
        html.Div(
            [
                html.Label("Dropdown"),
                dcc.Dropdown(
                    id="currency",
                    options=[
                        {"label": "USD", "value": "usd"},
                        {"label": "INR", "value": "inr"},
                        {"label": "EUR", "value": "eur"},
                    ],
                    value="usd",
                ),
            ]
        ),
        html.Br(), html.Br(), html.Br(), html.Br(),
        html.H4(children="In $", style=text_style),
        dash_table.DataTable(
            id="table",
            columns=[
                {"name": i, "id": i}
                for i in ["Coin", "Price", "Market Cap", "24h Volume", "24h Change"]
            ],
            data=[],
            export_format="csv"
        ),
    ]
)


@app.callback(
    dash.dependencies.Output("live-price-update", "children"),
    [
        dash.dependencies.Input("interval-component", "n_intervals"),
        dash.dependencies.Input("currency", "value"),
    ],
)
def update_price(children, value):
    currency_symbol_map = {"eur": "€ ", "inr": "₹ ", "usd": "$ "}
    return currency_symbol_map.get(value) + str(
        cg.get_price(ids="bitcoin", vs_currencies=value)["bitcoin"][value]
    )


@app.callback(
    dash.dependencies.Output("table", "data"),
    [dash.dependencies.Input("interval-component", "n_intervals")],
)
def generate_table(data):
    response = cg.get_price(
        ids=["bitcoin", "litecoin", "ethereum", "tether", "dogecoin"],
        vs_currencies="usd",
        include_market_cap="true",
        include_24hr_vol="true",
        include_24hr_change="true",
    )
    return [
        {
            "Coin": r,
            "Price": response[r]["usd"],
            "Market Cap": response[r]["usd_market_cap"],
            "24h Volume": response[r]["usd_24h_vol"],
            "24h Change": response[r]["usd_24h_change"],
        }
        for r in response
    ]


if __name__ == "__main__":
    app.run_server(debug=True)