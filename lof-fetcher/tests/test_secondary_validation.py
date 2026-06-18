from fetcher.sources.csv_assets import LofMeta
from fetcher.sources.secondary_validation import ActivityStats, FundNav, VenueQuote, classify_watchlist_row


def make_row(code="501050", name="华夏中证500ETF联接(LOF)", fund_type="index", status="active", benchmark="中证500指数收益率×95%"):
    return LofMeta(code=code, name=name, type=fund_type, scale_yi=40.0, benchmark_raw=benchmark, status=status)


def test_venue_match_nav_share_class_diff_is_not_mapping_error():
    result = classify_watchlist_row(
        make_row(name="华夏上证50AH优选指数(LOF)"),
        VenueQuote("eastmoney_quote", "50AHLOF", 1.7, 1000, 1_000_000, None, True),
        FundNav("fundgz", "华夏上证50AH优选指数A", "2026-06-17", 1.7, 1.7, "2026-06-18 11:27", True),
        ActivityStats("kline", 20, 800_000, 20, "low_active"),
    )

    assert result.name_compare in {"multi_source_match", "nav_match_venue_abbrev", "true_rename_or_share_class_change"}
    assert result.recommendation in {"keep", "rename"}


def test_qdii_goes_to_phase2():
    result = classify_watchlist_row(
        make_row(code="160516", name="诺安油气能源(LOF)", fund_type="industry", benchmark="标普全球石油净总收益指数"),
        VenueQuote("eastmoney_quote", "券商基金", 0.0, 0, 0, None, False),
        FundNav("fundgz", "博时证券公司ETF联接A", "2026-06-17", 1.3, 1.3, "2026-06-18 11:27", True),
        ActivityStats("kline", 0, None, 0, "no_kline"),
    )

    assert result.is_qdii is False
    assert result.recommendation == "replace"


def test_suspended_non_qdii_replaces():
    result = classify_watchlist_row(
        make_row(code="123456", name="测试行业指数(LOF)", fund_type="industry"),
        VenueQuote("eastmoney_quote", "测试LOF", None, 0, 0, None, False),
        FundNav("fundgz", "测试行业指数A", "2026-06-17", 1.0, 1.0, "2026-06-18 11:27", True),
        ActivityStats("kline", 0, None, 0, "no_kline"),
    )

    assert result.recommendation == "replace"
