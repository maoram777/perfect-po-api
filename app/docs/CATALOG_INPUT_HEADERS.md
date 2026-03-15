# Catalog input file headers (CSV / Excel)

This document defines the column headers expected in catalog upload files (CSV or XLSX).  
The implementation lives in `app/constants/catalog_headers.py`.

---

## 405 response when headers are missing

If the file is missing any **required** column, the API returns **HTTP 405** with a JSON body so the client can show a clear error and list the missing columns.

**Response:** `405 Method Not Allowed`

**Body (application/json):**
```json
{
  "detail": {
    "message": "Missing required catalog column headers. Add the following columns to your file (or use an accepted alias).",
    "missing_headers": ["sku", "offer_price"]
  }
}
```

- `detail.message`: Human-readable message.
- `detail.missing_headers`: Array of **canonical** header names that are missing (e.g. `sku`, `upc`, `quantity`, `offer_price`). Use this list to tell the user which columns to add and to build a proper error message (e.g. “Your file is missing these required columns: sku, offer_price. Add a column with one of the accepted names.”).

---

## Required headers

Upload is **rejected with 405** if any of these are missing. Each can be provided under any of the listed aliases (case and spacing are normalized).

| Canonical name | Description | Example aliases |
|----------------|-------------|------------------|
| **sku** | Stock Keeping Unit / product code | `sku`, `SKU`, `Article Number`, `product_sku`, `item_sku`, `product_code`, `item_code` |
| **upc** | Universal Product Code / barcode / EAN | `upc`, `UPC`, `UPC Code`, `barcode`, `ean`, `product_upc`, `item_upc` |
| **quantity** | Available quantity / inventory | `quantity`, `Quantity`, `Inventory`, `Quantity Available`, `qty`, `stock`, `product_quantity`, `item_quantity` |
| **offer_price** | Selling/offer price (used for profit and PO score) | `offer_price`, `Offer Price`, `offer`, `Offer`, `Price`, `price`, `selling_price` |

---

## Optional headers

Used when present. No error if missing.

| Canonical name | Description | Example aliases |
|----------------|-------------|------------------|
| **whs** | Warehouse/cost price (for PO score) | `WHS`, `whs`, `Warehouse Price`, `warehouse_price`, `warehouse`, `cost_price` |
| **msrp** | Manufacturer Suggested Retail Price / RRP | `MSRP`, `msrp`, `RRP`, `rrp`, `Retail Price`, `retail_price`, `list_price`, `Original Price` |
| **name** | Product name / title | `name`, `Article Name`, `Style Name`, `product_name`, `item_name`, `title`, `product_title` |
| **description** | Product description | `description`, `Description`, `product_description`, `item_description` |
| **brand** | Brand / manufacturer | `brand`, `Brand`, `product_brand`, `item_brand`, `manufacturer`, `make` |
| **category** | Category / subcategory / division | `Category`, `Subcategory`, `Division`, `category`, `product_category`, `type`, `product_type` |
| **color** | Color | `color`, `Color`, `Colour`, `product_color`, `item_color` |
| **size** | Size | `size`, `Size`, `product_size`, `item_size` |
| **currency** | Currency code (default: USD) | `Currency`, `currency`, `product_currency`, `item_currency` |
| **unit** | Unit of measure (e.g. piece, case) | `unit`, `Unit`, `product_unit`, `item_unit`, `uom`, `measurement_unit` |

---

## Header matching rules

- Comparison is **case-insensitive** and ignores spaces and underscores (e.g. `Offer Price`, `offer_price`, and `offerprice` all match **offer_price**).
- For each required canonical name, the file must have **at least one** column that matches one of its aliases.
