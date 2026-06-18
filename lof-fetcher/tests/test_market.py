from fetcher.sources.market import parse_sina_quote


def test_parse_sina_quote():
    text = 'var hq_str_sh600519="贵州茅台,1500.00,1490.00,1510.50,1520.00";'

    quote = parse_sina_quote("sh600519", text)

    assert quote is not None
    assert quote.code == "sh600519"
    assert quote.name == "贵州茅台"
    assert quote.price == 1510.5
    assert quote.previous_close == 1490.0
