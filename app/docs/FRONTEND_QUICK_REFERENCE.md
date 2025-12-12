# Product Model Changes - Quick Reference

## TL;DR

1. **`colors` → `color`**: Single string, not comma-separated
2. **New `size`**: String (e.g., "8.5", "M", "10x12")
3. **New `po_score`**: Number (0-100, initially null)

## JSON Response Example

### Before:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Running Shoes",
  "colors": "Red, Blue, Green",
  "price": 99.99
}
```

### After:
```json
{
  "id": "507f1f77bcf86cd799439011",
  "name": "Running Shoes",
  "color": "Red",
  "size": "8.5",
  "po_score": 85.5,
  "price": 99.99
}
```

## TypeScript Interface

```typescript
interface Product {
  id: string;
  catalog_id: string;
  line_item_id: string;
  name: string;
  description?: string;
  category?: string;
  brand?: string;
  sku?: string;
  upc?: string;
  price?: number;
  currency: string;
  quantity?: number;
  unit?: string;
  main_image?: string;
  images?: string[];
  color?: string;        // ⚠️ Changed from colors
  size?: string;         // ✨ New
  enrichment_status: string;
  po_score?: number;     // ✨ New
  enriched_at?: string;
  created_at: string;
  updated_at: string;
}
```

## Quick Fixes

### 1. Color Display
```typescript
// ❌ OLD
{product.colors?.split(',').map(c => <Badge>{c.trim()}</Badge>)}

// ✅ NEW
{product.color && <Badge>{product.color}</Badge>}
```

### 2. Size Display
```typescript
// ✅ NEW
{product.size && <span>Size: {product.size}</span>}
```

### 3. PO Score Display
```typescript
// ✅ NEW
{product.po_score != null && (
  <div>Score: {product.po_score}</div>
)}
```

## Find & Replace

Search your codebase for:
- `product.colors` → `product.color`
- `product?.colors` → `product?.color`
- `colors:` → `color:`
- `.colors` → `.color`

Then add:
- `product.size`
- `product.po_score`

---

See `FRONTEND_PRODUCT_MODEL_CHANGES.md` for full details.




