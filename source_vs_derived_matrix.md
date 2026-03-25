# Source vs Derived Matrix (v1)

Legend:
- Source: primary data to ingest into canonical tables.
- Derived: report/calculated output; used for validation only.
- Mixed: contains both source and derived blocks in the same sheet.
- Empty: no usable data.

**10-LSO_Individual_Sales 28.2.2026.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7-Individual Sales | Derived | Outlet (hints), Township | Month blocks with PKT/BOT are report totals; metadata columns can seed outlet master. |

**13-KT Individual Sales_1.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7. Individual Sales | Derived | Outlet (hints), Township | Month blocks with PKT/BOT/LIT are report totals. |

**7-MTL Individual Sale_2.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7- Individual Sales | Derived | Outlet (hints), Township | Month blocks with PKT/BOT are report totals. |

**7-MTL SKU Summary_4.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7-MTL | Derived | Product (hints) | SKU summary with Bot/Lit by month. |

**7-MTL for Table and DailySales(2026 Jan to Mar).xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| Table | Source | Product, Outlet, Township, Route | Contains product master blocks and outlet master block in one sheet. |
| DailySales | Source | SalesTransaction, SalesTransactionFinancials | Full transaction table with financial columns. |
| Sheet1 | Derived | Targets/Follow-Up | Target/Sale/Ach% only. |

**7-MTL for Township Summary_4.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7-MTL | Derived | Township | Township summary; formulas reference township detail sheets. |
| Meiktila | Derived | Product, Township | Township detail by product x month. |
| Tharzi | Derived | Product, Township | Township detail by product x month. |
| Pyaw Bwe | Derived | Product, Township | Township detail by product x month. |
| Want Twin | Derived | Product, Township | Township detail by product x month. |
| Mahaling | Derived | Product, Township | Township detail by product x month. |
| Yamethin | Derived | Product, Township | Township detail by product x month. |
| Kyaukpadaung | Derived | Product, Township | Township detail by product x month. |
| Taungthar | Derived | Product, Township | Township detail by product x month. |
| Myingyan | Derived | Product, Township | Township detail by product x month. |
| Bagan | Derived | Product, Township | Township detail by product x month. |
| Pakokku | Derived | Product, Township | Township detail by product x month. |

**7-MTL for Township Summary_4_1.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7-MTL | Derived | Township | Duplicate of `7-MTL for Township Summary_4.xlsx`. |
| Meiktila | Derived | Product, Township | Duplicate. |
| Tharzi | Derived | Product, Township | Duplicate. |
| Pyaw Bwe | Derived | Product, Township | Duplicate. |
| Want Twin | Derived | Product, Township | Duplicate. |
| Mahaling | Derived | Product, Township | Duplicate. |
| Yamethin | Derived | Product, Township | Duplicate. |
| Kyaukpadaung | Derived | Product, Township | Duplicate. |
| Taungthar | Derived | Product, Township | Duplicate. |
| Myingyan | Derived | Product, Township | Duplicate. |
| Bagan | Derived | Product, Township | Duplicate. |
| Pakokku | Derived | Product, Township | Duplicate. |

**9-MLM Individual Sales.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7-Individual Sales | Derived | Outlet (hints), Township | Month blocks with PKT/BOT/Liter are report totals. |
| Sheet1 | Empty |  | No usable data. |

**9-MLM SKU Summary_4.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 9-MLM (SKU) | Derived | Product (hints) | SKU summary with Bot/Lit by month. |

**9-MLM TOWNSHIP SUMMARY_1.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 4-Township Summary | Derived | Township | Summary; formulas reference township detail sheets. |
| 4--Township summary | Derived | Township | Summary variant with averages; not a source. |
| 4-MawLaMyaing | Derived | Product, Township | Township detail by product x month. |
| 4-Hpa-An | Derived | Product, Township | Township detail by product x month. |
| 4-Paung | Derived | Product, Township | Township detail by product x month. |
| 4-Mu Don | Derived | Product, Township | Township detail by product x month. |
| 4-ThaHtone | Derived | Product, Township | Township detail by product x month. |
| 4-KawKariek | Derived | Product, Township | Township detail by product x month. |
| 4-Yaye | Derived | Product, Township | Township detail by product x month. |
| 4-Phar Pon | Derived | Product, Township | Township detail by product x month. |
| 4-Bagoda-3 | Derived | Product, Township | Township detail by product x month. |
| 4-Chang Sone | Derived | Product, Township | Township detail by product x month. |
| 4-Than Phyu Zayat | Derived | Product, Township | Township detail by product x month. |
| Thein ZatYat | Derived | Product, Township | Township detail by product x month. |

**9-MLM Table and DailySales-2026_Feb.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| Table | Source | Product, Outlet, Township, Route | Product + outlet master blocks. |
| DailySales | Mixed | SalesTransaction, SalesTransactionFinancials | A-AF is transaction source; AH-AR is a summary block. |
| F_U | Derived | Outlet | Customer totals by unit. |
| WS_Van | Derived | Route/Team | Team totals by unit. |
| Follow Up | Derived | Targets/Follow-Up | Performance/target layout with many PKT/BOT/LIT blocks. |
| WS_Semi | Derived | Targets/Follow-Up | Monthly averages by customer. |
| Cons% | Derived | Targets/Follow-Up | Contribution % by customer. |
| Yaung Chi Oo | Derived | Salesperson summary | PKT/BOT blocks by month. |
| Ma Thida Oo | Derived | Salesperson summary | PKT/BOT blocks by month. |
| Hein Min Thu | Derived | Salesperson summary | PKT/BOT blocks by month. |
| Ko Htoo Zaw | Derived | Salesperson summary | PKT/BOT blocks by month. |
| Pyae Sone Shin | Derived | Salesperson summary | PKT/BOT blocks by month. |

**Keng Tung - Jan New Update.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| Outlet Summary | Derived | Route | A/B/C/D/S counts by route. |
| Outlet List | Source | Outlet, Township, Route | Master outlet list with way/agent/phone. |
| Way Plan | Source | PJP Plan, Route | Route plan by date. Multiple van blocks. |
| 8-Van Wise SKU | Derived | Route, Product | Route performance by SKU. |
| 8-Van Wise SKU(Jan-26) | Derived | Route, Product | Route performance by SKU with conversion factors. |
| PJP Outlets Van 1 | Mixed | PJP Plan, Outlet | Route totals + embedded outlet list. |
| PJP Outlets Van 2 | Mixed | PJP Plan, Outlet | Route totals + embedded outlet list. |
| PJP Outlets Van 3 | Mixed | PJP Plan, Outlet | Route totals + embedded outlet list. |

**LSH Feb PJP.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| Outlet Summary | Derived | Route | A/B/C/D/S counts by route. |
| Way Play(Feb) | Source | PJP Plan, Route | Route plan by date. |
| Outlet List | Source | Outlet, Township, Route | Master outlet list. |
| 1-Van Wise SKU(Feb) | Derived | Route, Product | Route performance by SKU. |
| PJP Outlets Plan 2 | Mixed | PJP Plan, Outlet | Route totals + embedded outlet list. |
| Van(2) | Derived | Route | Duplicate of Way Play summary. |

**MHL 2026 Feb.xlsx**

| Sheet | Classification | Primary entities | Notes |
| --- | --- | --- | --- |
| 7-MTL | Derived | Product | SKU summary by month. |
| Business Summary | Derived | Targets/Follow-Up | Target totals by month. |
| Ws Semi Ws | Derived | Outlet, Township | Individual sales report. |
| Final MTL SKU Wise | Derived | Product | SKU summary by month with ranking. |
| MTL Individual | Derived | Outlet, Township | Individual sales report. |
| MTL SKU Analysis | Derived | Product | SKU summary by month. |
| Township wise Analysis | Derived | Township | Bottle/Liter by month. |
| Final Town SKU wise Analysis | Derived | Product, Township | Matrix of township x product. |
| Outlet Summary | Derived | Route | A/B/C/D/S counts by route. |
| Outlet List | Source | Outlet, Township, Route | Master outlet list. |
| Way Plan | Source | PJP Plan, Route | Route plan by date. |
| 3-Van Wise SKU | Derived | Route, Product | Route performance by SKU. |
| Competition Information | Source | CompetitionEntry | Competition pricing data. |
| Top 3 or 4 brands in Township | Derived | Product, Township | Brand ranking report. |
| Meiktila | Derived | Product, Township | Township detail by product x month. |
| Tharzi | Derived | Product, Township | Township detail by product x month. |
| Pyawbwe | Derived | Product, Township | Township detail by product x month. |
| Wantwin | Derived | Product, Township | Township detail by product x month. |
| Mahlaing | Derived | Product, Township | Township detail by product x month. |
| Yamethin | Derived | Product, Township | Township detail by product x month. |
| Kyaukpandaung | Derived | Product, Township | Township detail by product x month. |
| Taungthar | Derived | Product, Township | Township detail by product x month. |
| Myingan | Derived | Product, Township | Township detail by product x month. |
| Bagan | Derived | Product, Township | Township detail by product x month. |
| Pakokku | Derived | Product, Township | Township detail by product x month. |
