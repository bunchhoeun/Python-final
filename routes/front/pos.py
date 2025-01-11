import os
import uuid, requests
from datetime import datetime

from flask import redirect, url_for, render_template, jsonify, request, json
from app import app, db
from models.models import Product, Category, Sale, SaleItem

from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


inch = 72
thermal_paper_size = (3.15 * inch, 11.7 * inch)  # 80mm x 297mm in inches


bot_name = "bonglanhoun_bot"
bot_token = "7062184533:AAFAlASWJ-tJ30Wo03FaoS0l5-deKnJ0uho"
channel = "-1002056950604"
image_file_path = None


@app.route('/')
def home():
    # Redirect to the /admin/dashboard route
    return redirect(url_for('pos'))


@app.get('/pos')
def pos():
    return render_template('front/index.html')


@app.get('/api/getPOSData')
def get_pos_data():
    products = Product.query.all()
    # Convert products to dictionary format
    products_list = [product.to_dict() for product in products]

    categories = Category.query.all()
    categories_list = [category.to_dict() for category in categories]
    return jsonify(products_list=products_list, categories_list=categories_list)


@app.post('/api/create_sale')
def create_sale():
    data = request.json
    ref_code = generate_ref_code()
    all_products = ""
    transaction_date = datetime.now().strftime("%B %d, %Y, %I:%M %p")

    try:
        # Create a new sale record
        new_sale = Sale(
            ref_code=ref_code,
            transaction_date=transaction_date,
            total_amount=data['total_amount'],
            received_amount=data['received_amount'],
            user_id=data['user_id']
        )
        db.session.add(new_sale)
        db.session.flush()  # Get the sale ID before committing

        media_group = []
        files = {}
        images = []
        # Add items to the sale_items table
        for index, item in enumerate(data['items'], start=1):
            sale_item = SaleItem(
                sale_id=new_sale.id,
                product_id=item['id'],
                qty=item['quantity'],
                price=item['price'],
                total=item['price'] * item['quantity']
            )
            db.session.add(sale_item)

            # Update product stock
            product = Product.query.get(item['id'])
            if product:
                product.current_stock -= item['quantity']

            all_products += f"📦 {index}. {product.name if product else 'Unknown Product'} {item['quantity']} x ${item['price']}\n"

            file_path = os.path.join("static", "upload", "product", "crop", item['image'])

            images.append(file_path)

        db.session.commit()

        # Ensure numeric conversion
        received_amount = float(data['received_amount'])
        total_amount = float(data['total_amount'])

        # Calculate change
        change = received_amount - total_amount

        # Create the HTML content for the Telegram message
        html = (
            "<strong>🧾 Invoice: {inv_no}</strong>\n"
            "👤 <strong>Buyer Name: {buyer}</strong>\n"
            "💵 <code>Total: ${grand_total}</code>\n"
            "💳 <code>Received: ${received_amount}</code>\n"
            "💰 <code>Change: ${change}</code>\n"
            "📅 <code>Date: {date}</code>\n"
            "<code>===================================================</code>\n"
            "<code>{all_products}</code>\n"
            "✅ <strong>Thank you for your purchase!</strong>"
        ).format(
            inv_no=ref_code,
            buyer="Regular",
            grand_total=f"{total_amount:.2f}",  # Format to 2 decimal places
            received_amount=f"{received_amount:.2f}",
            change=f"{change:.2f}",
            date=transaction_date,
            all_products=all_products,
        )

        for idx, image in enumerate(images):
            field_name = f"photo{idx}"  # Unique field name for each image
            files[field_name] = open(image, 'rb')  # Open image file

            media_item = {
                "type": "photo",
                "media": f"attach://{field_name}"
            }

            # Add the caption only to the first image
            if idx == 0:
                media_item["caption"] = html
                media_item["parse_mode"] = "HTML"

            media_group.append(media_item)


        # print_receipt(ref_code, "Regular", total_amount, received_amount, change, transaction_date, all_products)

        # Send the message to Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMediaGroup"

        response = requests.post(url, data={"chat_id": channel, "media": json.dumps(media_group)}, files=files)

        for file in files.values():
            file.close()

        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Sale created successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_ref_code():
    today = datetime.now().strftime("%Y%m%d")  # Format: YYYYMMDD

    # Get the highest ref_code for today
    last_sale = Sale.query.filter(Sale.ref_code.like(f"{today}-%")).order_by(Sale.ref_code.desc()).first()
    last_number = int(last_sale.ref_code.split('-')[-1]) if last_sale else 0

    # Increment the number and generate the new ref_code
    new_ref_code = f"{today}-{last_number + 1:04}"  # e.g., 20241214-0001
    return new_ref_code

def print_receipt(ref_code, buyer, total_amount, received_amount, change, transaction_date, all_products):
    # Directory where PDFs will be saved
    pdf_directory = 'static/upload/receipt'

    # Create the directory if it doesn't exist
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    # File path for the PDF
    pdf_file_path = os.path.join(pdf_directory, f"receipt_{ref_code}.pdf")

    # Create a canvas for the PDF with thermal paper size
    pdf = canvas.Canvas(pdf_file_path, pagesize=thermal_paper_size)  # Make sure thermal_paper_size is defined

    # Define page width and height for later centering calculations
    page_width, page_height = thermal_paper_size

    # Start Y position from the top (adjust as needed)
    y_position = page_height - 20

    # Helper function to draw centered text
    def draw_centered_text(y, text, font="Helvetica", font_size=10):
        pdf.setFont(font, font_size)
        text_width = pdf.stringWidth(text, font, font_size)
        x_position = (page_width - text_width) / 2
        pdf.drawString(x_position, y, text)

    # Start receipt with the shop name (centered)
    draw_centered_text(y_position, "Coffee Shop", font="Helvetica-Bold", font_size=12)
    y_position -= 20

    # Print logo (ensure the image is in black and white and the path is correct)
    logo_path = "logo.bmp"  # Path to the logo file, should be monochrome (black and white)
    try:
        pdf.drawImage(logo_path, 10, y_position - 30, width=80, height=30)  # Position and size of the logo
    except:
        draw_centered_text(y_position - 30, "[Logo not available]", font="Helvetica", font_size=10)
    y_position -= 40

    # Add the invoice header (Invoice number, centered)
    draw_centered_text(y_position, f"Invoice: {ref_code}")
    y_position -= 20

    # Buyer details (left-aligned)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(10, y_position, f"Buyer Name: {buyer}")
    y_position -= 20

    # Print total, received, and change (left-aligned)
    pdf.drawString(10, y_position, f"Total: ${total_amount:.2f}")
    y_position -= 20
    pdf.drawString(10, y_position, f"Received: ${received_amount:.2f}")
    y_position -= 20
    pdf.drawString(10, y_position, f"Change: ${change:.2f}")
    y_position -= 20

    # Print transaction date (left-aligned)
    pdf.drawString(10, y_position, f"Date: {transaction_date}")
    y_position -= 20

    # Divider line
    pdf.line(10, y_position, page_width - 10, y_position)
    y_position -= 10

    # List of products (itemized list, left-aligned)
    for index, product in enumerate(all_products.split('\n'), start=1):
        pdf.drawString(10, y_position, f"{index}. {product}")
        y_position -= 15

    # Divider line
    pdf.line(10, y_position, page_width - 10, y_position)
    y_position -= 10

    # Thank you message (centered)
    draw_centered_text(y_position, "Thank you for your purchase!")

    # Save the PDF
    pdf.save()

    # Return the file path where the PDF is saved
    return pdf_file_path