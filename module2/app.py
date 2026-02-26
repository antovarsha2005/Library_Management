from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import Database
import logging
from datetime import datetime
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
db = Database()

@app.route('/')
def index():
    """Redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Render dashboard with statistics"""
    try:
        stats = {
            'total_users': db.get_total_users(),
            'active_users': db.get_active_users(),
            'total_books': db.get_total_books(),
            'books_issued': db.get_books_issued()
        }
        recent_activities = db.get_recent_activities(limit=10)
        return render_template('dashboard.html', stats=stats, activities=recent_activities)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('dashboard.html', stats={}, activities=[])

@app.route('/users')
def view_users():
    """View all users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        users = db.get_all_users_paginated(page, per_page)
        return render_template('view_users.html', users=users, page=page)
    except Exception as e:
        logger.error(f"Error viewing users: {e}")
        flash('Error loading users', 'error')
        return render_template('view_users.html', users=[])

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    """Add new user"""
    if request.method == 'POST':
        try:
            user_data = {
                'name': request.form['name'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'address': request.form['address'],
                'membership_type': request.form['membership_type'],
                'joined_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            if db.add_user(user_data):
                flash('User added successfully!', 'success')
                logger.info(f"New user added: {user_data['email']}")
                return redirect(url_for('view_users'))
            else:
                flash('Failed to add user', 'error')
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            flash('Error adding user', 'error')
    
    return render_template('add_user.html')

@app.route('/users/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    """Update user information"""
    if request.method == 'POST':
        try:
            user_data = {
                'name': request.form['name'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'address': request.form['address'],
                'membership_type': request.form['membership_type'],
                'status': request.form['status']
            }
            
            if db.update_user(user_id, user_data):
                flash('User updated successfully!', 'success')
                logger.info(f"User updated: {user_id}")
                return redirect(url_for('view_users'))
            else:
                flash('Failed to update user', 'error')
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            flash('Error updating user', 'error')
    
    user = db.get_user_by_id(user_id)
    return render_template('update_user.html', user=user)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """Delete user"""
    try:
        if db.delete_user(user_id):
            flash('User deleted successfully!', 'success')
            logger.info(f"User deleted: {user_id}")
        else:
            flash('Failed to delete user', 'error')
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        flash('Error deleting user', 'error')
    
    return redirect(url_for('view_users'))

@app.route('/users/search')
def search_user():
    """Search users"""
    query = request.args.get('q', '')
    try:
        if query:
            users = db.search_users(query)
        else:
            users = []
        return render_template('search_user.html', users=users, query=query)
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        flash('Error searching users', 'error')
        return render_template('search_user.html', users=[], query=query)

@app.route('/api/users')
def api_users():
    """API endpoint for users"""
    try:
        users = db.get_all_users()
        return jsonify({'status': 'success', 'data': users})
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)