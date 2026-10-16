"""
Seed data — populates the database with demo customers, products, orders, and knowledge base documents.
This makes the project instantly demo-ready without any external setup.
"""
import json
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.core.security import get_password_hash


def seed_database(db: Session):
    """Seed the database with demo data if tables are empty."""

    # Check if already seeded
    if db.query(Customer).first():
        return

    # ─── Users (admin + support agents) ──────────────
    users = [
        User(email="admin@supportflow.ai", password_hash=get_password_hash("admin123"), full_name="Admin User", role="admin"),
        User(email="sarah@supportflow.ai", password_hash=get_password_hash("agent123"), full_name="Sarah Johnson", role="support_agent"),
        User(email="mike@supportflow.ai", password_hash=get_password_hash("agent123"), full_name="Mike Chen", role="support_agent"),
        User(email="ruthi@example.com", password_hash=get_password_hash("customer123"), full_name="Ruthi", role="customer"),
    ]
    db.add_all(users)
    db.commit()

    # ─── Customers ───────────────────────────────────
    customers = [
        Customer(name="Ruthi", email="ruthi@example.com", phone="+1-555-0101", address="123 Main St, San Francisco, CA 94102"),
        Customer(name="Arun Kumar", email="arun@example.com", phone="+1-555-0102", address="456 Oak Ave, New York, NY 10001"),
        Customer(name="Priya Sharma", email="priya@example.com", phone="+1-555-0103", address="789 Pine Rd, Chicago, IL 60601"),
        Customer(name="James Wilson", email="james@example.com", phone="+1-555-0104", address="321 Elm St, Austin, TX 73301"),
        Customer(name="Emily Zhang", email="emily@example.com", phone="+1-555-0105", address="654 Maple Dr, Seattle, WA 98101"),
    ]
    db.add_all(customers)
    db.commit()

    # ─── Products ────────────────────────────────────
    products = [
        Product(name="Wireless Noise-Cancelling Headphones", description="Premium ANC headphones with 30hr battery", price=149.99, inventory=50, category="electronics"),
        Product(name="Ergonomic Laptop Stand", description="Adjustable aluminum stand for 13-17 inch laptops", price=59.99, inventory=100, category="accessories"),
        Product(name="USB-C Hub 7-in-1", description="HDMI, USB 3.0 x3, SD, microSD, PD 100W", price=39.99, inventory=200, category="electronics"),
        Product(name="Mechanical Keyboard (Blue Switch)", description="Full-size RGB mechanical keyboard", price=89.99, inventory=75, category="electronics"),
        Product(name="Wireless Mouse Pro", description="Ergonomic wireless mouse with adjustable DPI", price=34.99, inventory=150, category="accessories"),
        Product(name="4K Webcam", description="Ultra HD webcam with auto-focus and noise-cancelling mic", price=79.99, inventory=60, category="electronics"),
        Product(name="Laptop Backpack", description="Water-resistant 15.6 inch laptop backpack", price=49.99, inventory=120, category="accessories"),
        Product(name="Monitor Light Bar", description="LED monitor light bar, adjustable brightness", price=44.99, inventory=80, category="accessories"),
    ]
    db.add_all(products)
    db.commit()

    # ─── Orders ──────────────────────────────────────
    orders_data = [
        # Ruthi's orders
        {"customer_id": 1, "status": "delivered", "total": 209.98, "tracking": "TRK-2024-001", "delivery": "Oct 10, 2024",
         "address": "123 Main St, San Francisco, CA 94102",
         "items": [{"product_id": 1, "qty": 1, "price": 149.99}, {"product_id": 3, "qty": 1, "price": 39.99}, {"product_id": 5, "qty": 1, "price": 34.99}]},
        {"customer_id": 1, "status": "shipped", "total": 89.99, "tracking": "TRK-2024-002", "delivery": "Oct 20, 2024",
         "address": "123 Main St, San Francisco, CA 94102",
         "items": [{"product_id": 4, "qty": 1, "price": 89.99}]},
        {"customer_id": 1, "status": "processing", "total": 124.98, "tracking": None, "delivery": "Oct 25, 2024",
         "address": "123 Main St, San Francisco, CA 94102",
         "items": [{"product_id": 6, "qty": 1, "price": 79.99}, {"product_id": 8, "qty": 1, "price": 44.99}]},

        # Arun's orders
        {"customer_id": 2, "status": "delivered", "total": 59.99, "tracking": "TRK-2024-003", "delivery": "Oct 8, 2024",
         "address": "456 Oak Ave, New York, NY 10001",
         "items": [{"product_id": 2, "qty": 1, "price": 59.99}]},
        {"customer_id": 2, "status": "processing", "total": 184.98, "tracking": None, "delivery": "Oct 22, 2024",
         "address": "456 Oak Ave, New York, NY 10001",
         "items": [{"product_id": 1, "qty": 1, "price": 149.99}, {"product_id": 5, "qty": 1, "price": 34.99}]},

        # Priya's order
        {"customer_id": 3, "status": "shipped", "total": 169.98, "tracking": "TRK-2024-004", "delivery": "Oct 18, 2024",
         "address": "789 Pine Rd, Chicago, IL 60601",
         "items": [{"product_id": 4, "qty": 1, "price": 89.99}, {"product_id": 6, "qty": 1, "price": 79.99}]},
    ]

    for od in orders_data:
        order = Order(
            customer_id=od["customer_id"],
            status=od["status"],
            total_amount=od["total"],
            tracking_number=od["tracking"],
            estimated_delivery=od["delivery"],
            shipping_address=od["address"],
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        for item in od["items"]:
            oi = OrderItem(order_id=order.id, product_id=item["product_id"], quantity=item["qty"], unit_price=item["price"])
            db.add(oi)
    db.commit()

    # ─── Knowledge Base (company policies) ───────────
    knowledge_docs = [
        {
            "filename": "return_policy.md",
            "title": "Return Policy",
            "category": "policy",
            "content": """Return Policy

Customers can return most items within 30 days of delivery for a full refund. Items must be in original condition with all packaging and accessories.

Conditions:
- Items must be returned within 30 days of delivery date
- Items must be unused and in original packaging
- Electronics must include all original accessories and manuals
- Custom or personalized items cannot be returned
- Sale items are final sale and cannot be returned

Process:
1. Contact our support team to initiate a return
2. You will receive a prepaid return shipping label
3. Pack the item securely and ship it back
4. Refund will be processed within 5-7 business days after we receive the item

Refunds are issued to the original payment method."""
        },
        {
            "filename": "shipping_policy.md",
            "title": "Shipping Policy",
            "category": "policy",
            "content": """Shipping Policy

We offer the following shipping options:

Standard Shipping (5-7 business days): Free for orders over $50, otherwise $5.99
Express Shipping (2-3 business days): $12.99
Overnight Shipping (1 business day): $24.99

All orders are processed within 1-2 business days. You will receive a tracking number via email once your order ships.

International shipping is available to select countries. International orders may be subject to customs duties and taxes.

Delivery delays:
- Weather events may cause 1-3 day delays
- Peak seasons (holidays) may cause 2-5 day delays
- We will notify you of any significant delays via email

If your package hasn't arrived within the expected timeframe, please contact our support team."""
        },
        {
            "filename": "warranty_policy.md",
            "title": "Warranty Policy",
            "category": "policy",
            "content": """Warranty Policy

All electronics products come with a 1-year manufacturer warranty that covers:
- Manufacturing defects
- Hardware malfunctions under normal use
- Battery issues (within first year)

Not covered:
- Physical damage (drops, water damage, etc.)
- Normal wear and tear
- Unauthorized modifications or repairs
- Accessories (unless explicitly stated)

To claim warranty:
1. Contact support with your order number and description of the issue
2. Our team will diagnose the problem
3. If covered, we will arrange a replacement or repair
4. Turnaround time is typically 7-14 business days

Extended warranty plans are available for purchase within 30 days of original order."""
        },
        {
            "filename": "faq.md",
            "title": "Frequently Asked Questions",
            "category": "faq",
            "content": """Frequently Asked Questions

Q: How can I track my order?
A: You can track your order using the tracking number provided in your shipping confirmation email. Contact support with your order number for real-time updates.

Q: Can I change my order after placing it?
A: Orders can be modified within 1 hour of placement if they haven't been processed yet. Contact support immediately for changes.

Q: What payment methods do you accept?
A: We accept Visa, Mastercard, American Express, PayPal, and Apple Pay.

Q: Do you offer price matching?
A: We offer price matching within 14 days of purchase if you find the same item at a lower price from an authorized retailer.

Q: How do I cancel my order?
A: Orders can be cancelled if they are still in 'processing' status. Once an order has shipped, it cannot be cancelled — you will need to initiate a return instead.

Q: What if I receive a damaged item?
A: Contact support immediately with photos of the damage. We will arrange a free replacement or full refund."""
        },
        {
            "filename": "cancellation_policy.md",
            "title": "Order Cancellation Policy",
            "category": "policy",
            "content": """Order Cancellation Policy

Orders can be cancelled under the following conditions:

1. The order status must be 'processing' (not yet shipped)
2. Cancellation requests must be made within 24 hours of order placement for guaranteed processing
3. Once an order has been shipped, it cannot be cancelled — please initiate a return instead

Cancellation process:
- Contact support or use the self-service cancellation option
- Cancellation is processed immediately for 'processing' orders
- Refund will be issued to original payment method within 3-5 business days

Partial cancellations:
- Individual items can be cancelled from multi-item orders if the order hasn't shipped
- If some items have shipped, only unshipped items can be cancelled

Note: Repeated cancellations may result in account review."""
        },
    ]

    for kd in knowledge_docs:
        doc = KnowledgeDocument(
            filename=kd["filename"],
            title=kd["title"],
            category=kd["category"],
            content=kd["content"],
            chunk_index=0,
            embedding=json.dumps([0.0] * 768),  # Placeholder; real embeddings generated via RAG upload API
        )
        db.add(doc)
    db.commit()

    print("✅ Database seeded with demo data!")
