import os
import shutil

from flask import jsonify, request
from werkzeug.security import generate_password_hash

from app import app, render_template, db
from models.models import User, TempImage
from sqlalchemy import or_

CROPPED_PROFILE_FOLDER = os.path.join('static', 'upload', 'profile', 'crop')
app.config['CROPPED_PROFILE_FOLDER'] = CROPPED_PROFILE_FOLDER

ORIGINAL_PROFILE_FOLDER = os.path.join('static', 'upload', 'profile', 'original')
app.config['ORIGINAL_PROFILE_FOLDER'] = ORIGINAL_PROFILE_FOLDER


@app.route('/admin/user')
def user_list():
    return render_template('admin/user/list.html')


@app.route('/api/add/user', methods=['POST'])
def add_user():
    form = request.get_json()
    # Extract data from the form
    name = form.get('name')
    code = form.get('code')
    password = form.get('password')
    email = form.get('email')
    phone = form.get('phone')
    gender = form.get('gender')
    role = form.get('role')
    status = form.get('status')
    address = form.get('address')

    image_id = form.get('profile')
    temp_image = TempImage.query.get(image_id) if image_id else None
    if temp_image:
        image_name = temp_image.name
        profile = image_name
    else:
        profile = None  # Handle the case where temp_image is None
        image_name = None

    if profile:
        temp_file_path = str(os.path.join(app.config['TEMP_FOLDER'], image_name))
        final_file_path = str(os.path.join(app.config['CROPPED_PROFILE_FOLDER'], image_name))

        if os.path.exists(temp_file_path):
            shutil.copy(temp_file_path, final_file_path)

        temp_original_file_path = str(os.path.join(app.config['TEMP_ORIGINAL_FOLDER'], image_name))
        profile_original_file = str(os.path.join(app.config['ORIGINAL_PROFILE_FOLDER'], image_name))

        if os.path.exists(temp_original_file_path):
            shutil.copy(temp_original_file_path, profile_original_file)

    hashed_password = generate_password_hash(password)

    # Create a new user
    new_user = User(
        name=name,
        code=code,
        password=hashed_password,
        email=email,
        phone=phone,
        gender=gender,
        role=role,
        status=status,
        address=address,
        profile=profile
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': form}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/update/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    # Retrieve the user from the database
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Get the form data from the request
    form = request.get_json()
    name = form.get('name', user.name)  # Use existing value if not provided
    code = form.get('code', user.code)
    password = form.get('password', user.password)
    email = form.get('email', user.email)
    phone = form.get('phone', user.phone)
    gender = form.get('gender', user.gender)
    role = form.get('role', user.role)
    status = form.get('status', user.status)
    address = form.get('address', user.address)

    image_id = form.get('profile')
    temp_image = TempImage.query.get(image_id) if image_id else None
    if temp_image:
        image_name = temp_image.name
        profile = image_name
    else:
        profile = user.profile  # Keep the existing profile image if none is provided
        image_name = None

    if profile != user.profile:
        temp_file_path = str(os.path.join(app.config['TEMP_FOLDER'], image_name))
        final_file_path = str(os.path.join(app.config['CROPPED_PROFILE_FOLDER'], image_name))

        if os.path.exists(temp_file_path):
            shutil.copy(temp_file_path, final_file_path)

        temp_original_file_path = str(os.path.join(app.config['TEMP_ORIGINAL_FOLDER'], image_name))
        profile_original_file = str(os.path.join(app.config['ORIGINAL_PROFILE_FOLDER'], image_name))

        if os.path.exists(temp_original_file_path):
            shutil.copy(temp_original_file_path, profile_original_file)

    # Hash password if it's provided
    if password:
        hashed_password = generate_password_hash(password)
    else:
        hashed_password = user.password  # Keep existing password if not provided

    # Update the user's details
    user.name = name
    user.code = code
    user.password = hashed_password
    user.email = email
    user.phone = phone
    user.gender = gender
    user.role = role
    user.status = status
    user.address = address
    user.profile = profile

    try:
        db.session.commit()
        
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete/user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Find the user by ID
        existing_user = User.query.get(user_id)
        if existing_user:
            # Delete the user from the database
            db.session.delete(existing_user)
            db.session.commit()

            # Return success response
            return jsonify({'status': True}), 200
        else:
            # If the user is not found
            return jsonify({'status': False, 'message': 'User not found'}), 404

    except Exception as err:
        # Handle any unexpected errors
        return jsonify({'status': False, 'message': str(err)}), 400


@app.route('/api/get/user')
def get_user():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))  # Get the limit (number of items per page)
    keyword = request.args.get('keyword', '').strip()  # Get the keyword parameter from the request

    # Base query
    query = User.query

    # Apply keyword search if provided
    if keyword:
        query = query.filter(
            or_(
                User.name.like(f'%{keyword}%'),  # Search for keyword in the name
                User.email.like(f'%{keyword}%')  # Search for keyword in the description
            )
        )

    # Apply pagination
    user = query.paginate(page=page, per_page=limit, error_out=False)

    # Prepare the response (same as before)
    response = {
        'user': [user.to_dict() for user in user.items],  # Convert each user to dict
        'totalCount': user.total,  # Total number of user in the database
        'totalPages': user.pages,  # Total number of pages
        'currentPage': user.page,  # Current page number
        'pages': [i for i in range(max(1, user.page - 2), min(user.pages + 1, user.page + 3))],
        # Dynamic page range
        'hasNext': user.has_next,  # Whether there is a next page
        'hasPrev': user.has_prev  # Whether there is a previous page
    }

    return jsonify(response)
