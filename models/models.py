from flask_login import UserMixin

from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(255), nullable=False)  # Hash the password later
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=False)  # 0 for Female, 1 for Male
    role = db.Column(db.Integer, nullable=False)  # 0 for User, 1 for Admin
    status = db.Column(db.Integer, nullable=False)  # 1 for Active, 0 for Inactive
    address = db.Column(db.Text, nullable=True)
    profile = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'password': self.password,
            'code': self.code,
            'email': self.email,
            'phone': self.phone,
            'gender': self.gender,
            'role': self.role,
            'status': self.status,
            'address': self.address,
            'profile': self.profile
        }


class TempImage(db.Model):
    __tablename__ = 'temp_image'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationship to Product
    products = db.relationship('Product', back_populates='category')

    def to_dict(self, include_products=True):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'product_count': len(self.products)  # Add product count
        }
        if include_products:
            data['products'] = [product.to_dict(include_category=False) for product in self.products]
        return data


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    name = db.Column(db.String(100), nullable=False)

    # Foreign key to Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    cost = db.Column(db.Numeric(10, 2), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    current_stock = db.Column(db.Integer, default=0)

    # Relationship to Category
    category = db.relationship('Category', back_populates='products')

    def to_dict(self, include_category=True):
        data = {
            'id': self.id,
            'code': self.code,
            'image': self.image,
            'name': self.name,
            'category_id': self.category_id,
            'cost': str(self.cost),
            'price': str(self.price),
            'current_stock': self.current_stock
        }
        if include_category and self.category:
            data['category'] = self.category.to_dict(include_products=False)  # Prevent recursion in category
        return data


class Sale(db.Model):
    __tablename__ = 'sale'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ref_code = db.Column(db.String(255), nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    received_amount = db.Column(db.Numeric(10, 2), nullable=True)

    # Foreign key to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='sales')
    items = db.relationship('SaleItem', back_populates='sale', cascade="all, delete-orphan")

    def to_dict(self, include_user=True, include_items=True):
        data = {
            'id': self.id,
            'ref_code': self.ref_code,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'total_amount': str(self.total_amount),
            'received_amount': str(self.received_amount) if self.received_amount else None,
            'user_id': self.user_id
        }
        if include_user and self.user:
            data['user'] = self.user.to_dict()
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        return data


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='RESTRICT', onupdate='CASCADE'),
                           nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    sale = db.relationship('Sale', back_populates='items')
    product = db.relationship('Product')

    def to_dict(self, include_sale=False, include_product=True):
        data = {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'qty': self.qty,
            'price': str(self.total),
            'total': str(self.total)
        }
        if include_sale and self.sale:
            data['sale'] = self.sale.to_dict(include_items=False, include_user=False)
        if include_product and self.product:
            data['product'] = self.product.to_dict(include_category=False)
        return data

User.sales = db.relationship('Sale', back_populates='user', cascade="all, delete-orphan")
Product.sale_items = db.relationship('SaleItem', back_populates='product')
