from flask import redirect, url_for, render_template
from app import app

@app.route('/admin')
def admin():
    # Redirect to the /admin/dashboard route
    return redirect(url_for('dashboard'))

@app.route('/admin/dashboard')
def dashboard():
    return render_template('admin/index.html')