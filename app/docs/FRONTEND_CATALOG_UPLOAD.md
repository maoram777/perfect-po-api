# Catalog upload – client implementation guide

This guide describes how to call the catalog upload API and how to handle the **405** response when required column headers are missing, so you can show a clear error and list missing columns to the user.

---

## Endpoint

**POST** `/catalogs/upload`  
Content-Type: `multipart/form-data`

**Form fields:**
- `file` (required): CSV or Excel file (`.csv`, `.xlsx`, `.xls`)
- `name` (required): Catalog name
- `description` (optional): Catalog description

**Success (200):**
```json
{
  "message": "Catalog file uploaded successfully",
  "catalog_id": "...",
  "filename": "products.csv",
  "total_items": 123
}
```

---

## Required columns and 405 response

The file **must** include a column for each of these (under any of the accepted names):

| Canonical name | Example accepted column names in file |
|----------------|--------------------------------------|
| `sku`          | sku, SKU, Article Number, product_sku, item_sku, product_code, item_code |
| `upc`          | upc, UPC, UPC Code, barcode, ean, product_upc, item_upc |
| `quantity`     | quantity, Quantity, Inventory, qty, stock, product_quantity, item_quantity |
| `offer_price`  | offer_price, Offer Price, offer, Offer, Price, price, selling_price |

If **any** of these are missing, the API returns **405 Method Not Allowed** with a body that lists exactly which required columns are missing.

---

## Handling 405 – missing headers

When the response status is **405**, the body is JSON with this shape:

```ts
// Response status: 405
interface MissingHeaders405 {
  detail: {
    message: string;
    missing_headers: string[];  // e.g. ["sku", "offer_price"]
  };
}
```

**Example response:**
```json
{
  "detail": {
    "message": "Missing required catalog column headers. Add the following columns to your file (or use an accepted alias).",
    "missing_headers": ["sku", "offer_price"]
  }
}
```

Use `detail.missing_headers` to:
1. Show the user which required columns are missing.
2. Build a short, clear error message (e.g. “Your file is missing these required columns: sku, offer_price.”).
3. Optionally link to documentation that lists accepted column names for each (see `CATALOG_INPUT_HEADERS.md` or API docs).

---

## Example: upload with error handling (TypeScript/React)

```typescript
interface UploadCatalogResponse {
  message: string;
  catalog_id: string;
  filename: string;
  total_items: number;
}

interface MissingHeadersDetail {
  message: string;
  missing_headers: string[];
}

async function uploadCatalog(
  file: File,
  name: string,
  description?: string
): Promise<UploadCatalogResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);
  if (description) formData.append('description', description);

  const response = await fetch('/catalogs/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
    body: formData,
  });

  const data = await response.json();

  if (response.status === 405) {
    const detail = data.detail as MissingHeadersDetail;
    const missing = detail?.missing_headers ?? [];
    const err = new Error(
      missing.length > 0
        ? `Missing required columns: ${missing.join(', ')}. Add these columns to your file.`
        : detail?.message ?? 'Catalog file is missing required column headers.'
    ) as Error & { missing_headers?: string[] };
    err.missing_headers = missing;
    throw err;
  }

  if (!response.ok) {
    throw new Error(data.detail ?? 'Upload failed');
  }

  return data as UploadCatalogResponse;
}
```

---

## Example: showing missing headers in the UI

```typescript
try {
  await uploadCatalog(file, name, description);
  showSuccess('Catalog uploaded successfully');
} catch (err) {
  const message = err instanceof Error ? err.message : 'Upload failed';
  const missing = (err as Error & { missing_headers?: string[] }).missing_headers;
  if (missing?.length) {
    showError(
      `Your file is missing these required columns: ${missing.join(', ')}. ` +
      `Please add a column for each (see accepted names in the upload help).`
    );
    setMissingHeaders(missing);  // e.g. to show a list or checklist in the UI
  } else {
    showError(message);
  }
}
```

---

## Summary

- **405** = one or more **required** column headers are missing.
- Response body: `detail.message` (string) and `detail.missing_headers` (array of canonical names).
- Use `missing_headers` to build a clear, user-facing error and to list exactly which columns to add.
- Full list of required/optional headers and accepted column names: see `CATALOG_INPUT_HEADERS.md` or the OpenAPI docs at `/docs`.
