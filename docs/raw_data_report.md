# Raw Data Inspection Report

## Source
- File: `/home/shraddha/Documents/Projects/dynamic_pricing_study/data/raw/online_retail_II_2010_2011.csv`
- Phase: 1 (Raw Data Inspection)

## Dataset Shape
- Rows: 541,910
- Columns: 8

## Columns and Data Types
| column | dtype |
| --- | --- |
| Invoice | object |
| StockCode | object |
| Description | object |
| Quantity | int64 |
| InvoiceDate | object |
| Price | float64 |
| Customer ID | float64 |
| Country | object |

## Null Count and Percentage
| column | null_count | null_percent |
| --- | --- | --- |
| Customer ID | 135080 | 24.9266 |
| Description | 1454 | 0.2683 |
| Invoice | 0 | 0.0 |
| StockCode | 0 | 0.0 |
| Quantity | 0 | 0.0 |
| InvoiceDate | 0 | 0.0 |
| Price | 0 | 0.0 |
| Country | 0 | 0.0 |

## Cancellation Invoices
- Rows with `Invoice` starting with `C`: 9,288 (1.71%)

## Quantity Distribution
| index | Quantity |
| --- | --- |
| count | 541910.0 |
| mean | 9.552233765754462 |
| std | 218.08095694392432 |
| min | -80995.0 |
| 1% | -2.0 |
| 5% | 1.0 |
| 50% | 3.0 |
| 95% | 29.0 |
| 99% | 100.0 |
| max | 80995.0 |

### Quantity Quality Flags
| metric | value |
| --- | --- |
| negative_quantity_rows | 10624 |
| zero_quantity_rows | 0 |

## Price Distribution
| index | Price |
| --- | --- |
| count | 541910.0 |
| mean | 4.611138332933514 |
| std | 96.75976549366526 |
| min | -11062.06 |
| 1% | 0.19 |
| 5% | 0.42 |
| 50% | 2.08 |
| 95% | 9.95 |
| 99% | 18.0 |
| max | 38970.0 |

### Price Quality Flags
| metric | value |
| --- | --- |
| negative_price_rows | 2 |
| zero_price_rows | 2515 |

## Country Distribution (Rows)
| country | row_count |
| --- | --- |
| United Kingdom | 495478 |
| Germany | 9495 |
| France | 8558 |
| EIRE | 8196 |
| Spain | 2533 |
| Netherlands | 2371 |
| Belgium | 2069 |
| Switzerland | 2002 |
| Portugal | 1519 |
| Australia | 1259 |
| Norway | 1086 |
| Italy | 803 |
| Channel Islands | 758 |
| Finland | 695 |
| Cyprus | 622 |
| Sweden | 462 |
| Unspecified | 446 |
| Austria | 401 |
| Denmark | 389 |
| Japan | 358 |

## Revenue per Country (Raw)
| country | Revenue |
| --- | --- |
| United Kingdom | 8187806.364 |
| Netherlands | 284661.54 |
| EIRE | 263276.82 |
| Germany | 221698.21 |
| France | 197421.9 |
| Australia | 137077.27 |
| Switzerland | 56385.35 |
| Spain | 54774.58 |
| Belgium | 40910.96 |
| Sweden | 36595.91 |
| Japan | 35340.62 |
| Norway | 35163.46 |
| Portugal | 29367.02 |
| Finland | 22326.74 |
| Channel Islands | 20086.29 |
| Denmark | 18768.14 |
| Italy | 16890.51 |
| Cyprus | 12946.29 |
| Austria | 10154.32 |
| Hong Kong | 10117.04 |

## Date Range Validation
- Min date: 2010-12-01 08:26:00, Max date: 2011-12-09 12:50:00, Unparseable rows: 0

## Frozen Decisions for Next Phase
- Keep UK only
- Remove cancelled invoices
- Remove negative quantities
- Remove zero or negative prices
- Temporal boundary already fixed at source (2010–2011 only)