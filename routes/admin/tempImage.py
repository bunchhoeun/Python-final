import os
import uuid

from flask import request, jsonify
from app import app, db
from models.models import TempImage

TEMP_FOLDER = os.path.join('static', 'temp')
app.config['TEMP_FOLDER'] = TEMP_FOLDER
TEMP_ORIGINAL_FOLDER = os.path.join('static', 'temp', 'original')
app.config['TEMP_ORIGINAL_FOLDER'] = TEMP_ORIGINAL_FOLDER


@app.route('/admin/api/upload-temp-image/create', methods=['POST'])
def upload_temp_image():
    if 'cropped_image' in request.files and 'original_image' in request.files:
        cropped_image = request.files['cropped_image']  # Get cropped image
        original_image = request.files['original_image']  # Get original image
        # Save the file
        uuid_name = str(uuid.uuid4())  # Generate a unique ID for the image

        filename = uuid_name + os.path.splitext(cropped_image.filename)[1]

        cropped_image_file_path = os.path.join(app.config['TEMP_FOLDER'], filename)
        original_image_file_path = os.path.join(app.config['TEMP_ORIGINAL_FOLDER'], filename)

        try:
            # Save both images
            cropped_image.save(cropped_image_file_path)
            original_image.save(original_image_file_path)

            # Save metadata to the database
            new_image = TempImage(name=filename)
            db.session.add(new_image)
            db.session.commit()

            # Return the ID of the new image entry
            return jsonify({'image_id': new_image.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid request. Missing image files.'}), 400

