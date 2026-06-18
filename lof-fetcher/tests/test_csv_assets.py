from fetcher.sources.csv_assets import benchmark_weights


class Component:
    def __init__(self, index_code, weight):
        self.index_code = index_code
        self.weight = weight


def test_benchmark_weights_split_cash():
    assigned, cash = benchmark_weights([
        Component("000300.SH", 0.8),
        Component("CASH", 0.2),
    ])

    assert assigned == 0.8
    assert cash == 0.2
