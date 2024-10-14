import pytest
from app import app, db, Item
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    with app.app_context():
        db.drop_all()

def test_insert_items(client):
    items = [
        {
            "id": 1,
            "title": "Test Item",
            "price": 10.99,
            "description": "This is a test item",
            "category": "test",
            "image": "http://test.com/image.jpg"
        }
    ]
    response = client.post('/insert_items', json=items)
    assert response.status_code == 201
    assert b"Items inserted successfully" in response.data

def test_add_to_cart(client):
    # First, insert an item
    items = [{"id": 1, "title": "Test Item", "price": 10.99, "description": "Test", "category": "test", "image": "test.jpg"}]
    client.post('/insert_items', json=items)

    # Now, add the item to the cart
    response = client.post('/add_to_cart', json={"id": 1, "quantity": 2})
    assert response.status_code == 200
    assert b"Item added to cart" in response.data

def test_add_to_cart_item_not_found(client):
    response = client.post('/add_to_cart', json={"id": 999, "quantity": 2})
    assert response.status_code == 404
    assert b"Item not found" in response.data

def test_list_items(client):
    # Insert some items
    items = [
        {"id": 1, "title": "Cheap Item", "price": 5.99, "description": "Test", "category": "test", "image": "test.jpg"},
        {"id": 2, "title": "Expensive Item", "price": 15.99, "description": "Test", "category": "test", "image": "test.jpg"}
    ]
    client.post('/insert_items', json=items)

    # Test ascending order
    response = client.get('/list_items?sort=asc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['price'] < data[1]['price']

    # Test descending order
    response = client.get('/list_items?sort=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['price'] > data[1]['price']

def test_update_quantity(client):
    # First, insert an item and add it to the cart
    items = [{"id": 1, "title": "Test Item", "price": 10.99, "description": "Test", "category": "test", "image": "test.jpg"}]
    client.post('/insert_items', json=items)
    client.post('/add_to_cart', json={"id": 1, "quantity": 2})

    # Now, update the quantity
    response = client.put('/update_quantity', json={"id": 1, "quantity": 5})
    assert response.status_code == 200
    assert b"Quantity updated" in response.data

def test_update_quantity_item_not_found(client):
    response = client.put('/update_quantity', json={"id": 999, "quantity": 5})
    assert response.status_code == 404
    assert b"Item not found" in response.data

def test_cart_total(client):
    # Insert items and add them to the cart
    items = [
        {"id": 1, "title": "Item 1", "price": 10.99, "description": "Test", "category": "test", "image": "test.jpg"},
        {"id": 2, "title": "Item 2", "price": 15.99, "description": "Test", "category": "test", "image": "test.jpg"}
    ]
    client.post('/insert_items', json=items)
    client.post('/add_to_cart', json={"id": 1, "quantity": 2})
    client.post('/add_to_cart', json={"id": 2, "quantity": 1})

    response = client.get('/cart_total')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['total'] == pytest.approx(37.97, 0.01)

# Note: We're not testing the checkout function as it involves external API calls to Stripe.
# In a real-world scenario, you would mock the Stripe API for testing.