from io import BytesIO
from typing import Iterable, Optional
from .models import QueryResult

BAR_WIDTH = 0.2


def get_chart(result: QueryResult, chart_type: str, num_rows: int) -> Optional[str]:
    import matplotlib.pyplot as plt
    """
        Return a line or bar chart in SVG format if the result table adheres to the expected format.
        A line chart is rendered if
        * there is at least on row of in the result table
        * there is at least one numeric column (the first column (with index 0) does not count)
        The first column is used as x-axis labels.
        All other numeric columns represent a line on the chart.
        The name of the column is used as the name of the line in the legend.
        Not numeric columns (except the first on) are ignored.
    """
    if chart_type not in ("bar", "line"):
        return
    if len(result.data) < 1:
        return None
    data = result.data[:num_rows]
    numeric_columns = [
        c for c in range(1, len(data[0]))
        if all([isinstance(col[c], (int, float)) or col[c] is None for col in data])
    ]
    # Don't create charts for > 10 series. This is a lightweight visualization.
    if len(numeric_columns) < 1 or len(numeric_columns) > 10:
        return None
    labels = [row[0] for row in data]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    bars = []
    bar_positions = []
    for idx, col_num in enumerate(numeric_columns):
        if chart_type == "bar":
            values = [row[col_num] if row[col_num] is not None else 0 for row in data]
            bar_container = ax.bar([x + idx * BAR_WIDTH
                                    for x in range(len(labels))], values, BAR_WIDTH, label=result.headers[col_num])
            bars.append(bar_container)
            bar_positions.append([(rect.get_x(), rect.get_height()) for rect in bar_container])
        if chart_type == "line":
            ax.plot(labels, [row[col_num] for row in data], label=result.headers[col_num])

    ax.set_xlabel(result.headers[0])

    if chart_type == "bar":
        ax.set_xticks([x + BAR_WIDTH * (len(numeric_columns) / 2 - 0.5) for x in range(len(labels))])
        ax.set_xticklabels(labels)

    ax.legend()
    for label in ax.get_xticklabels():
        label.set_rotation(20)  # makes labels fit better
        label.set_ha("right")
    svg_str = get_svg(fig)
    return svg_str


def get_svg(fig) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format="svg")
    buffer.seek(0)
    graph = buffer.getvalue().decode("utf-8")
    buffer.close()
    return graph


def is_numeric(column: Iterable) -> bool:
    return all([isinstance(value, (int, float)) or value is None for value in column])
