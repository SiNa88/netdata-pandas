# AUTOGENERATED! DO NOT EDIT! File to edit: 00_data.ipynb (unless otherwise specified).

__all__ = ['get_chart_list', 'get_chart', 'get_charts', 'get_data']

# Cell
#export
import asks
import trio
import pandas as pd
import requests

# Cell


def get_chart_list(host: str = '127.0.0.1:19999', starts_with: str = None) -> list:
    """Get list of all available charts.

    Parameters
    ----------
    host : str
        The host we want to get a list of available charts from.
    y
        Description of parameter `y` (with type not specified)

    Returns
    -------
    chart_list : list
        A list of availalbe charts.

    """
    url = f"http://{host}/api/v1/charts"
    r = requests.get(url)
    charts = r.json().get('charts')
    chart_list = [chart for chart in charts]
    if starts_with:
        chart_list = [chart for chart in chart_list if chart.startswith(starts_with)]
    return chart_list

# Cell


async def get_chart(api_call, data, col_sep='|'):
    """Get data for an individual chart.
    """
    url, chart = api_call
    r = await asks.get(url)
    r_json = r.json()
    df = pd.DataFrame(r_json['data'], columns=['time_idx'] + r_json['labels'][1:])
    df = df.set_index('time_idx').add_prefix(f'{chart}{col_sep}')
    data[chart] = df


async def get_charts(api_calls, col_sep='|'):
    """Create a nursey to make seperate async calls to get each chart.
    """
    data = {}
    with trio.move_on_after(60):
        async with trio.open_nursery() as nursery:
            for api_call in api_calls:
                nursery.start_soon(get_chart, api_call, data, col_sep)
    df = pd.concat(data, join='outer', axis=1, sort=True)
    df.columns = df.columns.droplevel()
    return df


def get_data(host: str = 'london.my-netdata.io', charts: list = ['system.cpu'], after: int = -60,
             before: int = 0, points: int = 0, col_sep: str = '|', numeric_only: bool = False,
             ffill: bool = True, diff: bool = False) -> pd.DataFrame:
    """Define api calls to make and any post processing to be done.
    """
    api_calls = [
        (
            f'http://{host}/api/v1/data?chart={chart}&after={after}&before={before}&points={points}&format=json',
            chart
        )
        for chart in charts
    ]
    df = trio.run(get_charts, api_calls, col_sep)
    if numeric_only:
        df = df._get_numeric_data()
    if ffill:
        df = df.ffill()
    if diff:
        df = df.diff().dropna(how='all')
    return df