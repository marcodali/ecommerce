from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import stripe
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopping_cart.db'
db = SQLAlchemy(app)

# Set your Stripe API key
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    image = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=0)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    data = request.json
    item = Item.query.get(data['id'])
    if item:
        item.quantity += data['quantity']
        db.session.commit()
        return jsonify({"message": "Item added to cart"}), 200
    return jsonify({"message": "Item not found"}), 404

@app.route('/insert_items', methods=['POST'])
def insert_items():
    items_data = request.json
    for item_data in items_data:
        new_item = Item(
            id=item_data['id'],
            title=item_data['title'],
            price=item_data['price'],
            description=item_data['description'],
            category=item_data['category'],
            image=item_data['image']
        )
        db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Items inserted successfully"}), 201

@app.route('/list_items', methods=['GET'])
def list_items():
    sort = request.args.get('sort', 'asc')
    if sort not in ['asc', 'desc']:
        return jsonify({"message": "Invalid sort parameter"}), 400
    
    items = Item.query.order_by(Item.price.asc() if sort == 'asc' else Item.price.desc()).all()
    return jsonify([{
        "id": item.id,
        "title": item.title,
        "price": item.price,
        "description": item.description,
        "category": item.category,
        "image": item.image,
        "quantity": item.quantity
    } for item in items])

@app.route('/update_quantity', methods=['PUT'])
def update_quantity():
    data = request.json
    item = Item.query.get(data['id'])
    if item:
        item.quantity = data['quantity']
        db.session.commit()
        return jsonify({"message": "Quantity updated"}), 200
    return jsonify({"message": "Item not found"}), 404

@app.route('/cart_total', methods=['GET'])
def cart_total():
    total = sum(item.price * item.quantity for item in Item.query.all())
    return jsonify({"total": total})

@app.route('/checkout', methods=['POST'])
def checkout():
    total = sum(item.price * item.quantity for item in Item.query.all())
    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # Stripe expects the amount in cents
            currency='usd',
        )
        return jsonify({
            'clientSecret': intent.client_secret
        })
    except Exception as e:
        return jsonify(error=str(e)), 403

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)