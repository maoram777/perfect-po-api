import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from bson import ObjectId
from ..database import get_database
from ..models.offer import Offer, OfferCreate, OfferItem, OfferRule, ProductInfo
import math

logger = logging.getLogger(__name__)


class OfferService:
    """Service for generating and managing offers based on enriched catalog data."""
    
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
        return self._db
    
    async def generate_offers_for_catalog(
        self, 
        catalog_id: str, 
        user_id: str,
        offer_type: str = "standard",
        max_offers: int = 5
    ) -> List[Offer]:
        """Generate offers for a specific catalog based on enriched products."""
        try:
            # Get enriched products from the catalog
            products = await self.db.products.find({
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id),
                "enrichment.status": "completed"
            }).to_list(None)
            
            if not products:
                raise ValueError("No enriched products found for this catalog")
            
            # Get catalog information
            catalog = await self.db.catalogs.find_one({
                "_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            
            if not catalog:
                raise ValueError("Catalog not found")
            
            # Generate different types of offers
            offers = []
            
            if offer_type == "standard" or offer_type == "all":
                offers.extend(await self._generate_standard_offers(products, catalog, user_id, max_offers))
            
            if offer_type == "bundle" or offer_type == "all":
                offers.extend(await self._generate_bundle_offers(products, catalog, user_id, max_offers))
            
            if offer_type == "flash" or offer_type == "all":
                offers.extend(await self._generate_flash_offers(products, catalog, user_id, max_offers))
            
            # Save offers to database
            saved_offers = []
            for offer in offers:
                offer_dict = offer.dict()
                offer_dict["_id"] = ObjectId()
                result = await self.db.offers.insert_one(offer_dict)
                offer_dict["_id"] = result.inserted_id
                saved_offers.append(Offer(**offer_dict))
            
            logger.info(f"Generated {len(saved_offers)} offers for catalog {catalog_id}")
            return saved_offers
            
        except Exception as e:
            logger.error(f"Error generating offers: {e}")
            raise Exception(f"Failed to generate offers: {e}")
    
    async def _generate_standard_offers(
        self, 
        products: List[Dict[str, Any]], 
        catalog: Dict[str, Any],
        user_id: str,
        max_offers: int
    ) -> List[Offer]:
        """Generate standard individual product offers."""
        offers = []
        
        # Select random products for offers
        selected_products = random.sample(products, min(len(products), max_offers))
        
        for i, product in enumerate(selected_products):
            # Calculate offer price with random discount
            original_price = product.get("price", 0) or 0
            if original_price <= 0:
                continue
            
            # Generate random discount between 5% and 25%
            discount_percentage = random.uniform(5, 25)
            offer_price = round(original_price * (1 - discount_percentage / 100), 2)
            
            # Extract product information for embedding
            product_info = self._extract_product_info(product, product["_id"])
            
            # Create offer item
            offer_item = OfferItem(
                product_id=product["_id"],
                product=ProductInfo(**product_info),
                original_price=original_price,
                offer_price=offer_price,
                discount_percentage=round(discount_percentage, 2),
                quantity_required=1,
                max_quantity=random.randint(5, 20),
                upc=product.get("upc"),
                sku=product.get("sku")
            )
            
            # Create offer rule
            offer_rule = OfferRule(
                rule_id=f"rule_{i+1}",
                rule_name="Standard Discount Rule",
                rule_type="pricing",
                rule_parameters={"discount_type": "percentage", "min_discount": 5},
                priority=1,
                is_active=True
            )
            
            # Calculate offer metrics
            total_discount = original_price - offer_price
            total_savings = total_discount
            
            # Generate simple offer score (0-10)
            offer_score = round(random.uniform(6.0, 9.5), 1)
            
            # Create offer
            offer = Offer(
                catalog_id=ObjectId(catalog["_id"]),
                user_id=ObjectId(user_id),
                name=f"Special Offer: {product.get('name', 'Product')}",
                description=f"Limited time discount on {product.get('name', 'this product')}",
                offer_type="standard",
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=random.randint(7, 30)),
                is_active=True,
                items=[offer_item],
                rules=[offer_rule],
                total_discount=round(discount_percentage, 2),
                total_savings=total_savings,
                offer_score=offer_score,
                generation_method="rule_based"
            )
            
            offers.append(offer)
        
        return offers
    
    async def _generate_bundle_offers(
        self, 
        products: List[Dict[str, Any]], 
        catalog: Dict[str, Any],
        user_id: str,
        max_offers: int
    ) -> List[Offer]:
        """Generate bundle offers combining multiple products."""
        offers = []
        
        if len(products) < 2:
            return offers
        
        # Create bundle offers
        for i in range(min(max_offers, len(products) // 2)):
            # Select 2-3 products for bundle
            bundle_size = random.randint(2, min(3, len(products)))
            bundle_products = random.sample(products, bundle_size)
            
            bundle_items = []
            total_original_price = 0
            
            for product in bundle_products:
                original_price = product.get("price", 0) or 0
                if original_price <= 0:
                    continue
                
                # Bundle discount is higher than individual offers
                discount_percentage = random.uniform(15, 35)
                offer_price = round(original_price * (1 - discount_percentage / 100), 2)
                
                # Extract product information for embedding
                product_info = self._extract_product_info(product, product["_id"])
                
                offer_item = OfferItem(
                    product_id=product["_id"],
                    product=ProductInfo(**product_info),
                    original_price=original_price,
                    offer_price=offer_price,
                    discount_percentage=round(discount_percentage, 2),
                    quantity_required=1,
                    max_quantity=random.randint(3, 10),
                    upc=product.get("upc"),
                    sku=product.get("sku")
                )
                
                bundle_items.append(offer_item)
                total_original_price += original_price
            
            if not bundle_items:
                continue
            
            # Calculate bundle metrics
            total_offer_price = sum(item.offer_price for item in bundle_items)
            total_discount = total_original_price - total_offer_price
            bundle_discount_percentage = round((total_discount / total_original_price) * 100, 2)
            
            # Bundle rule
            bundle_rule = OfferRule(
                rule_id=f"bundle_rule_{i+1}",
                rule_name="Bundle Discount Rule",
                rule_type="bundle",
                rule_parameters={"min_products": len(bundle_items), "bundle_discount": bundle_discount_percentage},
                priority=2,
                is_active=True
            )
            
            # Generate bundle offer score
            offer_score = round(random.uniform(7.0, 9.8), 1)
            
            # Create bundle offer
            offer = Offer(
                catalog_id=ObjectId(catalog["_id"]),
                user_id=ObjectId(user_id),
                name=f"Bundle Deal #{i+1}",
                description=f"Save on {len(bundle_items)} products when purchased together",
                offer_type="bundle",
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=random.randint(14, 45)),
                is_active=True,
                items=bundle_items,
                rules=[bundle_rule],
                total_discount=round(bundle_discount_percentage, 2),
                total_savings=total_discount,
                offer_score=offer_score,
                generation_method="rule_based"
            )
            
            offers.append(offer)
        
        return offers
    
    async def _generate_flash_offers(
        self, 
        products: List[Dict[str, Any]], 
        catalog: Dict[str, Any],
        user_id: str,
        max_offers: int
    ) -> List[Offer]:
        """Generate flash sale offers with high discounts and short validity."""
        offers = []
        
        # Select random products for flash offers
        selected_products = random.sample(products, min(len(products), max_offers))
        
        for i, product in enumerate(selected_products):
            original_price = product.get("price", 0) or 0
            if original_price <= 0:
                continue
            
            # Flash offers have higher discounts (20-40%)
            discount_percentage = random.uniform(20, 40)
            offer_price = round(original_price * (1 - discount_percentage / 100), 2)
            
            # Extract product information for embedding
            product_info = self._extract_product_info(product, product["_id"])
            
            # Create flash offer item
            offer_item = OfferItem(
                product_id=product["_id"],
                product=ProductInfo(**product_info),
                original_price=original_price,
                offer_price=offer_price,
                discount_percentage=round(discount_percentage, 2),
                quantity_required=1,
                max_quantity=random.randint(3, 8),  # Limited quantity for flash sales
                upc=product.get("upc"),
                sku=product.get("sku")
            )
            
            # Flash sale rule
            flash_rule = OfferRule(
                rule_id=f"flash_rule_{i+1}",
                rule_name="Flash Sale Rule",
                rule_type="timing",
                rule_parameters={"flash_duration_hours": 24, "max_quantity": offer_item.max_quantity},
                priority=3,  # High priority for flash sales
                is_active=True
            )
            
            # Calculate metrics
            total_discount = original_price - offer_price
            total_savings = total_discount
            
            # Flash offers get higher scores
            offer_score = round(random.uniform(8.0, 9.9), 1)
            
            # Create flash offer with short validity
            offer = Offer(
                catalog_id=ObjectId(catalog["_id"]),
                user_id=ObjectId(user_id),
                name=f"Flash Sale: {product.get('name', 'Product')}",
                description=f"Limited time flash sale! {discount_percentage:.0f}% off!",
                offer_type="flash",
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(hours=random.randint(6, 48)),  # Short validity
                is_active=True,
                items=[offer_item],
                rules=[flash_rule],
                total_discount=round(discount_percentage, 2),
                total_savings=total_savings,
                offer_score=offer_score,
                generation_method="rule_based"
            )
            
            offers.append(offer)
        
        return offers
    
    async def get_user_offers(
        self, 
        user_id: str, 
        catalog_id: Optional[str] = None,
        offer_type: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Offer]:
        """Get offers for a specific user."""
        try:
            filter_query = {"user_id": ObjectId(user_id)}
            
            if catalog_id:
                filter_query["catalog_id"] = ObjectId(catalog_id)
            
            if offer_type:
                filter_query["offer_type"] = offer_type
            
            cursor = self.db.offers.find(filter_query).skip(skip).limit(limit)
            offers = []
            async for offer in cursor:
                offers.append(Offer(**offer))
            
            return offers
            
        except Exception as e:
            logger.error(f"Error fetching user offers: {e}")
            raise Exception(f"Failed to fetch offers: {e}")
    
    async def get_offer_by_id(self, offer_id: str, user_id: str) -> Optional[Offer]:
        """Get a specific offer by ID."""
        try:
            offer = await self.db.offers.find_one({
                "_id": ObjectId(offer_id),
                "user_id": ObjectId(user_id)
            })
            
            return Offer(**offer) if offer else None
            
        except Exception as e:
            logger.error(f"Error fetching offer: {e}")
            raise Exception(f"Failed to fetch offer: {e}")
    
    async def update_offer(
        self, 
        offer_id: str, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Offer]:
        """Update an offer."""
        try:
            update_dict = update_data.copy()
            update_dict["updated_at"] = datetime.utcnow()
            
            result = await self.db.offers.update_one(
                {"_id": ObjectId(offer_id), "user_id": ObjectId(user_id)},
                {"$set": update_dict}
            )
            
            if result.modified_count > 0:
                return await self.get_offer_by_id(offer_id, user_id)
            return None
            
        except Exception as e:
            logger.error(f"Error updating offer: {e}")
            raise Exception(f"Failed to update offer: {e}")
    
    async def delete_offer(self, offer_id: str, user_id: str) -> bool:
        """Delete an offer."""
        try:
            result = await self.db.offers.delete_one({
                "_id": ObjectId(offer_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting offer: {e}")
            raise Exception(f"Failed to delete offer: {e}")
    
    async def generate_optimal_offer(
        self,
        catalog_id: str,
        user_id: str,
        investment: float,
        grace_percent: float = 5.0,
        max_products_per_category: Optional[int] = None,
        min_po_score: Optional[float] = None
    ) -> Tuple[Optional[Offer], Dict[str, Any]]:
        """Generate optimal offer based on investment amount, po_score, profit, and inventory.
        
        Algorithm:
        1. Filter products: enriched, po_score exists, profit > 0 (profitable products)
        2. Sort by po_score (descending) and offer price
        3. Use greedy algorithm with variety constraint
        4. Ensure total matches investment within grace_percent
        
        Args:
            catalog_id: Catalog ID
            user_id: User ID
            investment: Total investment amount
            grace_percent: Allowed deviation from investment (default 5%)
            max_products_per_category: Maximum products per category for variety (None = no limit)
            min_po_score: Minimum PO score threshold (None = no threshold)
        
        Returns:
            Tuple of (Offer, metadata dict with selection details)
        """
        try:
            # Get eligible products
            filter_query = {
                "catalog_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id),
                "enrichment.status": {"$in": ["completed", "partially_completed"]},
                "profit": {"$gt": 0},  # Only profitable products (profit > 0)
                "po_score": {"$ne": None}  # Must have PO score
            }
            
            if min_po_score is not None:
                filter_query["po_score"] = {"$ne": None, "$gte": min_po_score}
            
            products = await self.db.products.find(filter_query).to_list(None)
            
            if not products:
                raise ValueError("No eligible products found. Products must be enriched, have po_score, and profit > 0")
            
            # Get catalog information
            catalog = await self.db.catalogs.find_one({
                "_id": ObjectId(catalog_id),
                "user_id": ObjectId(user_id)
            })
            
            if not catalog:
                raise ValueError("Catalog not found")
            
            # Extract offer prices (saved at product level from CSV)
            eligible_products = []
            for product in products:
                offer_price = product.get("offer_price")  # Required field, saved at product level
                quantity_available = product.get("quantity") or 0  # Required field, saved at product level
                
                if offer_price and offer_price > 0 and quantity_available > 0:
                    eligible_products.append({
                        "product_id": product["_id"],
                        "product": product,
                        "offer_price": float(offer_price),
                        "po_score": product.get("po_score", 0),
                        "quantity_available": int(quantity_available),
                        "category": product.get("category") or "Uncategorized",
                        "name": product.get("name", "Unknown Product")
                    })
            
            if not eligible_products:
                raise ValueError("No products with valid offer prices and inventory found")
            
            # Sort by po_score (descending) and then by offer_price (ascending for better deals)
            eligible_products.sort(key=lambda x: (-x["po_score"], x["offer_price"]))
            
            # Calculate investment bounds
            min_investment = investment * (1 - grace_percent / 100)
            max_investment = investment * (1 + grace_percent / 100)
            
            # Greedy selection with variety constraint
            selected_items = []
            total_cost = 0.0
            category_counts = {}
            total_po_score = 0.0
            selection_metadata = {
                "products_considered": len(eligible_products),
                "products_selected": 0,
                "total_investment": investment,
                "actual_total": 0.0,
                "deviation_percent": 0.0,
                "average_po_score": 0.0,
                "categories_included": []
            }
            
            for product_info in eligible_products:
                # Check if adding this product would exceed budget
                if total_cost + product_info["offer_price"] > max_investment:
                    continue
                
                # Check variety constraint (max products per category)
                category = product_info["category"]
                if max_products_per_category:
                    if category_counts.get(category, 0) >= max_products_per_category:
                        continue
                
                # Add product (quantity = 1 for now, can be extended)
                selected_items.append({
                    "product_id": product_info["product_id"],
                    "product": product_info["product"],
                    "offer_price": product_info["offer_price"],
                    "po_score": product_info["po_score"],
                    "quantity": 1
                })
                
                total_cost += product_info["offer_price"]
                total_po_score += product_info["po_score"]
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # Stop if we've reached minimum investment
                if total_cost >= min_investment:
                    break
            
            # If we haven't reached minimum, try to fill with smaller items
            if total_cost < min_investment:
                remaining = min_investment - total_cost
                for product_info in eligible_products:
                    if product_info["product_id"] in [item["product_id"] for item in selected_items]:
                        continue
                    
                    if product_info["offer_price"] <= remaining and total_cost + product_info["offer_price"] <= max_investment:
                        category = product_info["category"]
                        if max_products_per_category and category_counts.get(category, 0) >= max_products_per_category:
                            continue
                        
                        selected_items.append({
                            "product_id": product_info["product_id"],
                            "product": product_info["product"],
                            "offer_price": product_info["offer_price"],
                            "po_score": product_info["po_score"],
                            "quantity": 1
                        })
                        
                        total_cost += product_info["offer_price"]
                        total_po_score += product_info["po_score"]
                        category_counts[category] = category_counts.get(category, 0) + 1
                        
                        if total_cost >= min_investment:
                            break
            
            if not selected_items:
                raise ValueError(f"Could not create offer within investment range (${min_investment:.2f} - ${max_investment:.2f})")
            
            # Create offer items
            offer_items = []
            total_original_price = 0.0
            total_offer_price = 0.0
            
            for item in selected_items:
                product = item["product"]
                raw_data = product.get("raw_data", {})
                original_price = self._extract_original_price(raw_data) or item["offer_price"]
                offer_price = item["offer_price"]
                quantity = item["quantity"]
                
                discount_percentage = ((original_price - offer_price) / original_price * 100) if original_price > 0 else 0
                
                # Extract product information for embedding
                product_info = self._extract_product_info(product, item["product_id"])
                
                offer_item = OfferItem(
                    product_id=item["product_id"],
                    product=ProductInfo(**product_info),
                    original_price=original_price,
                    offer_price=offer_price,
                    discount_percentage=round(discount_percentage, 2),
                    quantity_required=quantity,
                    max_quantity=item["product"].get("quantity", 1),
                    notes=f"PO Score: {item['po_score']:.1f}",
                    upc=product.get("upc"),
                    sku=product.get("sku")
                )
                
                offer_items.append(offer_item)
                total_original_price += original_price * quantity
                total_offer_price += offer_price * quantity
            
            # Calculate metrics
            total_discount = total_original_price - total_offer_price
            total_discount_percentage = (total_discount / total_original_price * 100) if total_original_price > 0 else 0
            average_po_score = total_po_score / len(selected_items) if selected_items else 0
            
            # Calculate offer score based on po_score and variety
            variety_score = min(100, len(category_counts) * 10)  # 10 points per category, max 100
            po_score_normalized = (average_po_score / 100) * 50  # Max 50 points
            offer_score = round(variety_score + po_score_normalized, 1)
            
            # Create offer rule
            offer_rule = OfferRule(
                rule_id="optimal_offer_rule",
                rule_name="Optimal Investment Offer",
                rule_type="investment",
                rule_parameters={
                    "investment": investment,
                    "grace_percent": grace_percent,
                    "min_po_score": min_po_score,
                    "max_products_per_category": max_products_per_category
                },
                priority=1,
                is_active=True
            )
            
            # Create offer
            offer = Offer(
                catalog_id=ObjectId(catalog_id),
                user_id=ObjectId(user_id),
                name=f"Optimal Offer - ${investment:,.2f} Investment",
                description=f"Optimized offer with {len(selected_items)} products, average PO score: {average_po_score:.1f}",
                offer_type="optimal",
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=30),
                is_active=True,
                items=offer_items,
                rules=[offer_rule],
                total_discount=round(total_discount_percentage, 2),
                total_savings=round(total_discount, 2),
                offer_score=offer_score,
                generation_method="optimal_algorithm"
            )
            
            # Save to database
            offer_dict = offer.dict()
            offer_dict["_id"] = ObjectId()
            result = await self.db.offers.insert_one(offer_dict)
            offer_dict["_id"] = result.inserted_id
            saved_offer = Offer(**offer_dict)
            
            # Prepare metadata
            deviation_percent = abs(total_offer_price - investment) / investment * 100 if investment > 0 else 0
            selection_metadata.update({
                "products_selected": len(selected_items),
                "actual_total": round(total_offer_price, 2),
                "deviation_percent": round(deviation_percent, 2),
                "average_po_score": round(average_po_score, 2),
                "categories_included": list(category_counts.keys()),
                "category_distribution": category_counts,
                "total_savings": round(total_discount, 2),
                "total_discount_percent": round(total_discount_percentage, 2)
            })
            
            logger.info(
                f"Generated optimal offer for catalog {catalog_id}: "
                f"{len(selected_items)} products, ${total_offer_price:.2f} total, "
                f"avg PO score: {average_po_score:.1f}"
            )
            
            return saved_offer, selection_metadata
            
        except Exception as e:
            logger.error(f"Error generating optimal offer: {e}")
            raise Exception(f"Failed to generate optimal offer: {e}")
    
    def _extract_offer_price(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract offer price from original data."""
        price_fields = ["Offer Price", "offer_price", "offer", "Offer", "Price", "price", "selling_price"]
        
        for field in price_fields:
            value = raw_data.get(field)
            if value is not None:
                try:
                    if isinstance(value, str):
                        cleaned_value = value.replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
                        return float(cleaned_value)
                    else:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_original_price(self, raw_data: Dict[str, Any]) -> Optional[float]:
        """Extract original/MSRP price from original data."""
        price_fields = ["MSRP", "msrp", "RRP", "rrp", "Retail Price", "retail_price", "list_price", "Original Price"]
        
        for field in price_fields:
            value = raw_data.get(field)
            if value is not None:
                try:
                    if isinstance(value, str):
                        cleaned_value = value.replace('$', '').replace('€', '').replace(',', '').replace(' ', '').strip()
                        return float(cleaned_value)
                    else:
                        return float(value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_product_info(self, product: Dict[str, Any], product_id: Any) -> Dict[str, Any]:
        """Extract product information for embedding in offer items."""
        # Handle color field migration (from 'colors' to 'color')
        color = product.get("color")
        if not color and product.get("colors"):
            colors_str = product.get("colors", "")
            if colors_str and "," in str(colors_str):
                color = str(colors_str).split(",")[0].strip()
            elif colors_str:
                color = str(colors_str).strip()
        
        # Handle main_image field
        image = product.get("main_image")
        if image is not None:
            if isinstance(image, list) and len(image) > 0:
                image = str(image[0]) if image[0] else None
            elif not isinstance(image, str):
                image = str(image) if image else None
        
        return {
            "id": str(product_id),
            "brand": product.get("brand"),
            "name": product.get("name"),
            "description": product.get("description"),
            "color": color,
            "size": product.get("size"),
            "image": image
        }


# Global instance
offer_service = OfferService()
