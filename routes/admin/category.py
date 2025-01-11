from flask import jsonify, request
from app import app, render_template, db
from models.models import Category
from sqlalchemy import or_, false  # Correct import for 'or_'


@app.route('/admin/categories')
def categories_list():
    return render_template('admin/category/list.html')


@app.route('/api/add/category', methods=['POST'])
def add_category():
    form = request.get_json()

    name = form.get('categoryName')
    description = form.get('description')

    if not name or not description:
        return jsonify({'error': 'All fields are required'}), 400

    new_category = Category(name=name, description=description)

    try:
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({'message': 'Category added successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/update/category/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        # Get the JSON data from the request
        form = request.get_json()

        # Extract category name and description from the form
        name = form.get('categoryName')
        description = form.get('description')

        # Find the category by ID
        existing_category = Category.query.get(category_id)
        if existing_category:
            # Update the existing category
            existing_category.name = name  # Make sure this matches your model's column name
            existing_category.description = description  # Make sure this matches your model's column name

            # Commit the changes to the database
            db.session.commit()
            

            # Return success response
            return jsonify({'status': True}), 200
        else:
            # If the category is not found
            return jsonify({'status': False, 'message': 'Category not found'}), 404

    except Exception as err:
        # Handle any unexpected errors
        return jsonify({'status': False, 'message': str(err)}), 400


@app.route('/api/delete/category/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        # Find the category by ID
        existing_category = Category.query.get(category_id)
        if existing_category:
            # Delete the category from the database
            db.session.delete(existing_category)
            db.session.commit()
            

            # Return success response
            return jsonify({'status': True}), 200
        else:
            # If the category is not found
            return jsonify({'status': False, 'message': 'Category not found'}), 404

    except Exception as err:
        # Handle any unexpected errors
        return jsonify({'status': False, 'message': str(err)}), 400

@app.route('/api/get/categories')
def get_categories():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))  # Get the limit (number of items per page)
    keyword = request.args.get('keyword', '').strip()  # Get the keyword parameter from the request

    # Base query
    query = Category.query

    # Apply keyword search if provided
    if keyword:
        query = query.filter(
            or_(
                Category.name.like(f'%{keyword}%'),  # Search for keyword in the name
                Category.description.like(f'%{keyword}%')  # Search for keyword in the description
            )
        )

    # Apply pagination
    categories = query.paginate(page=page, per_page=limit, error_out=False)

    # Prepare the response (same as before)
    response = {
        'categories': [category.to_dict() for category in categories.items],  # Convert each category to dict
        'totalCount': categories.total,  # Total number of categories in the database
        'totalPages': categories.pages,  # Total number of pages
        'currentPage': categories.page,  # Current page number
        'pages': [i for i in range(max(1, categories.page - 2), min(categories.pages + 1, categories.page + 3))],
        # Dynamic page range
        'hasNext': categories.has_next,  # Whether there is a next page
        'hasPrev': categories.has_prev  # Whether there is a previous page
    }

    return jsonify(response)
