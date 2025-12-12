# Offer Generation Guide - Frontend Implementation

## Overview
This guide explains how to implement PO score calculation, MSRP validation, and optimal offer generation in the React frontend application.

## Table of Contents
1. [PO Score Calculation](#po-score-calculation)
2. [MSRP Validation](#msrp-validation)
3. [Optimal Offer Creation](#optimal-offer-creation)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [Example Implementation](#example-implementation)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## PO Score Calculation

### Overview
PO (Purchase Order) score represents the opportunity/deal quality. It's calculated based on:
- **WHS** (Warehouse Price)
- **MSRP** (Manufacturer Recommended Retail Price)
- **Offer Price**

Higher discount = Higher PO score (0-100 scale).

### Endpoints

#### 1. Calculate PO Scores for All Products
**Endpoint:** `POST /products/calculate-po-scores`

**Query Parameters:**
- `catalog_id` (optional): Filter by catalog ID

**Response:**
```typescript
{
  message: string;
  updated: number;      // Products with calculated scores
  skipped: number;     // Products that couldn't be calculated
  errors: number;       // Products with errors
  total_processed: number;
}
```

**Example:**
```typescript
// Calculate PO scores for all products in a catalog
const calculatePOScores = async (catalogId?: string) => {
  try {
    const params = catalogId ? `?catalog_id=${catalogId}` : '';
    const response = await fetch(`/api/products/calculate-po-scores${params}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to calculate PO scores');
    }
    
    const data = await response.json();
    console.log(`Updated: ${data.updated}, Skipped: ${data.skipped}`);
    return data;
  } catch (error) {
    console.error('Error calculating PO scores:', error);
    throw error;
  }
};
```

#### 2. Calculate PO Score for Single Product
**Endpoint:** `POST /products/{product_id}/calculate-po-score`

**Response:**
```typescript
{
  product_id: string;
  po_score: number | null;
  calculation_details: {
    whs: number | null;
    msrp: number | null;
    offer: number | null;
  };
  message: string;
}
```

**Example:**
```typescript
const calculateProductPOScore = async (productId: string) => {
  try {
    const response = await fetch(`/api/products/${productId}/calculate-po-score`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error calculating PO score:', error);
    throw error;
  }
};
```

---

## MSRP Validation

### Overview
MSRP validation checks if the source MSRP is within 5% of the enriched price from Keepa/Amazon API. This helps eliminate invalid products from offers.

### Endpoints

#### 1. Validate MSRP for All Products
**Endpoint:** `POST /products/validate-msrp`

**Query Parameters:**
- `catalog_id` (optional): Filter by catalog ID

**Response:**
```typescript
{
  message: string;
  validated: number;      // Products with msrp_validated = true
  invalidated: number;    // Products with msrp_validated = false
  skipped: number;        // Products that couldn't be validated
  errors: number;
  total_processed: number;
}
```

**Example:**
```typescript
const validateMSRP = async (catalogId?: string) => {
  try {
    const params = catalogId ? `?catalog_id=${catalogId}` : '';
    const response = await fetch(`/api/products/validate-msrp${params}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log(`Validated: ${data.validated}, Invalidated: ${data.invalidated}`);
    return data;
  } catch (error) {
    console.error('Error validating MSRP:', error);
    throw error;
  }
};
```

#### 2. Validate MSRP for Single Product
**Endpoint:** `POST /products/{product_id}/validate-msrp`

**Response:**
```typescript
{
  product_id: string;
  msrp_validated: boolean | null;
  validation_details: {
    source_msrp: number | null;
    enriched_price: number | null;
    delta_percent: number;
    difference: number | null;
    percentage_diff: number | null;
  };
  message: string;
}
```

---

## Product API - PO Score Visibility

### Overview
The `po_score` field is now available in all product API responses, allowing you to display it in the console and UI.

### Endpoints

**Get Products:** `GET /products`
- Returns list of products with `po_score` field included
- Filter by `catalog_id` to get products for a specific catalog

**Get Single Product:** `GET /products/{product_id}`
- Returns single product with `po_score` field included

### Product Response Structure
```typescript
interface ProductResponse {
  id: string;
  catalog_id: string;
  name: string;
  // ... other fields
  po_score: number | null;  // Purchase Order score (0-100)
  msrp: number | null;  // MSRP value from original data
  msrp_validated: boolean | null;  // MSRP validation status (true/false/null)
  enrichment_status: string;
  // ... other fields
}
```

### Example: Display PO Score in Console
```typescript
const fetchProducts = async (catalogId: string) => {
  try {
    const response = await fetch(`/api/products?catalog_id=${catalogId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const products = await response.json();
    
    // Display products with PO scores and MSRP status in console
    products.forEach((product: any) => {
      const msrpStatus = product.msrp_validated === true ? 'Validated' 
                       : product.msrp_validated === false ? 'Invalid' 
                       : 'Pending';
      console.log(`${product.name}: PO Score = ${product.po_score ?? 'N/A'}, MSRP = $${product.msrp ?? 'N/A'}, MSRP Status = ${msrpStatus}`);
    });
    
    return products;
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
};
```

---

## Optimal Offer Creation

### Overview
Creates an optimal offer based on:
- Investment amount (with 5% grace)
- PO scores (higher is better)
- MSRP validation (only validated products)
- Product variety (to reduce risk)
- Available inventory

### Endpoints

**Primary Endpoint:** `POST /offers`
- This is the main endpoint for creating new offers
- Uses optimal generation algorithm by default

**Legacy Endpoint:** `POST /offers/optimal`
- Still available for backward compatibility
- Same functionality as `POST /offers`

**Request Body:**
```typescript
{
  catalog_id: string;
  investment: number;                    // Required: Total investment amount
  grace_percent?: number;                // Optional: Default 5.0 (0-20%)
  max_products_per_category?: number;    // Optional: Limit products per category
  min_po_score?: number;                 // Optional: Minimum PO score threshold (0-100)
}
```

**Note:** Use `POST /offers` as the primary endpoint. The `/offers/optimal` endpoint is available for backward compatibility.

**Response:**
```typescript
{
  message: string;
  offer: {
    id: string;
    catalog_id: string;
    name: string;
    description: string;
    offer_type: "optimal";
    valid_from: string;
    valid_until: string;
    is_active: boolean;
    items: Array<{
      product_id: string;
      original_price: number;
      offer_price: number;
      discount_percentage: number;
      quantity_required: number;
      max_quantity: number;
      notes: string;
    }>;
    total_discount: number;
    total_savings: number;
    offer_score: number;
    generation_method: "optimal_algorithm";
    created_at: string;
    updated_at: string;
  };
  metadata: {
    products_considered: number;
    products_selected: number;
    total_investment: number;
    actual_total: number;
    deviation_percent: number;
    average_po_score: number;
    categories_included: string[];
    category_distribution: Record<string, number>;
    total_savings: number;
    total_discount_percent: number;
  };
}
```

### Example Implementation

```typescript
interface OptimalOfferRequest {
  catalog_id: string;
  investment: number;
  grace_percent?: number;
  max_products_per_category?: number;
  min_po_score?: number;
}

const createOffer = async (request: OptimalOfferRequest) => {
  try {
    // Use the main /offers endpoint (recommended)
    const response = await fetch('/api/offers', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create offer');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error creating offer:', error);
    throw error;
  }
};

// Legacy function name for backward compatibility
const createOptimalOffer = createOffer;

// Usage
const handleCreateOffer = async () => {
  try {
    const result = await createOffer({
      catalog_id: '68a187ff78a50181068ddc8c',
      investment: 10000.00,
      grace_percent: 5.0,
      max_products_per_category: 3,
      min_po_score: 50.0
    });
    
    console.log('Offer created:', result.offer);
    console.log('Metadata:', result.metadata);
  } catch (error) {
    console.error('Failed to create offer:', error);
  }
};
```

---

## Complete Workflow Example

### React Component Example

```typescript
import React, { useState } from 'react';

interface OfferGenerationProps {
  catalogId: string;
}

const OfferGeneration: React.FC<OfferGenerationProps> = ({ catalogId }) => {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'idle' | 'calculating' | 'validating' | 'creating'>('idle');
  const [results, setResults] = useState<any>(null);
  const [investment, setInvestment] = useState<number>(10000);

  // Step 1: Calculate PO Scores
  const handleCalculatePOScores = async () => {
    setLoading(true);
    setStep('calculating');
    try {
      const response = await fetch(`/api/products/calculate-po-scores?catalog_id=${catalogId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      console.log('PO Scores calculated:', data);
      return data;
    } catch (error) {
      console.error('Error calculating PO scores:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Validate MSRP
  const handleValidateMSRP = async () => {
    setLoading(true);
    setStep('validating');
    try {
      const response = await fetch(`/api/products/validate-msrp?catalog_id=${catalogId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      console.log('MSRP validated:', data);
      return data;
    } catch (error) {
      console.error('Error validating MSRP:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Create Offer
  const handleCreateOffer = async () => {
    setLoading(true);
    setStep('creating');
    try {
      const response = await fetch('/api/offers', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          catalog_id: catalogId,
          investment: investment,
          grace_percent: 5.0,
          max_products_per_category: 3,
          min_po_score: 50.0
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create offer');
      }
      
      const data = await response.json();
      setResults(data);
      console.log('Offer created:', data);
      return data;
    } catch (error) {
      console.error('Error creating offer:', error);
      throw error;
    } finally {
      setLoading(false);
      setStep('idle');
    }
  };

  // Complete workflow
  const handleFullWorkflow = async () => {
    try {
      // Step 1: Calculate PO scores
      await handleCalculatePOScores();
      await new Promise(resolve => setTimeout(resolve, 1000)); // Small delay
      
      // Step 2: Validate MSRP
      await handleValidateMSRP();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Step 3: Create offer
      await handleCreateOffer();
    } catch (error) {
      console.error('Workflow error:', error);
      alert('Failed to complete workflow. Please try again.');
    }
  };

  return (
    <div className="offer-generation">
      <h2>Generate Optimal Offer</h2>
      
      <div className="form-group">
        <label>Investment Amount ($)</label>
        <input
          type="number"
          value={investment}
          onChange={(e) => setInvestment(parseFloat(e.target.value))}
          min="0"
          step="0.01"
        />
      </div>

      <div className="button-group">
        <button 
          onClick={handleCalculatePOScores}
          disabled={loading}
        >
          {step === 'calculating' ? 'Calculating...' : '1. Calculate PO Scores'}
        </button>
        
        <button 
          onClick={handleValidateMSRP}
          disabled={loading}
        >
          {step === 'validating' ? 'Validating...' : '2. Validate MSRP'}
        </button>
        
        <button 
          onClick={handleCreateOffer}
          disabled={loading}
        >
          {step === 'creating' ? 'Creating...' : '3. Create Offer'}
        </button>
        
        <button 
          onClick={handleFullWorkflow}
          disabled={loading}
          className="primary"
        >
          {loading ? 'Processing...' : 'Run Full Workflow'}
        </button>
      </div>

      {results && (
        <div className="results">
          <h3>Offer Created Successfully!</h3>
          <div className="offer-summary">
            <p><strong>Products Selected:</strong> {results.metadata.products_selected}</p>
            <p><strong>Total Investment:</strong> ${results.metadata.total_investment.toLocaleString()}</p>
            <p><strong>Actual Total:</strong> ${results.metadata.actual_total.toLocaleString()}</p>
            <p><strong>Deviation:</strong> {results.metadata.deviation_percent}%</p>
            <p><strong>Average PO Score:</strong> {results.metadata.average_po_score.toFixed(1)}</p>
            <p><strong>Total Savings:</strong> ${results.metadata.total_savings.toLocaleString()}</p>
            <p><strong>Categories:</strong> {results.metadata.categories_included.join(', ')}</p>
          </div>
          
          <div className="offer-items">
            <h4>Selected Products:</h4>
            <ul>
              {results.offer.items.map((item: any, index: number) => (
                <li key={index}>
                  Product {item.product_id} - ${item.offer_price} 
                  (PO Score: {item.notes.split(': ')[1]})
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default OfferGeneration;
```

---

## API Endpoints Reference

### PO Score Calculation
- `POST /products/calculate-po-scores?catalog_id={id}` - Calculate for all products
- `POST /products/{product_id}/calculate-po-score` - Calculate for single product

### MSRP Validation
- `POST /products/validate-msrp?catalog_id={id}` - Validate all products
- `POST /products/{product_id}/validate-msrp` - Validate single product

### Offer Creation
- `POST /offers` - Create new offer (uses optimal generation algorithm)
- `POST /offers/optimal` - Create optimal offer (legacy endpoint, same as POST /offers)

### Product Information
- `GET /products` - Get all products (includes `po_score` field)
- `GET /products/{product_id}` - Get single product (includes `po_score` field)

---

## Error Handling

### Common Errors

1. **No Eligible Products**
   ```
   Error: "No eligible products found. Products must be enriched, have po_score, and msrp_validated=True"
   ```
   **Solution:** Ensure products are enriched and validated before creating offers.

2. **Investment Range Not Met**
   ```
   Error: "Could not create offer within investment range ($X - $Y)"
   ```
   **Solution:** Adjust investment amount or grace_percent, or check available products.

3. **Missing Required Fields**
   ```
   Error: "PO score could not be calculated (missing required fields)"
   ```
   **Solution:** Ensure products have WHS, MSRP, and Offer Price in original_data.

### Error Handling Example

```typescript
const handleCreateOffer = async () => {
  try {
    const result = await createOffer({
      catalog_id: catalogId,
      investment: investment
    });
    return result;
  } catch (error: any) {
    if (error.message.includes('No eligible products')) {
      alert('No eligible products found. Please ensure products are enriched and validated.');
    } else if (error.message.includes('investment range')) {
      alert('Could not create offer with this investment amount. Try adjusting the amount.');
    } else {
      alert(`Error: ${error.message}`);
    }
    throw error;
  }
};
```

---

## Best Practices

### 1. Pre-flight Checks
Before creating an offer, check if products are ready and display PO scores:

```typescript
const checkProductsReady = async (catalogId: string) => {
  const response = await fetch(`/api/products?catalog_id=${catalogId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const products = await response.json();
  
  // Display PO scores and MSRP status in console
  console.log('Products with PO Scores and MSRP Status:');
  products.forEach((p: any) => {
    const msrpStatus = p.msrp_validated === true ? 'Validated' 
                     : p.msrp_validated === false ? 'Invalid' 
                     : 'Pending';
    console.log(`${p.name}: PO Score = ${p.po_score ?? 'N/A'}, MSRP = $${p.msrp ?? 'N/A'}, MSRP Status = ${msrpStatus}`);
  });
  
  const enriched = products.filter((p: any) => 
    p.enrichment_status === 'completed' && 
    p.po_score !== null && 
    p.msrp_validated === true
  );
  
  return {
    total: products.length,
    ready: enriched.length,
    readyPercent: (enriched.length / products.length) * 100,
    averagePOScore: enriched.length > 0 
      ? enriched.reduce((sum: number, p: any) => sum + (p.po_score || 0), 0) / enriched.length 
      : 0
  };
};
```

### 2. Progress Indicators
Show progress during multi-step workflow:

```typescript
const [progress, setProgress] = useState({
  step: 0,
  total: 3,
  message: ''
});

const updateProgress = (step: number, message: string) => {
  setProgress({ step, total: 3, message });
};
```

### 3. Validation Before Submission
Validate investment amount before submitting:

```typescript
const validateInvestment = (amount: number): boolean => {
  if (amount <= 0) {
    alert('Investment must be greater than 0');
    return false;
  }
  if (amount < 100) {
    alert('Investment should be at least $100');
    return false;
  }
  return true;
};
```

### 4. Display Offer Details
Show comprehensive offer information:

```typescript
const OfferDetails: React.FC<{ offer: any }> = ({ offer }) => {
  return (
    <div className="offer-details">
      <h3>{offer.name}</h3>
      <div className="metrics">
        <Metric label="Total Investment" value={`$${offer.metadata.total_investment.toLocaleString()}`} />
        <Metric label="Actual Total" value={`$${offer.metadata.actual_total.toLocaleString()}`} />
        <Metric label="Deviation" value={`${offer.metadata.deviation_percent}%`} />
        <Metric label="Average PO Score" value={offer.metadata.average_po_score.toFixed(1)} />
        <Metric label="Total Savings" value={`$${offer.metadata.total_savings.toLocaleString()}`} />
        <Metric label="Products" value={offer.metadata.products_selected} />
      </div>
      
      <ProductList items={offer.offer.items} />
    </div>
  );
};
```

### 5. Retry Logic
Implement retry for failed operations:

```typescript
const retryOperation = async (
  operation: () => Promise<any>,
  maxRetries: number = 3,
  delay: number = 1000
) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
};
```

---

## TypeScript Types

```typescript
// Add these to your types file

interface POScoreCalculation {
  message: string;
  updated: number;
  skipped: number;
  errors: number;
  total_processed: number;
}

interface MSRPValidation {
  message: string;
  validated: number;
  invalidated: number;
  skipped: number;
  errors: number;
  total_processed: number;
}

interface OptimalOfferRequest {
  catalog_id: string;
  investment: number;
  grace_percent?: number;
  max_products_per_category?: number;
  min_po_score?: number;
}

interface OfferItem {
  product_id: string;
  original_price: number;
  offer_price: number;
  discount_percentage: number;
  quantity_required: number;
  max_quantity: number;
  notes: string;
}

interface OptimalOfferResponse {
  message: string;
  offer: {
    id: string;
    catalog_id: string;
    name: string;
    description: string;
    offer_type: "optimal";
    items: OfferItem[];
    total_discount: number;
    total_savings: number;
    offer_score: number;
    created_at: string;
    updated_at: string;
  };
  metadata: {
    products_considered: number;
    products_selected: number;
    total_investment: number;
    actual_total: number;
    deviation_percent: number;
    average_po_score: number;
    categories_included: string[];
    category_distribution: Record<string, number>;
    total_savings: number;
    total_discount_percent: number;
  };
}
```

---

## Summary

1. **View PO Scores**: PO scores are now available in all product API responses (`GET /products`)
2. **Calculate PO Scores**: Run before creating offers to ensure all products have scores
3. **Validate MSRP**: Ensure only validated products are included in offers
4. **Create Offer**: Use `POST /offers` to generate offer based on investment amount and constraints
5. **Handle Errors**: Provide user-friendly error messages
6. **Show Progress**: Display workflow progress and results

## Key Changes

- ✅ **New Endpoint**: `POST /offers` is now the primary endpoint for creating offers
- ✅ **PO Score Visibility**: `po_score` is included in all product API responses
- ✅ **Backward Compatibility**: `POST /offers/optimal` still works but use `POST /offers` going forward

For questions or issues, contact the backend team.

---

**Last Updated:** December 2024  
**API Version:** Current  
**Status:** ✅ Ready for implementation




