import os
import shutil
from flask import jsonify, request
from werkzeug.security import generate_password_hash
from app import app, render_template, db
from models.models import Product, Category, TempImage
from sqlalchemy import or_

CROPPED_PRODUCT_FOLDER = os.path.join('static', 'upload', 'product', 'crop')
app.config['CROPPED_PRODUCT_FOLDER'] = CROPPED_PRODUCT_FOLDER

ORIGINAL_PRODUCT_FOLDER = os.path.join('static', 'upload', 'product', 'original')
app.config['ORIGINAL_PRODUCT_FOLDER'] = ORIGINAL_PRODUCT_FOLDER


@app.route('/admin/products')
def products_list():
    return render_template('admin/product/list.html')


@app.route('/api/add/product', methods=['POST'])
def add_product():
    form = request.get_json()

    # Extract data from the form
    name = form.get('name')
    code = form.get('code')
    cost = form.get('cost')
    price = form.get('price')
    current_stock = form.get('current_stock')
    category_id = form.get('category')
    image_id = form.get('image')

    temp_image = TempImage.query.get(image_id) if image_id else None
    if temp_image:
        image_name = temp_image.name
        product_image_name = image_name
    else:
        product_image_name = None  # Handle the case where temp_image is None
        image_name = None

    if product_image_name:
        temp_file_path = str(os.path.join(app.config['TEMP_FOLDER'], image_name))
        final_file_path = str(os.path.join(app.config['CROPPED_PRODUCT_FOLDER'], image_name))

        if os.path.exists(temp_file_path):
            shutil.copy(temp_file_path, final_file_path)

        temp_original_file_path = str(os.path.join(app.config['TEMP_ORIGINAL_FOLDER'], image_name))
        product_image_name_original_file = str(os.path.join(app.config['ORIGINAL_PRODUCT_FOLDER'], image_name))

        if os.path.exists(temp_original_file_path):
            shutil.copy(temp_original_file_path, product_image_name_original_file)

    new_product = Product(
        name=name,
        code=code,
        cost=cost,
        price=price,
        current_stock=current_stock,
        category_id=category_id,
        image=image_name
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({'message': 'Product added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/update/product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    form = request.get_json()

    # Find the existing product
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Extract data from the form
    name = form.get('name')
    code = form.get('code')
    cost = form.get('cost')
    price = form.get('price')
    current_stock = form.get('current_stock')
    category_id = form.get('category')
    image_id = form.get('image')

    # Handle image updates
    temp_image = TempImage.query.get(image_id) if image_id else None
    if temp_image:
        image_name = temp_image.name
        product_image_name = image_name
    else:
        product_image_name = product.image  # Keep the existing image if no new one is provided

    if temp_image:
        temp_file_path = str(os.path.join(app.config['TEMP_FOLDER'], image_name))
        final_file_path = str(os.path.join(app.config['CROPPED_PRODUCT_FOLDER'], image_name))

        if os.path.exists(temp_file_path):
            shutil.copy(temp_file_path, final_file_path)

        temp_original_file_path = str(os.path.join(app.config['TEMP_ORIGINAL_FOLDER'], image_name))
        product_image_name_original_file = str(os.path.join(app.config['ORIGINAL_PRODUCT_FOLDER'], image_name))

        if os.path.exists(temp_original_file_path):
            shutil.copy(temp_original_file_path, product_image_name_original_file)

    # Update the product fields
    product.name = name
    product.code = code
    product.cost = cost
    product.price = price
    product.current_stock = current_stock
    product.category_id = category_id
    product.image = product_image_name

    try:
        db.session.commit()
        
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@app.route('/api/delete/product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        # Find the product by ID
        product = Product.query.get(product_id)
        if product:
            # Delete the product from the database
            db.session.delete(product)
            db.session.commit()
            

            # Return success response
            return jsonify({'status': True}), 200
        else:
            # If the product is not found
            return jsonify({'status': False, 'message': 'Product not found'}), 404
    except Exception as e:
        return jsonify({'status': False, 'message': str(e)}), 500


@app.route('/api/get/products')
def get_products():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    keyword = request.args.get('keyword', '').strip()

    # Base query
    query = Product.query

    # Apply keyword search if provided
    if keyword:
        query = query.filter(Product.name.ilike(f'%{keyword}%'))

    # Apply pagination
    products = query.paginate(page=page, per_page=limit, error_out=False)

    response = {
        'products': [product.to_dict() for product in products.items],
        'totalCount': products.total,
        'totalPages': products.pages,
        'currentPage': products.page,
        'pages': [i for i in range(max(1, products.page - 2), min(products.pages + 1, products.page + 3))],
        'hasNext': products.has_next,
        'hasPrev': products.has_prev
    }

    return jsonify(response)
