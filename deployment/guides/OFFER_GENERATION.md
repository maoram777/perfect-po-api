# Offer Generation System

The Perfect PO API includes an intelligent offer generation system that creates offers based on enriched catalog data. This system is designed to identify profitable opportunities and create compelling offers for your customers.

## 🎯 How It Works

### 1. **Data Foundation**
- Offers are generated based on **enriched products** from your catalogs
- Only products with `enrichment_status: "completed"` are considered
- The system analyzes product data, pricing, and market information

### 2. **Offer Types Generated**

#### **Standard Offers** 📦
- Individual product discounts (5-25% off)
- Based on product pricing and market analysis
- Valid for 7-30 days
- Target score: 6.0-9.5

#### **Bundle Offers** 🎁
- Multi-product combinations (2-3 items)
- Higher discounts (15-35% off) for buying together
- Valid for 14-45 days
- Target score: 7.0-9.8

#### **Flash Offers** ⚡
- Limited-time high discounts (20-40% off)
- Short validity (6-48 hours)
- Limited quantities
- Target score: 8.0-9.9

### 3. **Scoring System**
Each offer receives a score (0-10) based on:
- Discount percentage
- Product popularity
- Market demand
- Profitability potential
- Time sensitivity

## 🚀 Using the Offer Generation

### **Generate Offers**
```bash
POST /offers/generate?catalog_id={id}&offer_type=all&max_offers=5
```

**Parameters:**
- `catalog_id` - Required: The catalog to generate offers for
- `offer_type` - Optional: `standard`, `bundle`, `flash`, or `all` (default)
- `max_offers` - Optional: Maximum offers per type (1-20, default: 5)

### **View Generated Offers**
```bash
# Get all offers
GET /offers

# Get offers for specific catalog
GET /offers?catalog_id={id}

# Get offers by type
GET /offers?offer_type=standard

# Get specific offer
GET /offers/{offer_id}
```

### **Offer Management**
```bash
# Update offer
PUT /offers/{offer_id}

# Delete offer
DELETE /offers/{offer_id}

# Get offers summary
GET /offers/catalog/{catalog_id}/summary
```

## 📊 Offer Structure

### **Offer Object**
```json
{
  "id": "offer_id",
  "catalog_id": "catalog_id",
  "name": "Special Offer: Product Name",
  "description": "Limited time discount description",
  "offer_type": "standard|bundle|flash",
  "valid_from": "2024-01-01T00:00:00Z",
  "valid_until": "2024-01-31T23:59:59Z",
  "is_active": true,
  "items": [...],
  "rules": [...],
  "total_discount": 15.5,
  "total_savings": 25.00,
  "offer_score": 8.5,
  "generation_method": "rule_based"
}
```

### **Offer Item**
```json
{
  "product_id": "product_id",
  "original_price": 99.99,
  "offer_price": 84.99,
  "discount_percentage": 15.0,
  "quantity_required": 1,
  "max_quantity": 10
}
```

### **Offer Rule**
```json
{
  "rule_id": "rule_1",
  "rule_name": "Standard Discount Rule",
  "rule_type": "pricing",
  "rule_parameters": {"discount_type": "percentage", "min_discount": 5},
  "priority": 1,
  "is_active": true
}
```

## 🔧 Current Implementation

### **Simple Logic (Current)**
The current system uses randomized logic for demonstration:
- Random product selection from enriched catalog
- Random discount percentages within defined ranges
- Random validity periods
- Mock scoring system

### **Future Enhancements**
The system is designed to be easily enhanced with:
- **ROI Analysis** - Calculate actual profitability
- **Arbitrage Detection** - Identify price differences across markets
- **Market Data Integration** - Real-time pricing from external sources
- **Machine Learning** - Predictive offer optimization
- **Competitive Analysis** - Market positioning and pricing

## 🧪 Testing the System

### **Complete Flow**
1. Upload catalog file
2. Enrich catalog with external data
3. Generate offers based on enriched products
4. View and manage generated offers

### **Test Script**
Use the included test script:
```bash
python test_enrichment.py
```

This will test the complete flow including offer generation.

## 💡 Best Practices

### **For Offer Generation**
1. **Ensure Complete Enrichment** - Only enriched products generate offers
2. **Use Appropriate Offer Types** - Match offer types to your business strategy
3. **Monitor Offer Performance** - Track which offers perform best
4. **Regular Regeneration** - Generate new offers as market conditions change

### **For Production Use**
1. **Replace Mock Logic** - Implement real ROI calculations
2. **Add Market Data** - Integrate with pricing APIs
3. **Implement Analytics** - Track offer performance and conversion
4. **Add A/B Testing** - Test different offer strategies

## 🔮 Future Roadmap

### **Phase 1: Basic Offers** ✅
- Simple rule-based offer generation
- Multiple offer types
- Basic scoring system

### **Phase 2: Smart Offers** 🚧
- ROI-based pricing
- Market data integration
- Arbitrage detection

### **Phase 3: AI-Powered Offers** 📈
- Machine learning optimization
- Predictive pricing
- Dynamic offer adjustment

### **Phase 4: Advanced Analytics** 📊
- Performance tracking
- Conversion optimization
- Market trend analysis

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🐛 Troubleshooting

### **Common Issues**

1. **No Offers Generated**
   - Ensure catalog has enriched products
   - Check enrichment status is "completed"
   - Verify catalog ownership

2. **Invalid Offer Type**
   - Use: `standard`, `bundle`, `flash`, or `all`
   - Check parameter spelling

3. **Empty Offer Results**
   - Verify catalog has products with prices
   - Check product enrichment status

### **Debug Mode**
Enable debug logging in `.env`:
```bash
DEBUG=true
```

The offer generation system provides a solid foundation for creating profitable offers based on your catalog data. Start with the current implementation and enhance it with your specific business logic and market data sources.

