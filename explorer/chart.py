from typing import Optional
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from .models import QueryResult


def get_pie_chart(result: QueryResult) -> Optional[str]:
    if len(result.data) < 1 \
        or not isinstance(result.data[0][0], str) \
        or not isinstance(result.data[0][1], (int, float)):
        return None
    labels = [row[0] for row in result.data]
    values = [row[1] for row in result.data]
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels)
    return get_csv_as_hex(fig)


def get_csv_as_hex(fig: Figure) -> str:
    buffer = BytesIO()
    fig.savefig(buffer, format='svg')
    buffer.seek(0)
    graph = buffer.getvalue().decode('utf-8')
    buffer.close()
    return graph
