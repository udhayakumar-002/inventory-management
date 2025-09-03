from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from functools import wraps
import os
from datetime import datetime

app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Mock database (replace with real database later)
users = {
    "admin": {"password": "password123", "name": "Administrator"}
}

class Category:
    def __init__(self, id, name, description, status=True):
        self.id = id
        self.name = name
        self.description = description
        self.status = status

# Mock database
categories = [
    Category(1, "Electronics", "Electronic items and gadgets", True),
    Category(2, "Groceries", "Food and household items", True),
    Category(3, "Clothing", "Apparel and accessories", True)
]

class Product:
    def __init__(self, id, code, name, category, price, stock):
        self.id = id
        self.code = code
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock

class Invoice:
    def __init__(self, id, number, customer, date, total):
        self.id = id
        self.number = number
        self.customer = customer
        self.date = date
        self.total = total

# Mock data
products = [
    Product(1, "P001", "Laptop", "Electronics", 999.99, 10),
    Product(2, "P002", "Mouse", "Electronics", 29.99, 50),
    Product(3, "P003", "Keyboard", "Electronics", 49.99, 30)
]

invoices = [
    Invoice(1, "INV-001", "John Doe", "2025-09-01", 1029.98),
    Invoice(2, "INV-002", "Jane Smith", "2025-09-02", 159.97)
]

stock_history = []

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def login_page():
    if 'user' in session:
        return redirect(url_for('home_page'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in users and users[username]["password"] == password:
        session['user'] = username
        return jsonify({"status": "success"})
    return jsonify({"status": "failed", "msg": "Invalid username or password"})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))

@app.route('/home')
@login_required
def home_page():
    return render_template('home.html', page="home")

@app.route('/category')
@login_required
def category():
    return render_template('category_mgt.html', page="category", categories=categories)

@app.route('/products')
@login_required
def products_page():
    return render_template('product_mgt.html', page="products", products=products)

@app.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html', page="inventory", products=products)

@app.route('/sales')
@login_required
def sales():
    return render_template('sales.html', page="sales", invoices=invoices)

@app.route('/inventory-history')
@login_required
def inventory_history():
    return render_template('inventory-history.html', page="inventory_history", stock_history=stock_history)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', page="profile", user=users[session['user']])

# Category Management
@app.route('/manage_category', methods=['GET', 'POST'])
@app.route('/manage_category/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_category(id=None):
    category = next((cat for cat in categories if cat.id == id), None) if id else None
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        status = request.form.get('status') == '1'
        
        if category:
            # Update existing category
            category.name = name
            category.description = description
            category.status = status
            msg = "Category updated successfully"
        else:
            # Create new category
            new_id = max(cat.id for cat in categories) + 1 if categories else 1
            new_category = Category(new_id, name, description, status)
            categories.append(new_category)
            msg = "Category created successfully"
            
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "success", "msg": msg})
        return redirect(url_for('category'))
        
    return render_template('manage_category.html', category=category)

# Product Management
@app.route('/manage_product', methods=['GET', 'POST'])
@app.route('/manage_product/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_product(id=None):
    product = next((prod for prod in products if prod.id == id), None) if id else None
    
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        category_id = int(request.form.get('category_id'))
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        
        category = next((cat for cat in categories if cat.id == category_id), None)
        
        if product:
            # Update existing product
            product.code = code
            product.name = name
            product.category = category.name if category else ''
            product.price = price
            product.stock = stock
            msg = "Product updated successfully"
        else:
            # Create new product
            new_id = max(prod.id for prod in products) + 1 if products else 1
            new_product = Product(new_id, code, name, category.name if category else '', price, stock)
            products.append(new_product)
            msg = "Product created successfully"
            
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"status": "success", "msg": msg})
        return redirect(url_for('products_page'))
        
    return render_template('manage_product.html', product=product, categories=categories)

# Stock Management
@app.route('/manage_stock', methods=['GET', 'POST'])
@app.route('/manage_stock/<int:id>', methods=['GET', 'POST'])
@login_required
def manage_stock(id=None):
    product = next((prod for prod in products if prod.id == id), None) if id else None
    
    if request.method == 'POST':
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        stock_type = request.form.get('type')
        remarks = request.form.get('remarks')
        
        product = next((prod for prod in products if prod.id == product_id), None)
        
        if product:
            if stock_type == 'in':
                product.stock += quantity
            else:
                if product.stock >= quantity:
                    product.stock -= quantity
                else:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({"status": "failed", "msg": "Insufficient stock"})
                    return redirect(url_for('inventory'))
            
            # Add to stock history
            stock_history.append({
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'product': product.name,
                'type': stock_type,
                'quantity': quantity,
                'remarks': remarks
            })
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "success", "msg": "Stock updated successfully"})
            return redirect(url_for('inventory'))
            
    return render_template('manage_stock.html', product=product, products=products)

# Category Delete
@app.route('/category/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    category = next((cat for cat in categories if cat.id == id), None)
    if category:
        categories.remove(category)
        return jsonify({"status": "success", "msg": "Category deleted successfully"})
    return jsonify({"status": "failed", "msg": "Category not found"}), 404

# Product Delete
@app.route('/product/<int:id>/delete', methods=['POST'])
@login_required
def delete_product(id):
    product = next((prod for prod in products if prod.id == id), None)
    if product:
        products.remove(product)
        return jsonify({"status": "success", "msg": "Product deleted successfully"})
    return jsonify({"status": "failed", "msg": "Product not found"}), 404

# Profile Management
@app.route('/manage_profile', methods=['GET', 'POST'])
@login_required
def manage_profile():
    if request.method == 'POST':
        # Handle profile updates
        pass
    return render_template('manage_profile.html')

@app.route('/update_password', methods=['GET', 'POST'])
@login_required
def update_password():
    if request.method == 'POST':
        # Handle password updates
        pass
    return render_template('update_password.html')

# Context processor for template variables
@app.context_processor
def utility_processor():
    return {
        'MEDIA_URL': '/static',
        'page': None,
        'datetime': datetime,
    }

# Health check endpoint for Render
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Only run in debug mode locally
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
