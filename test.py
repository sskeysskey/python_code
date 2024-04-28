from bokeh.plotting import figure, output_file, save, show
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
import sqlite3
from datetime import datetime, timedelta

def fetch_data(name):
    conn = sqlite3.connect('/Users/yanzhang/Finance.db')
    cursor = conn.cursor()
    three_months_ago = datetime.now() - timedelta(days=90)
    query = "SELECT date, price FROM Stocks WHERE name = ? AND date >= ? ORDER BY date;"
    cursor.execute(query, (name, three_months_ago.strftime("%Y-%m-%d")))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def create_html_plot(name):
    data = fetch_data(name)
    if data:
        dates, prices = zip(*data)
        dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
    else:
        dates, prices = [], []

    source = ColumnDataSource(data=dict(date=dates, price=prices))

    plot = figure(title=f"{name} - Price Chart", x_axis_type="datetime", sizing_mode="stretch_width", height=250)
    plot.line('date', 'price', source=source, line_width=2)
    
    plot.xaxis.formatter = DatetimeTickFormatter(months="%b %Y")
    plot.xaxis.major_label_orientation = 3.14/4

    output_file(f"{name}.html")
    save(plot)
    show(plot)

# 生成具体某个产品的图表HTML
create_html_plot('NASDAQ')