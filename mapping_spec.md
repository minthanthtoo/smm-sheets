# SMM App Mapping Spec (v1)

This mapping spec is derived from the Excel files in `/Users/min/codex/SMM-sheets/files/` and groups them by sheet type. It defines canonical fields, how sheets map to them, and how records should match across sheets.

## Canonical Entities

1. Region
- region_id (string, e.g., MTL, MLM, LSO, KT, LSH)
- region_name

2. Township
- township_id (normalized string)
- township_name
- township_name_en
- region_id

3. Outlet (Customer)
- outlet_id (generated)
- outlet_code (legacy No/Sr if present)
- outlet_name_mm (Burmese name if present)
- outlet_name_en (English name if present)
- township_id
- outlet_type (Wholesale, Semi-Wholesale, Vansales, etc.)
- address_full
- way_code (raw way/route text if present)
- contact_name_mm
- contact_name_en
- contact_phone
- responsible_person
- agent_name
- category (A/B/C/D/S) if present
- notes

4. Product (SKU)
- product_id (Stock ID if present)
- product_name
- ml
- packing
- unit_type (e.g., bottle/can descriptor, often Burmese)
- sales_price
- brand
- category

5. Route (Way) / Van
- route_id (region_id + van + way)
- van_id (Van 1, Van 2, etc.)
- way_code (W-1, Van 2-1, etc.)
- route_name (Actual Way Name)
- township_id

6. Sales Transaction
- txn_id
- date
- outlet_id
- product_id
- channel (WholeSales, Contract, Van, etc.)
- voucher_no
- car_no
- day_label (Today)
- period
- sale_type_raw (Particular in DailySales)
- outlet_name_raw
- township_name_raw
- address_raw
- qty_pack
- qty_bottle
- qty_liter
- customer_id_raw (CustomerID if present)
- stock_name_raw
- ml_raw
- packing_raw
- sale_class_raw (BE/Whisky/Column1 if present)
- participation_raw (ပါဝင်မှု)
- parking_fee

7. Sales Transaction Financials (optional)
- txn_id
- unit_rate (နှုံး)
- gross_amount (သင့်ငွေ)
- opening_balance (စာရင်းဖွင့်)
- old_price_discount (ဈေးဟောင်းလျှော့)
- commission (ကော်မရှင်)
- discount (ဈေးလျှော့)
- transport_discount (ကားခလျှော့)
- transport_add (ကားခ+)
- payment_date_1 (ငွေရသည့်နေ့)
- receivable_1 (ကြွေးရငွေ)
- payment_date_2 (ငွေရသည့်နေ့(၂))
- receivable_2 (ကြွေးရငွေ2)
- payment_date_3 (ငွေရသည့်နေ့(၃))
- receivable_3 (ကြွေးရငွေ3)
- payment_date_4 (ငွေရသည့်နေ့ ၄)
- receivable_4 (ကြွေးရငွေ4)
- outstanding_balance (အကြွေးကျန်2)

8. PJP Plan (Route Plan)
- plan_id
- date
- route_id
- planned_outlets_by_category (A/B/C/D/S)
- total_planned

9. Competition Entry
- competition_id
- region_id
- township_id
- company_name
- distributor_name
- product_name
- size_ml
- packing
- landing_price
- selling_price
- margin
- freight_cost
- promo_cost
- notes

10. Targets / Follow-Up (optional)
- target_id
- outlet_id
- year
- month
- target_value
- follow_up_notes

---

## Sheet Type Mapping

### A) Individual Sales
Examples: `*Individual Sales*.xlsx`

Columns (typical):
- No
- Customer Names (often two columns: Burmese + English)
- Township (Area) (often two columns: Burmese + English)
- Type (WS, SWS, Van, etc.)
- Contact Name (often two columns: Burmese + English)
- Contact No.
- Responsible by
- Month columns with subheaders: PKT, BOT, LIT

Mapping:
- Customer Names -> Outlet.outlet_name_mm/outlet_name_en
- Township (Area) -> Township.township_name
- Type -> Outlet.outlet_type
- Contact Name -> Outlet.contact_name_mm/contact_name_en
- Contact No. -> Outlet.contact_phone
- Responsible by -> Outlet.responsible_person
- Month + PKT/BOT/LIT -> Derived Report from Sales Transaction

Matching/Join logic:
- Outlet match on normalized outlet name + township + phone (if present).
- Derived by aggregating Sales Transaction grouped by outlet_id + month + measure.


### B) SKU Summary
Examples: `*SKU Summary*.xlsx`

Columns:
- Sr.
- Product Name
- Ranking
- ML
- Packing
- Sales Price
- Month columns with subheaders: Bot, Lit

Mapping:
- Product Name -> Product.product_name
- ML -> Product.ml
- Packing -> Product.packing
- Sales Price -> Product.sales_price
- Month Bot/Lit -> Derived Report from Sales Transaction grouped by product_id + month

Matching:
- Prefer Stock ID if product master is available; else normalize name + ml + packing.


### C) Township Summary (Monthly Bottle/Liter)
Examples: `*Township Summary*.xlsx`

Columns:
- No
- Township
- Month columns with subheaders: Bottle, Liter

Mapping:
- Township -> Township.township_name
- Month Bottle/Liter -> Derived Report from Sales Transaction grouped by township_id + month


### D) Township Sales Detail (Product by Month)
Examples: township-specific sheets within Township Summary workbooks, or `MHL 2026 Feb.xlsx`

Columns:
- Sr
- Product Name
- ML
- Packing
- Month columns with subheaders: PK, Bottle, Liter

Mapping:
- Product -> Product.product_name/ml/packing
- Township -> inferred from sheet title (e.g., "Meiktila", "Hpa-An")
- Month PK/Bottle/Liter -> Derived Report from Sales Transaction grouped by township_id + product_id + month


### E) Table (Master Data)
Examples: `*Table and DailySales*.xlsx` (Table sheet)

Common blocks in sheet:
- Product list: Stock ID, Particular, ml, Qty, Sales Price
- Outlet list: No, Merchant name, Address, Township, Sales channel, Car No., PG Name

Mapping:
- Stock ID -> Product.product_id
- Particular -> Product.product_name
- ml -> Product.ml
- Qty -> Product.packing (convert to pack size)
- Sales Price -> Product.sales_price

- Merchant name -> Outlet.outlet_name_mm/outlet_name_en
- Address -> Outlet.address
- Township -> Township.township_name
- Sales -> Outlet.outlet_type or channel
- Car No. -> Route/Van reference

Matching:
- Product master should be created from Stock ID.
- Outlet master should be created from name + township + phone (if present).


### F) DailySales (Transactions)
Examples: `*Table and DailySales*.xlsx` (DailySales sheet)

Columns (typical):
- Year, Month, Date, Today, Period
- VoucherNo, CarNo
- CustomerID / Customer Name
- Township
- Sales/WholeSales
- Particular (sale type)
- StockID, StockName, ML, Packing
- Bottle, SalesPK (sometimes)

Mapping:
- Date -> Sales Transaction.date
- VoucherNo -> Sales Transaction.voucher_no
- CarNo -> Sales Transaction.car_no
- CustomerID/Name -> Outlet match
- Township -> Township match
- StockID/StockName/ML -> Product match
- Bottle/SalesPK -> qty_bottle / qty_pack / qty_liter
- Sales/WholeSales -> Sales Transaction.channel

Matching:
- Outlet match by name + township (use phone when available).
- Product match by StockID, else by name + ml + packing.


### G) Outlet Summary
Examples: `Outlet Summary` sheets

Columns:
- Way, Route Name, Number of Outlets
- Subcolumns A/B/C/D/S + Total

Mapping:
- Way/Route -> Route.route_id
- Category counts -> Derived from Outlet.category by route_id


### H) Outlet List
Examples: `Outlet List` sheets

Columns:
- Sr, Outlet Name, TYPE, Address, Township, Way, Phone, Agent, Capital/Notes

Mapping:
- Outlet Name -> Outlet.outlet_name_mm/en
- TYPE -> Outlet.outlet_type
- Address -> Outlet.address
- Township -> Township
- Way -> Route
- Phone -> Outlet.contact_phone
- Agent -> Outlet.agent_name
- Capital/Notes -> Outlet.notes

Matching:
- This is primary source for Outlet master.


### I) Way Plan / Route Plan
Examples: `Way Plan` or `Way Play` sheets

Columns:
- Date, Day, Way, Actual Way Name
- A/B/C/D/S/Total

Mapping:
- Date -> PJP Plan.date
- Way + Actual Way Name -> Route
- A/B/C/D/S -> planned outlets by category


### J) Van Wise SKU
Examples: `Van Wise SKU` sheets

Columns:
- Region, Township, Way, Actual Route Name
- Total Working Day, Call Plan, Visit Call, Effective Call %
- SKU columns with Bot/Liter

Mapping:
- Route -> Route.route_id
- Calls -> Route performance metrics
- SKU Bot/Liter -> Derived from Sales Transaction filtered by route + product


### K) PJP Outlets Plan
Examples: `PJP Outlets` sheets

Columns:
- Route Name, Number of Outlets, A/B/C/D/S
- Embedded outlet lists by route

Mapping:
- Route -> Route.route_id
- Category counts -> Planned or actual outlets
- Outlet list -> Outlet master + route assignment


### L) Competition Information
Examples: `Competition Information` sheet

Columns:
- Region, Town, Company Name, Distributor, Township
- Product Name, Size/ML, Packing Size
- Buying Price, Selling Price, Promotions, Margin

Mapping:
- Region/Township -> CompetitionEntry.region_id/township_id
- Product -> CompetitionEntry.product_name
- Price fields -> CompetitionEntry.landing_price/selling_price/margin


### M) WS_Semi, Cons%, Follow Up
These are derived performance/target views.

Mapping:
- Customer + month -> aggregate from transactions
- Contribution % -> computed from yearly totals
- Follow Up -> optional target/notes table

---

## Matching & Normalization Rules

1. Names
- Normalize: trim, collapse spaces, case-fold English.
- Maintain both Burmese and English fields when both appear.

2. Township
- Build a canonical township dictionary per region.
- Use normalized township as foreign key.

3. Product
- Primary key: Stock ID when available.
- Fallback: product_name + ml + packing.

4. Units
- Enforce single standard: pack, bottle, liter.
- Store conversions in Product (pack_size, ml_per_bottle).

5. Dates
- Convert Excel date serials to ISO date.
- Store month as YYYY-MM for aggregation.

---

## Derived Reports to Generate in App

- Individual Sales (by outlet, by month)
- SKU Summary (by product, by month)
- Township Summary (by township, by month)
- Township Sales Detail (product x township x month)
- Van Wise SKU (route x product x month)
- Outlet Summary (route x outlet category)
- WS_Semi / Cons% (customer contribution and averages)

## Exact Field Mappings Per Sheet (v1)

Conventions:
- Row numbers are 1-based Excel rows.
- “Month block” = a month label in the header row with PKT/BOT/LIT or Bottle/Liter subheaders in the next row.
- “Derived” = formula/report sheet; not ingested as a primary source (use for validation/report parity).

### 10-LSO_Individual_Sales 28.2.2026.xlsx
**Sheet: 7-Individual Sales** (Derived + outlet master hints)
Header layout: Row 2 has metadata and month labels (January-2024 through Oct-2024). Row 3 has PKT/BOT per month.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | No | Outlet.outlet_code | Legacy row number |
| B | Customer Names | Outlet.outlet_name_mm | Burmese name |
| C | (blank) | Outlet.outlet_name_en | English name values present |
| D | Township (Area) | Township.township_name | Burmese name |
| E | (blank) | Township.township_name_en | English name values present |
| F | Type | Outlet.outlet_type | WS/SWS/Van |
| G | Contact Name | Outlet.contact_name_mm | Burmese name |
| H | (blank) | Outlet.contact_name_en | English name values present |
| I | Contact No. | Outlet.contact_phone |  |
| J | Responsible by | Outlet.responsible_person |  |
| K..AC | Month block | Derived monthly totals | PKT -> qty_pack, BOT -> qty_bottle |

### 13-KT Individual Sales_1.xlsx
**Sheet: 7. Individual Sales** (Derived + outlet master hints)
Header layout: Row 2 has metadata and month labels (January-2024 through July-2024). Row 3 has PKT/BOT/LIT per month.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | No | Outlet.outlet_code | Legacy row number |
| B | Customer Names | Outlet.outlet_name_mm | Burmese name |
| C | (blank) | Outlet.outlet_name_en | English name values present |
| D | Township (Area) | Township.township_name | Burmese name |
| E | (blank) | Township.township_name_en | English name values present |
| F | Type | Outlet.outlet_type | WS/SWS/Van |
| G | Contact Name | Outlet.contact_name_mm | Burmese name |
| H | (blank) | Outlet.contact_name_en | English name values present |
| I | Contact No. | Outlet.contact_phone |  |
| J | Responsible by | Outlet.responsible_person |  |
| K..AC | Month block | Derived monthly totals | PKT -> qty_pack, BOT -> qty_bottle, LIT -> qty_liter |

### 7-MTL Individual Sale_2.xlsx
**Sheet: 7- Individual Sales** (Derived + outlet master hints)
Header layout: Row 2 holds month dates (2024-01-01 through 2024-12-01). Row 3 has metadata + PKT/BOT per month.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | Sr.No | Outlet.outlet_code | Legacy row number |
| B | Customer Name | Outlet.outlet_name_mm | Burmese name |
| C | (blank) | Outlet.outlet_name_en | English name values present |
| D | Area | Township.township_name | Burmese name |
| E | (blank) | Township.township_name_en | English name values present |
| F | Outlet Type | Outlet.outlet_type |  |
| G..AC | Month block | Derived monthly totals | PKT -> qty_pack, BOT -> qty_bottle |

### 7-MTL SKU Summary_4.xlsx
**Sheet: 7-MTL** (Derived SKU summary)
Header layout: Row 2 has product fields and month dates (2022-01-01 through 2022-06-01). Row 3 has Bot/Lit per month.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | Sr. | (row number) | Not stored |
| B | Product Name | Product.product_name |  |
| C | (blank) | Product.unit_type | Burmese unit/descriptor in many rows |
| D | Ranking | (derived) | Report-only |
| E | ML | Product.ml |  |
| F | Packing | Product.packing |  |
| G | Sales Price | Product.sales_price |  |
| H..S | Month block | Derived monthly totals | Bot -> qty_bottle, Lit -> qty_liter |

### 7-MTL for Table and DailySales(2026 Jan to Mar).xlsx
**Sheet: Table** (Source: Product master + Outlet master)
Header layout: single header row with three blocks.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | Stock ID | Product.product_id | Product block 1 |
| B | Particular | Product.product_name |  |
| C | ml | Product.ml |  |
| D | Qty | Product.packing | Pack size |
| E | Column1 | Product.category | Raw/unknown, keep as product.category if used |
| F | Sales Price | Product.sales_price |  |
| H | No | Outlet.outlet_code | Outlet block |
| I | ကုန်သည် | Outlet.outlet_name_mm |  |
| J | လိပ်စာ | Outlet.address_full |  |
| K | Township | Township.township_name |  |
| L | Sales | Outlet.outlet_type | Channel/Type |
| N | Particular | Outlet.notes | Raw/unknown in outlet block |
| P | Car No. | Route.van_id or Outlet.way_code | If used for route assignment |
| R | PG Name | Outlet.responsible_person |  |
| T | Stock ID | Product.product_id | Product block 2 |
| U | Particular | Product.product_name |  |
| V | ml | Product.ml |  |
| W | Qty | Product.packing |  |
| X | Column1 | Product.category | Raw/unknown, keep as product.category if used |
| Y | Sales Price | Product.sales_price |  |

**Sheet: DailySales** (Source: Sales transactions)
Header layout: single header row, columns A through AN.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | Year | SalesTransaction.date | Combine with Month + Date |
| B | Month | SalesTransaction.date |  |
| C | Date | SalesTransaction.date |  |
| D | Today | SalesTransaction.day_label | Raw day label |
| E | Period | SalesTransaction.period |  |
| F | BE/Whisky | SalesTransaction.sale_class_raw | Raw category |
| G | VoucherNo | SalesTransaction.voucher_no |  |
| H | CarNo | SalesTransaction.car_no |  |
| I | CustomerID | SalesTransaction.customer_id_raw |  |
| J | ကုန်သည်အမည် | SalesTransaction.outlet_name_raw | Match to Outlet |
| K | Township | SalesTransaction.township_name_raw | Match to Township |
| L | လိပ်စာ | SalesTransaction.address_raw | Match to Outlet |
| M | Sales | SalesTransaction.channel |  |
| N | Particular | SalesTransaction.sale_type_raw | Raw sale type |
| O | StockID | SalesTransaction.product_id | Match to Product |
| P | StockName | SalesTransaction.stock_name_raw |  |
| Q | ML | SalesTransaction.ml_raw |  |
| R | ပါဝင်မှု | SalesTransaction.participation_raw |  |
| S | bottle | SalesTransaction.qty_bottle | Raw bottle count |
| T | Parking | SalesTransaction.parking_fee |  |
| U | SalesPK | SalesTransaction.qty_pack |  |
| V | SalesBot | SalesTransaction.qty_bottle |  |
| W | Liter | SalesTransaction.qty_liter |  |
| X | နှုံး | SalesTransactionFinancials.unit_rate |  |
| Y | သင့်ငွေ | SalesTransactionFinancials.gross_amount |  |
| Z | စာရင်းဖွင့် | SalesTransactionFinancials.opening_balance |  |
| AA | ဈေးဟောင်းလျှော့ | SalesTransactionFinancials.old_price_discount |  |
| AB | ‌ကော်မရှင် | SalesTransactionFinancials.commission |  |
| AC | ‌ဈေးလျှော့ | SalesTransactionFinancials.discount |  |
| AD | ကားခလျှော့ | SalesTransactionFinancials.transport_discount |  |
| AE | ကားခ+ | SalesTransactionFinancials.transport_add |  |
| AF | ငွေရသည့်နေ့ | SalesTransactionFinancials.payment_date_1 |  |
| AG | ကြွေးရငွေ | SalesTransactionFinancials.receivable_1 |  |
| AH | ငွေရသည့်နေ့(၂) | SalesTransactionFinancials.payment_date_2 |  |
| AI | ကြွေးရငွေ2 | SalesTransactionFinancials.receivable_2 |  |
| AJ | ငွေရသည့်နေ့(၃) | SalesTransactionFinancials.payment_date_3 |  |
| AK | ကြွေးရငွေ3 | SalesTransactionFinancials.receivable_3 |  |
| AL | ငွေရသည့်နေ့ ၄ | SalesTransactionFinancials.payment_date_4 |  |
| AM | ကြွေးရငွေ4 | SalesTransactionFinancials.receivable_4 |  |
| AN | အကြွေးကျန်2 | SalesTransactionFinancials.outstanding_balance |  |

**Sheet: Sheet1** (Derived targets)
Header layout: Row 3 has Target, Sale, Ach% repeating blocks.
Mapping: Target/Sale/Ach% -> Targets/Follow-Up (optional), not a primary source.

### 7-MTL for Township Summary_4.xlsx
**Sheet: 7-MTL** (Derived township summary)
Header layout: Row 2 has No, TownShip, Van + month dates; Row 3 has Bottle/Liter. Multiple blocks exist in the same sheet (region summary + market summary).
Mapping: Derived from township detail sheets; do not ingest as source.

**Sheets: Meiktila, Tharzi, Pyaw Bwe, Want Twin, Mahaling, Yamethin, Kyaukpadaung, Taungthar, Myingyan, Bagan, Pakokku** (Derived township detail)
Header layout: Row 2 has Sr, Product Name, Ml, Packing + month dates; Row 3 has PK/Bottle/Liter.
Mapping: Product fields -> Product; township inferred from sheet name; month block -> derived totals (PK -> qty_pack, Bottle -> qty_bottle, Liter -> qty_liter).

### 7-MTL for Township Summary_4_1.xlsx
All sheets are structural duplicates of `7-MTL for Township Summary_4.xlsx`. Use identical mappings for each sheet.

### 9-MLM Individual Sales.xlsx
**Sheet: 7-Individual Sales** (Derived + outlet master hints)
Header layout: Row 2 has metadata and month labels (January-2024 through July-2024). Row 3 has PKT/BOT/Liter per month.
Mapping: Same as LSO/KT individual sales, with Liter -> qty_liter.

**Sheet: Sheet1** (Empty/unused)
Mapping: No ingestion.

### 9-MLM SKU Summary_4.xlsx
**Sheet: 9-MLM (SKU)** (Derived SKU summary)
Header layout: Row 2 has product fields and month dates (2022-01-01 through 2022-06-01). Row 3 has Bot/Lit per month.
Mapping: Same as `7-MTL SKU Summary_4.xlsx`.

### 9-MLM TOWNSHIP SUMMARY_1.xlsx
**Sheet: 4-Township Summary** (Derived township summary)
Header layout: Row 2 has No, TownShip + month dates; Row 3 has Bottle/Liter.
Mapping: Derived from township detail sheets; do not ingest as source.

**Sheet: 4--Township summary** (Derived township summary variant)
Header layout: Row 2 has No, TownShip, Van, 2024 Average, and a 2025 report block. Row 4 has BT/Liter subheaders.
Mapping: Derived report only; not ingested.

**Sheets: 4-MawLaMyaing, 4-Hpa-An, 4-Paung, 4-Mu Don, 4-ThaHtone, 4-KawKariek, 4-Yaye, 4-Phar Pon, 4-Bagoda-3, 4-Chang Sone, 4-Than Phyu Zayat, Thein ZatYat** (Derived township detail)
Header layout: Row 3 has Sr/Product/Ml/Packing + month names (January, February, etc). Row 4 has Pk/BT/Liter.
Mapping: Product fields -> Product; township inferred from sheet name; month block -> derived totals (PK -> qty_pack, BT -> qty_bottle, Liter -> qty_liter).

### 9-MLM Table and DailySales-2026_Feb.xlsx
**Sheet: Table** (Source: Product master + Outlet master)
Header layout: single header row with two blocks.

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | Stock ID | Product.product_id | Product block |
| B | Particular | Product.product_name |  |
| C | ml | Product.ml |  |
| D | Qty | Product.packing |  |
| E | Column1 | Product.category | Raw/unknown |
| F | Sales Price | Product.sales_price |  |
| I | No | Outlet.outlet_code | Outlet block |
| J | ကုန်သည် | Outlet.outlet_name_mm |  |
| K | လိပ်စာ | Outlet.address_full |  |
| L | Township | Township.township_name |  |
| M | Sales | Outlet.outlet_type | Channel/Type |
| O | Particular | Outlet.notes | Raw/unknown in outlet block |
| Q | Car No | Route.van_id or Outlet.way_code | If used for route assignment |

**Sheet: DailySales** (Source: Sales transactions + appended summary block)
Header layout: single header row with primary block A-AF and secondary block AH-AR.

Primary block (A-AF) mapping:

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| A | Year | SalesTransaction.date | Combine with Month + Date |
| B | Month | SalesTransaction.date |  |
| C | Date | SalesTransaction.date |  |
| D | Today | SalesTransaction.day_label |  |
| E | Period | SalesTransaction.period |  |
| F | Column1 | SalesTransaction.sale_class_raw | Raw category |
| G | VoucherNo | SalesTransaction.voucher_no |  |
| H | CarNo | SalesTransaction.car_no |  |
| I | CustomerID | SalesTransaction.customer_id_raw |  |
| J | ကုန်သည်အမည် | SalesTransaction.outlet_name_raw | Match to Outlet |
| K | Township | SalesTransaction.township_name_raw | Match to Township |
| L | WholeSales | SalesTransaction.channel |  |
| M | Particular | SalesTransaction.sale_type_raw |  |
| N | StockID | SalesTransaction.product_id | Match to Product |
| O | StockName | SalesTransaction.stock_name_raw |  |
| P | ML | SalesTransaction.ml_raw |  |
| Q | ပါဝင်မှု | SalesTransaction.participation_raw |  |
| R | Bottle | SalesTransaction.qty_bottle | Raw bottle count |
| S | Parking | SalesTransaction.parking_fee |  |
| T | SalesPK | SalesTransaction.qty_pack |  |
| U | SalesBot | SalesTransaction.qty_bottle |  |
| V | Liter | SalesTransaction.qty_liter |  |
| W | နှုံး | SalesTransactionFinancials.unit_rate |  |
| X | သင့်ငွေ | SalesTransactionFinancials.gross_amount |  |
| Y | စာရင်းဖွင့် | SalesTransactionFinancials.opening_balance |  |
| Z | ဈေးဟောင်းလျှော့ | SalesTransactionFinancials.old_price_discount |  |
| AA | ‌ကော်မရှင် | SalesTransactionFinancials.commission |  |
| AB | ငွေရသည့်နေ့ | SalesTransactionFinancials.payment_date_1 |  |
| AC | ကြွေးရငွေ | SalesTransactionFinancials.receivable_1 |  |
| AD | ငွေရသည့်နေ့(၂) | SalesTransactionFinancials.payment_date_2 |  |
| AE | ကြွေးရငွေ2 | SalesTransactionFinancials.receivable_2 |  |
| AF | အကြွေးကျန်2 | SalesTransactionFinancials.outstanding_balance |  |

Secondary block (AH-AR) mapping:

| Column | Header | Canonical field | Notes |
| --- | --- | --- | --- |
| AH | Date | (derived) | Summary block, not ingested as transactions |
| AI | Month | (derived) |  |
| AJ | Year | (derived) |  |
| AK | Customer Name | Outlet.outlet_name_raw | If used as summary by customer |
| AL | Township | Township.township_name_raw |  |
| AM | Team | Route.van_id or Team | Summary by team |
| AN | Particular | SalesTransaction.sale_type_raw |  |
| AO | Stock Name | Product.product_name |  |
| AP | Sales Ctns | qty_pack |  |
| AQ | Sales Bot; | qty_bottle |  |
| AR | Sales Liter | qty_liter |  |

**Sheet: F_U** (Derived customer totals)
Header layout: Row 9.
Mapping: Customer Name -> Outlet; Sum of Sales Liter/Bot/Ctns -> derived totals.

**Sheet: WS_Van** (Derived team totals)
Header layout: Row 9.
Mapping: Team -> Route.van_id; Sum of Sales Liter/Bot/Ctns -> derived totals.

**Sheet: Follow Up** (Derived performance/targets)
Header layout: Row 17, then repeated PKT/Bottle/Liter blocks across columns.
Mapping: Sr No., Customer Name, Area, Outlet Type, Cons%, Resp by -> Targets/Follow-Up optional table; remaining PKT/Bottle/Liter blocks are derived monthly/product totals.

**Sheet: WS_Semi** (Derived customer averages)
Header layout: Row 2.
Mapping: Customer Name -> Outlet; Jan-Dec + Total + AVG -> derived metrics (Targets/Follow-Up optional).

**Sheet: Cons%** (Derived contribution report)
Header layout: Row 3.
Mapping: Customer Name/Area/Channel -> Outlet; Jan-Dec + Yearly Total + AVG + Contribution% -> derived metrics.

**Sheets: Yaung Chi Oo, Ma Thida Oo, Hein Min Thu, Ko Htoo Zaw, Pyae Sone Shin** (Derived salesperson summaries)
Header layout: Row 4 with repeated PKT/BOT blocks; month labels appear above.
Mapping: Derived monthly totals by salesperson; not ingested as source.

### Keng Tung - Jan New Update.xlsx
**Sheet: Outlet Summary** (Derived route outlet counts)
Header layout: Row 2-3 define Way/Route Name with A/B/C/D/S + Total. Multiple Van blocks are side-by-side.
Mapping: Route.way_code + route_name; category counts -> derived from Outlet.category.

**Sheet: Outlet List** (Source: Outlet master)
Header layout: Row 5. Sheet contains repeated blocks horizontally.

| Header | Canonical field | Notes |
| --- | --- | --- |
| စဉ် / Sr | Outlet.outlet_code |  |
| ကုန်သည်အမည် / ဆိုင်အမည် | Outlet.outlet_name_mm |  |
| Type / TYPE | Outlet.outlet_type |  |
| လိပ်စာ အပြည့်အစုံ / လိပ်စာ | Outlet.address_full |  |
| Way | Outlet.way_code | Raw way/route |
| ဖုန်းနံပါတ် | Outlet.contact_phone |  |
| Agent | Outlet.agent_name |  |
| ရင်းနှီးမှု | Outlet.notes | Capital/notes |

**Sheet: Way Plan** (Source: Route plan)
Header layout: Row 2-3 define repeated blocks for Van 1, Van 2, Van 3 (No, Date, Actual Way, Day, Way, A/B/C/D/S, Total).
Mapping: Date -> PJP Plan.date; Way/Actual Way -> Route; A/B/C/D/S/Total -> planned outlets by category.

**Sheet: 8-Van Wise SKU** (Derived route + SKU performance)
Header layout: Row 2 has Region/Township/Way/Route + call metrics; product columns with Bot/Liter.
Mapping: Derived totals by route and product.

**Sheet: 8-Van Wise SKU(Jan-26)** (Derived route + SKU performance)
Header layout: Row 2 has Region/Township/Van + product columns; Row 3 contains bottle/liter conversion factors.
Mapping: Derived totals by route and product; use Product matches for each column header.

**Sheets: PJP Outlets Van 1, PJP Outlets Van 2, PJP Outlets Van 3** (Source: Route plan + Outlet lists)
Header layout: Left block has Route Name + A/B/C/D/S + Total. Right blocks embed outlet lists (Sr, ဆိုင်အမည်, TYPE, လိပ်စာ, ဖုန်းနံပါတ်, Agent, ရင်းနှီးမှု).
Mapping: Route -> PJP Plan; outlet list -> Outlet master + Route assignment.

### LSH Feb PJP.xlsx
**Sheet: Outlet Summary** (Derived route outlet counts)
Header layout: Row 2-3 define Way/Actual Way Name + A/B/C/D/S + Total.
Mapping: Derived from Outlet List / Route assignments.

**Sheet: Way Play(Feb)** (Source: Route plan)
Header layout: Row 3 (Date, Day, Way, Actual Way Name, A/B/C/D/S, Total).
Mapping: PJP Plan.

**Sheet: Outlet List** (Source: Outlet master)
Header layout: Row 3.

| Header | Canonical field | Notes |
| --- | --- | --- |
| Sr | Outlet.outlet_code |  |
| ဆိုင်အမည် | Outlet.outlet_name_mm |  |
| TYPE | Outlet.outlet_type |  |
| လိပ်စာ | Outlet.address_full |  |
| Township | Township.township_name |  |
| Way | Outlet.way_code |  |
| ဖုန်းနံပါတ် | Outlet.contact_phone |  |
| ဘယ်သူ့ Outletလဲ | Outlet.responsible_person |  |
| ရင်းနှီးမှု | Outlet.notes |  |

**Sheet: 1-Van Wise SKU(Feb)** (Derived route + SKU performance)
Header layout: Row 2 has Region/Township/Way + call metrics; product columns with Bot/Liter.
Mapping: Derived totals by route and product.

**Sheet: PJP Outlets Plan 2** (Source: Route plan + Outlet lists)
Header layout: Left block has Route Name + A/B/C/D/S + Total; right blocks embed outlet lists.
Mapping: Route -> PJP Plan; outlet list -> Outlet master + Route assignment.

**Sheet: Van(2)** (Derived route plan summary)
Header layout: Same as Way Play(Feb).
Mapping: Derived; not ingested as source.

### MHL 2026 Feb.xlsx
**Sheet: 7-MTL** (Derived SKU summary)
Header layout: Row 2 has Product Name/ML/Packing/Sales Price + month dates. Row 3 has Bot/Lit.
Mapping: Same as SKU Summary; derived from transactions.

**Sheet: Business Summary** (Derived targets/summary)
Header layout: Row 3 has months and totals; rows include Target (Bot/Liter) and contribution.
Mapping: Targets/Follow-Up optional; not a primary source.

**Sheet: Ws Semi Ws** (Derived individual sales)
Header layout: Row 2 has month dates; Row 3 has Sr.No/Customer/Area/Outlet Type + PKT/BOT blocks.
Mapping: Same as Individual Sales; derived totals.

**Sheet: Final MTL SKU Wise** (Derived SKU summary)
Header layout: Same pattern as SKU Summary with Ranking column.
Mapping: Derived.

**Sheet: MTL Individual** (Derived individual sales)
Header layout: Same pattern as Individual Sales (PKT/BOT blocks).
Mapping: Derived.

**Sheet: MTL SKU Analysis** (Derived SKU summary)
Header layout: Same pattern as SKU Summary without Ranking.
Mapping: Derived.

**Sheet: Township wise Analysis** (Derived township summary)
Header layout: Row 1 has No/TownShip; Row 2 has month dates; Row 3 has Bottle/Liter.
Mapping: Derived from township detail sheets.

**Sheet: Final Town SKU wise Analysis** (Derived township x product matrix)
Header layout: Row 1 has Product + township columns with 2025/2026 subcolumns.
Mapping: Derived; not ingested.

**Sheet: Outlet Summary** (Derived route outlet counts)
Header layout: Same pattern as other Outlet Summary sheets, multiple Van blocks side-by-side.
Mapping: Derived.

**Sheet: Outlet List** (Source: Outlet master)
Header layout: Row 3.
Mapping: Same as LSH Outlet List.

**Sheet: Way Plan** (Source: Route plan)
Header layout: Row 1 has Date/Day/Way/Actual Way Name + A/B/C/D/S + Total.
Mapping: PJP Plan.

**Sheet: 3-Van Wise SKU** (Derived route + SKU performance)
Header layout: Row 2 has Region/Township/Way + call metrics; product columns with Bot/Liter.
Mapping: Derived totals by route and product.

**Sheet: Competition Information** (Source: Competition entries)
Header layout: Row 2.

| Header | Canonical field | Notes |
| --- | --- | --- |
| Region | CompetitionEntry.region_id |  |
| Town | CompetitionEntry.township_id | Use township mapping |
| Company Name | CompetitionEntry.company_name |  |
| Distributor | CompetitionEntry.distributor_name |  |
| Township | CompetitionEntry.township_id |  |
| Product Name | CompetitionEntry.product_name |  |
| DB Landing Price | CompetitionEntry.landing_price |  |
| DB Selling Price | CompetitionEntry.selling_price |  |
| Selling- landing | CompetitionEntry.margin |  |
| Size/ ML | CompetitionEntry.size_ml |  |
| Packing Size | CompetitionEntry.packing |  |
| Buying Price | CompetitionEntry.landing_price | Raw field (if different) |
| Freight+Labour | CompetitionEntry.freight_cost |  |
| Trade promotion( If Any) | CompetitionEntry.promo_cost |  |
| Buying-(Freight+Promotion) | CompetitionEntry.landing_price | Computed |
| Selling price | CompetitionEntry.selling_price |  |

**Sheet: Top 3 or 4 brands in Township** (Derived brand ranking)
Header layout: Product + township columns with 2024/2025 subcolumns.
Mapping: Derived; not ingested.

**Sheets: Meiktila, Tharzi, Pyawbwe, Wantwin, Mahlaing, Yamethin, Kyaukpandaung, Taungthar, Myingan, Bagan, Pakokku** (Derived township detail)
Header layout: Row 3 has Sr/Product/Ml/Packing + month names; Row 4 has PK/Bottle/Liter.
Mapping: Product fields -> Product; township inferred from sheet name; month block -> derived totals.
