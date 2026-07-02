// 本地 mock 数据：dev-004 接口未上线前用于跑通三页
// 默认池已切到 watchlist-v2（30 只，QDII 后置二期），接口返回结构保持 PRD §6。

import type {
  BenchmarkComponent,
  FundType,
  IngestRealtimeBody,
  IngestRealtimeData,
  LofDetailData,
  LofHistoryData,
  LofListData,
  ListParams,
  QdiiEstimateFields
} from '@/api/types'

interface MockMeta {
  code: string
  name: string
  type: FundType
  scale_yi: number
  benchmark_raw: string
  status: 'active' | 'active_low_liquidity'
  coverage_top10: number
  benchmark_assigned_weight: number
  cash_weight: number
  benchmark_components: BenchmarkComponent[]
  qdii?: QdiiEstimateFields
}

const META: MockMeta[] = [
  {
    code: "161725",
    name: "招商中证白酒指数(LOF)A",
    type: 'index',
    scale_yi: 300,
    benchmark_raw: "中证白酒指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active',
    coverage_top10: 0.93,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "399997.SZ",
        name: "中证白酒指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "161005",
    name: "富国天惠成长混合(LOF)A",
    type: 'active',
    scale_yi: 180,
    benchmark_raw: "沪深300指数收益率×80%+中证综合债券指数收益率×20%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.8
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.2
      }
    ]
  },
  {
    code: "163406",
    name: "兴全合润混合A",
    type: 'active',
    scale_yi: 150,
    benchmark_raw: "沪深300指数收益率×75%+上证国债指数收益率×25%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "000012.SH",
        name: "上证国债指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "160706",
    name: "嘉实沪深300ETF联接A",
    type: 'index',
    scale_yi: 80,
    benchmark_raw: "沪深300指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "501050",
    name: "华夏上证50AH优选指数A",
    type: 'index',
    scale_yi: 40,
    benchmark_raw: "上证50AH优选指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "950090.CSI",
        name: "上证50AH优选指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "160505",
    name: "博时主题行业混合(LOF)",
    type: 'active',
    scale_yi: 30,
    benchmark_raw: "沪深300指数收益率×80%+中证综合债券指数收益率×20%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.8
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.2
      }
    ]
  },
  {
    code: "162605",
    name: "景顺长城鼎益混合(LOF)A",
    type: 'active',
    scale_yi: 30,
    benchmark_raw: "沪深300指数收益率×80%+中证综合债券指数收益率×20%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.8
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.2
      }
    ]
  },
  {
    code: "161024",
    name: "富国中证军工指数(LOF)A",
    type: 'index',
    scale_yi: 18,
    benchmark_raw: "中证军工指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "399967.SZ",
        name: "中证军工指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "160119",
    name: "南方中证500ETF联接(LOF)A",
    type: 'index',
    scale_yi: 15,
    benchmark_raw: "中证500指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "000905.SH",
        name: "中证500指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "160632",
    name: "鹏华酒A",
    type: 'industry',
    scale_yi: 12,
    benchmark_raw: "中证酒指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active',
    coverage_top10: 0.72,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "399987.SZ",
        name: "中证酒指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "160220",
    name: "国泰民益混合(LOF)A",
    type: 'active',
    scale_yi: 3,
    benchmark_raw: "沪深300指数收益率×60%+中证综合债券指数收益率×40%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.6
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.4
      }
    ]
  },
  {
    code: "161903",
    name: "万家行业优选混合(LOF)",
    type: 'active',
    scale_yi: 8,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501227",
    name: "泓德红利优选混合(LOF)A",
    type: 'active',
    scale_yi: 12,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501205",
    name: "鹏华创新未来混合(LOF)C",
    type: 'active',
    scale_yi: 12,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501096",
    name: "国联安科创混合(LOF)",
    type: 'active',
    scale_yi: 6,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501099",
    name: "平安新兴产业混合(LOF)",
    type: 'active',
    scale_yi: 6,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501201",
    name: "红土创新科技创新股票(LOF)A",
    type: 'active',
    scale_yi: 6,
    benchmark_raw: "中国战略新兴产业成份指数收益率×80%+中证综合债券指数收益率×20%",
    status: 'active',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.8
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.2
      }
    ]
  },
  {
    code: "501203",
    name: "易方达创新未来混合(LOF)",
    type: 'active',
    scale_yi: 5,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501208",
    name: "中欧创新未来混合(LOF)",
    type: 'active',
    scale_yi: 5,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501085",
    name: "财通科创主题灵活配置混合(LOF)",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501219",
    name: "华夏智胜先锋股票(LOF)A",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "中证800指数收益率×80%+中证综合债券指数收益率×20%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000906.SH",
        name: "中证800指数",
        weight: 0.8
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.2
      }
    ]
  },
  {
    code: "501095",
    name: "中银证券科技创新混合(LOF)",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501077",
    name: "富国创新企业灵活配置混合(LOF)A",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501057",
    name: "汇添富中证新能源汽车产业指数(LOF)A",
    type: 'index',
    scale_yi: 4,
    benchmark_raw: "中证新能源汽车产业指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active_low_liquidity',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "930997.CSI",
        name: "中证新能源汽车产业指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "501206",
    name: "汇添富创新未来混合(LOF)",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "沪深300指数收益率×75%+中证综合债券指数收益率×25%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000300.SH",
        name: "沪深300指数",
        weight: 0.75
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.25
      }
    ]
  },
  {
    code: "501078",
    name: "广发科创主题灵活配置混合(LOF)",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501097",
    name: "国寿安保科技创新混合(LOF)",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501090",
    name: "华宝中证消费龙头ETF联接A",
    type: 'index',
    scale_yi: 4,
    benchmark_raw: "中证消费龙头指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active_low_liquidity',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "931068.CSI",
        name: "中证消费龙头指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  },
  {
    code: "501081",
    name: "中欧科创主题混合(LOF)A",
    type: 'active',
    scale_yi: 4,
    benchmark_raw: "中国战略新兴产业成份指数收益率×70%+中证综合债券指数收益率×30%",
    status: 'active_low_liquidity',
    coverage_top10: 0.52,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [
      {
        index_code: "000891.CSI",
        name: "中国战略新兴产业成份指数",
        weight: 0.7
      },
      {
        index_code: "H11009.CSI",
        name: "中证综合债券指数",
        weight: 0.3
      }
    ]
  },
  {
    code: "501311",
    name: "嘉实港股通新经济指数A",
    type: 'index',
    scale_yi: 4,
    benchmark_raw: "中证港股通新经济指数收益率×95%+银行活期存款利率(税后)×5%",
    status: 'active_low_liquidity',
    coverage_top10: 0.2,
    benchmark_assigned_weight: 0.95,
    cash_weight: 0.05,
    benchmark_components: [
      {
        index_code: "930709.CSI",
        name: "中证港股通新经济指数",
        weight: 0.95
      },
      {
        index_code: "CASH",
        name: "银行活期存款利率",
        weight: 0.05
      }
    ]
  }
]


const QDII_HIGH_MOCKS: MockMeta[] = [
  {
    code: '510900',
    name: '易方达恒生国企(QDII-ETF)',
    type: 'index',
    scale_yi: 85,
    benchmark_raw: '恒生中国企业指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'HSCEI.HI', name: '恒生中国企业指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 1.142,
      qdii_estimate_premium: 0.0321,
      qdii_reference_index_code: 'HSCEI.HI',
      qdii_reference_index_name: '恒生中国企业指数',
      qdii_reference_index_change_pct: 0.0112,
      qdii_fx_change_pct: -0.0018,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '159920',
    name: '华夏恒生ETF(QDII)',
    type: 'index',
    scale_yi: 120,
    benchmark_raw: '恒生指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'HSI.HI', name: '恒生指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 1.058,
      qdii_estimate_premium: 0.0245,
      qdii_reference_index_code: 'HSI.HI',
      qdii_reference_index_name: '恒生指数',
      qdii_reference_index_change_pct: 0.0096,
      qdii_fx_change_pct: -0.0018,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '159941',
    name: '广发纳指100ETF(QDII)',
    type: 'index',
    scale_yi: 95,
    benchmark_raw: '纳斯达克100指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'NDX.GI', name: '纳斯达克100指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 1.318,
      qdii_estimate_premium: 0.0418,
      qdii_reference_index_code: 'NDX.GI',
      qdii_reference_index_name: '纳斯达克100指数',
      qdii_reference_index_change_pct: 0.0068,
      qdii_fx_change_pct: 0.0021,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '513500',
    name: '博时标普500ETF(QDII)',
    type: 'index',
    scale_yi: 70,
    benchmark_raw: '标普500指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'SPX.GI', name: '标普500指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: 2.426,
      qdii_estimate_premium: 0.0189,
      qdii_reference_index_code: 'SPX.GI',
      qdii_reference_index_name: '标普500指数',
      qdii_reference_index_change_pct: 0.0042,
      qdii_fx_change_pct: 0.0021,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: '2026-07-01'
    }
  },
  {
    code: '161125',
    name: '易方达标普500指数(QDII-LOF)',
    type: 'index',
    scale_yi: 45,
    benchmark_raw: '标普500指数收益率（经汇率调整）',
    status: 'active',
    coverage_top10: 1,
    benchmark_assigned_weight: 1,
    cash_weight: 0,
    benchmark_components: [{ index_code: 'SPX.GI', name: '标普500指数', weight: 1 }],
    qdii: {
      qdii_estimate_nav: null,
      qdii_estimate_premium: null,
      qdii_reference_index_code: 'SPX.GI',
      qdii_reference_index_name: '标普500指数',
      qdii_reference_index_change_pct: null,
      qdii_fx_change_pct: null,
      qdii_estimate_quality: 'high',
      qdii_estimate_source: '参考指数+汇率估算',
      qdii_nav_date: null
    }
  }
]

META.push(...QDII_HIGH_MOCKS)

function pseudoRand(seed: string, salt = 0): number {
  let hash = 2166136261 ^ salt
  for (let index = 0; index < seed.length; index++) {
    hash ^= seed.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return ((hash >>> 0) % 10000) / 10000
}

function makeQuote(meta: MockMeta) {
  const minuteSeed = Math.floor(Date.now() / 60000)
  const randomPrice = pseudoRand(meta.code, minuteSeed)
  const randomPremium = pseudoRand(meta.code, minuteSeed + 1)
  const iopv = +(0.6 + randomPrice * 1.6).toFixed(3)
  const premium = +((randomPremium - 0.5) * 0.12).toFixed(4)
  const price = +(iopv * (1 + premium)).toFixed(3)
  const coverage =
    meta.type === 'index'
      ? 1.0
      : +(meta.coverage_top10 * 0.5 + meta.benchmark_assigned_weight * 0.5).toFixed(2)
  const pctile = +pseudoRand(meta.code, 7).toFixed(2)
  return { price, iopv, premium, coverage, pctile }
}

export function mockListResponse(params: ListParams = {}): LofListData {
  let list = META.slice()
  if (params.type && params.type !== 'all') {
    list = list.filter((meta) => meta.type === params.type)
  }
  const items = list.map((meta) => {
    const quote = makeQuote(meta)
    return {
      code: meta.code,
      name: meta.name,
      type: meta.type,
      price: quote.price,
      iopv: quote.iopv,
      premium: quote.premium,
      coverage: quote.coverage,
      pctile_30d: quote.pctile,
      source_quality: meta.status === 'active_low_liquidity' ? 'degraded' as const : 'ok' as const,
      ...meta.qdii
    }
  })

  const sort = params.sort || 'premium_desc'
  if (sort === 'premium_desc') items.sort((a, b) => b.premium - a.premium)
  else if (sort === 'premium_asc') items.sort((a, b) => a.premium - b.premium)
  else if (sort === 'code') items.sort((a, b) => a.code.localeCompare(b.code))

  return { ts: new Date().toISOString(), items }
}

export function mockDetailResponse(code: string): LofDetailData {
  const meta = META.find((item) => item.code === code) || META[0]
  const quote = makeQuote(meta)
  return {
    code: meta.code,
    name: meta.name,
    type: meta.type,
    scale_yi: meta.scale_yi,
    coverage_top10: meta.coverage_top10,
    coverage_breakdown: {
      top10_weight: meta.coverage_top10,
      benchmark_assigned_weight: meta.benchmark_assigned_weight,
      cash_weight: meta.cash_weight
    },
    benchmark_raw: meta.benchmark_raw,
    benchmark_components: meta.benchmark_components,
    holdings_top10: [
      { stock_code: '600519.SH', stock_name: '贵州茅台', weight: 0.15 },
      { stock_code: '000858.SZ', stock_name: '五粮液', weight: 0.12 },
      { stock_code: '000568.SZ', stock_name: '泸州老窖', weight: 0.10 },
      { stock_code: '600809.SH', stock_name: '山西汾酒', weight: 0.09 },
      { stock_code: '000596.SZ', stock_name: '古井贡酒', weight: 0.07 },
      { stock_code: '603369.SH', stock_name: '今世缘', weight: 0.06 },
      { stock_code: '000799.SZ', stock_name: '酒鬼酒', weight: 0.06 },
      { stock_code: '603198.SH', stock_name: '迎驾贡酒', weight: 0.05 },
      { stock_code: '600702.SH', stock_name: '舍得酒业', weight: 0.05 },
      { stock_code: '000860.SZ', stock_name: '顺鑫农业', weight: 0.04 }
    ],
    realtime: {
      ts: new Date().toISOString(),
      price: quote.price,
      iopv: quote.iopv,
      premium: quote.premium,
      coverage: quote.coverage,
      source_quality: meta.status === 'active_low_liquidity' ? 'degraded' : 'ok'
    },
    pctile_30d: quote.pctile,
    ...meta.qdii
  }
}

export function mockHistoryResponse(code: string, days = 30): LofHistoryData {
  const meta = META.find((item) => item.code === code) || META[0]
  const items = []
  const today = new Date()
  for (let index = days - 1; index >= 0; index--) {
    const date = new Date(today)
    date.setDate(date.getDate() - index)
    const day = date.getDay()
    if (day === 0 || day === 6) continue
    const random = pseudoRand(meta.code, index + 100)
    const close = +(0.6 + random * 1.6).toFixed(3)
    const nav = +(close * (1 - (random - 0.5) * 0.06)).toFixed(3)
    const premium = +((close - nav) / nav).toFixed(4)
    items.push({
      date: date.toISOString().slice(0, 10),
      close_price: close,
      official_nav: nav,
      premium_close: premium,
      premium_pctile_30d: +pseudoRand(meta.code, index + 200).toFixed(2)
    })
  }
  return { code: meta.code, granularity: 'day', items }
}

export function mockIngestRealtimeResponse(body: IngestRealtimeBody): IngestRealtimeData {
  const accepted = Array.isArray(body.items) ? body.items.length : 0
  return { accepted, rejected: 0 }
}

export const mockMetaList = META
