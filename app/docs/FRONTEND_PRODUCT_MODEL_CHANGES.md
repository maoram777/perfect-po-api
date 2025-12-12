# Product Model Changes - Frontend Update Guide

## Overview
The Product model has been updated with the following changes:
1. **`colors` → `color`**: Changed from comma-separated string to single color value
2. **New `size` field**: Added to support product sizing (shoes, clothing, etc.)
3. **New `po_score` field**: Added for Purchase Order opportunity/deal quality scoring

## API Changes

### Product Response Structure

#### Before:
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
  colors?: string;  // ❌ REMOVED - comma-separated string
  enrichment_status: string;
  enriched_at?: string;
  created_at: string;
  updated_at: string;
}
```

#### After:
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
  color?: string;        // ✅ NEW - single color value (not array, not comma-separated)
  size?: string;         // ✅ NEW - size (e.g., "8.5" for shoes, "M" or "10x12" for clothing)
  enrichment_status: string;
  po_score?: number;     // ✅ NEW - Purchase Order score (0-100, calculated later)
  enriched_at?: string;
  created_at: string;
  updated_at: string;
}
```

## Field Details

### 1. `color` (replaces `colors`)

**Type:** `string | null | undefined`

**Description:** Single product color value. If multiple colors were previously stored, only the first/primary color is now returned.

**Migration:**
```typescript
// ❌ OLD - Don't use this anymore
const colors = product.colors; // "Red, Blue, Green"
const colorArray = colors?.split(',').map(c => c.trim());

// ✅ NEW - Use this
const color = product.color; // "Red"
```

**Example Values:**
- `"Red"`
- `"Blue"`
- `"Black"`
- `"Flame|Ivory"` (if Keepa returns combined colors)
- `null` or `undefined` (if not available)

### 2. `size` (new field)

**Type:** `string | null | undefined`

**Description:** Product size. Can be:
- **Shoes**: Numeric size (e.g., `"8.5"`, `"10"`, `"12.5"`)
- **Clothing**: Size code (e.g., `"M"`, `"L"`, `"XL"`) or dimensions (e.g., `"10x12"`)
- Extracted from Index column when available (e.g., `"3MD30090914 M 8.5"` → `"8.5"`)

**Example Values:**
- `"8.5"` (shoe size)
- `"M"` (clothing size)
- `"10x12"` (dimensions)
- `null` or `undefined` (if not available)

**Usage:**
```typescript
// Display size in UI
{product.size && (
  <span className="product-size">Size: {product.size}</span>
)}

// Filter by size
const filteredProducts = products.filter(p => p.size === selectedSize);
```

### 3. `po_score` (new field)

**Type:** `number | null | undefined`

**Description:** Purchase Order score representing opportunity/deal quality. This field will be calculated later by the backend. Initially, it will be `null` for all products.

**Range:** Expected to be 0-100 (or similar scale, TBD)

**Usage:**
```typescript
// Display PO score when available
{product.po_score !== null && product.po_score !== undefined && (
  <div className="po-score">
    <span>PO Score: {product.po_score}</span>
    <ProgressBar value={product.po_score} max={100} />
  </div>
)}

// Sort by PO score
const sortedProducts = [...products].sort((a, b) => {
  const scoreA = a.po_score ?? 0;
  const scoreB = b.po_score ?? 0;
  return scoreB - scoreA; // Descending order
});
```

## Required Frontend Updates

### 1. Update TypeScript Interfaces

```typescript
// Update your Product interface/type
interface Product {
  // ... existing fields ...
  color?: string;        // Changed from colors
  size?: string;         // New field
  po_score?: number;     // New field
  // ... rest of fields ...
}
```

### 2. Update Component Props

```typescript
// Before
interface ProductCardProps {
  product: {
    // ...
    colors?: string;
  };
}

// After
interface ProductCardProps {
  product: {
    // ...
    color?: string;
    size?: string;
    po_score?: number;
  };
}
```

### 3. Update Display Logic

```typescript
// ❌ OLD - Displaying multiple colors
{product.colors && (
  <div className="colors">
    {product.colors.split(',').map((color, idx) => (
      <span key={idx} className="color-badge">{color.trim()}</span>
    ))}
  </div>
)}

// ✅ NEW - Displaying single color
{product.color && (
  <div className="color">
    <span className="color-badge">{product.color}</span>
  </div>
)}

// ✅ NEW - Displaying size
{product.size && (
  <div className="size">
    <span>Size: {product.size}</span>
  </div>
)}
```

### 4. Update Forms/Inputs

```typescript
// ❌ OLD - Multiple colors input
<input 
  type="text" 
  value={product.colors || ''} 
  placeholder="Red, Blue, Green"
/>

// ✅ NEW - Single color input
<input 
  type="text" 
  value={product.color || ''} 
  placeholder="Red"
/>

// ✅ NEW - Size input
<input 
  type="text" 
  value={product.size || ''} 
  placeholder="8.5 or M"
/>
```

### 5. Update API Calls

No changes needed to API endpoints - the backend automatically returns the new structure. However, if you're sending product data:

```typescript
// ❌ OLD - Don't send colors
const productData = {
  // ...
  colors: "Red, Blue"
};

// ✅ NEW - Send color and size
const productData = {
  // ...
  color: "Red",
  size: "8.5"
};
```

### 6. Update Filters/Search

```typescript
// Update color filter
// ❌ OLD
const filterByColor = (products: Product[], color: string) => {
  return products.filter(p => 
    p.colors?.toLowerCase().includes(color.toLowerCase())
  );
};

// ✅ NEW
const filterByColor = (products: Product[], color: string) => {
  return products.filter(p => 
    p.color?.toLowerCase() === color.toLowerCase()
  );
};

// ✅ NEW - Size filter
const filterBySize = (products: Product[], size: string) => {
  return products.filter(p => p.size === size);
};
```

### 7. Update State Management

If you're using Redux, Zustand, or similar:

```typescript
// Update your state shape
interface ProductState {
  products: Product[]; // Now includes color, size, po_score
  // ...
}

// Update actions/reducers
const updateProduct = (product: Product) => {
  // Make sure to handle color, size, po_score
  return {
    ...product,
    color: product.color || null,
    size: product.size || null,
    po_score: product.po_score || null
  };
};
```

## Migration Checklist

- [ ] Update TypeScript interfaces/types for Product
- [ ] Replace all references to `colors` with `color`
- [ ] Update color display logic (remove comma-splitting)
- [ ] Add `size` field display in product cards/lists
- [ ] Add `po_score` field display (when available)
- [ ] Update product forms to use single color input
- [ ] Update filters to use `color` instead of `colors`
- [ ] Add size-based filtering if needed
- [ ] Update any product creation/editing forms
- [ ] Update API response handlers
- [ ] Test product display with new fields
- [ ] Update any product comparison/sorting logic
- [ ] Update documentation/comments

## Example Component Update

```typescript
// ProductCard.tsx - Example update
import React from 'react';

interface Product {
  id: string;
  name: string;
  color?: string;      // Changed from colors
  size?: string;        // New
  po_score?: number;    // New
  price?: number;
  main_image?: string;
  // ... other fields
}

const ProductCard: React.FC<{ product: Product }> = ({ product }) => {
  return (
    <div className="product-card">
      {product.main_image && (
        <img src={product.main_image} alt={product.name} />
      )}
      <h3>{product.name}</h3>
      
      {/* ✅ Updated color display */}
      {product.color && (
        <div className="product-color">
          <span className="label">Color:</span>
          <span className="value">{product.color}</span>
        </div>
      )}
      
      {/* ✅ New size display */}
      {product.size && (
        <div className="product-size">
          <span className="label">Size:</span>
          <span className="value">{product.size}</span>
        </div>
      )}
      
      {/* ✅ New PO score display */}
      {product.po_score !== null && product.po_score !== undefined && (
        <div className="product-po-score">
          <span className="label">PO Score:</span>
          <span className="value">{product.po_score.toFixed(1)}</span>
          <div className="score-bar">
            <div 
              className="score-fill" 
              style={{ width: `${product.po_score}%` }}
            />
          </div>
        </div>
      )}
      
      {product.price && (
        <div className="product-price">${product.price.toFixed(2)}</div>
      )}
    </div>
  );
};

export default ProductCard;
```

## API Endpoints Affected

All product-related endpoints now return the updated structure:

- `GET /products/` - List products
- `GET /products/{product_id}` - Get single product
- `GET /catalogs/{catalog_id}/products` - Get catalog products
- `POST /catalogs/{catalog_id}/enrich` - Enriched products (new structure)

## Backward Compatibility

⚠️ **Breaking Change**: This is a breaking change. The `colors` field will no longer be returned by the API. All frontend code using `colors` must be updated to use `color`.

## Questions or Issues?

If you encounter any issues or have questions about these changes, please contact the backend team.

---

**Last Updated:** November 9, 2025  
**API Version:** Current  
**Status:** ✅ Ready for implementation




