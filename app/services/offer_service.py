import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from ..database import get_database
from ..models.offer import Offer, OfferCreate, OfferItem, OfferRule
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
                "enrichment_status": "completed"
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
            
            # Create offer item
            offer_item = OfferItem(
                product_id=product["_id"],
                original_price=original_price,
                offer_price=offer_price,
                discount_percentage=round(discount_percentage, 2),
                quantity_required=1,
                max_quantity=random.randint(5, 20)
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
                
                offer_item = OfferItem(
                    product_id=product["_id"],
                    original_price=original_price,
                    offer_price=offer_price,
                    discount_percentage=round(discount_percentage, 2),
                    quantity_required=1,
                    max_quantity=random.randint(3, 10)
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
            
            # Create flash offer item
            offer_item = OfferItem(
                product_id=product["_id"],
                original_price=original_price,
                offer_price=offer_price,
                discount_percentage=round(discount_percentage, 2),
                quantity_required=1,
                max_quantity=random.randint(3, 8)  # Limited quantity for flash sales
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


# Global instance
offer_service = OfferService()
