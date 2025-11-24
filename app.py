from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Database configuration - UPDATE THESE VALUES WITH YOUR MYSQL CREDENTIALS
DB_CONFIG = {
    'host': 'localhost',        # Your MySQL server host
    'user': 'root',             # Your MySQL username
    'password': '21082005',  # Your MySQL password
    'database': 'voter_service',       # Database name
    'charset': 'utf8mb4'
}

# Database initialization
def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def init_db():
    # Connect without specifying database first
    config = DB_CONFIG.copy()
    db_name = config.pop('database')
    
    # Connect to MySQL server
    conn = pymysql.connect(**config)
    c = conn.cursor()
    
    # Create database if it doesn't exist
    c.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    c.execute(f"USE {db_name}")
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(50) DEFAULT 'voter',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create voter applications table
    c.execute('''CREATE TABLE IF NOT EXISTS voter_applications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        date_of_birth DATE NOT NULL,
        gender VARCHAR(50) NOT NULL,
        address TEXT NOT NULL,
        state VARCHAR(100) NOT NULL,
        district VARCHAR(100) NOT NULL,
        pincode VARCHAR(20) NOT NULL,
        id_proof_type VARCHAR(100) NOT NULL,
        id_proof_number VARCHAR(100) NOT NULL,
        status VARCHAR(50) DEFAULT 'submitted',
        admin_remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Create election cards table
    c.execute('''CREATE TABLE IF NOT EXISTS election_cards (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        user_id INT NOT NULL,
        election_card_number VARCHAR(50) UNIQUE NOT NULL,
        issued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES voter_applications(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    

    
    # Insert default admin user if not exists
    hashed_password = hash_password('admin123')
    c.execute("""INSERT IGNORE INTO users (name, email, password, role) 
                 VALUES (%s, %s, %s, %s)""",
              ('Admin User', 'admin@example.com', hashed_password, 'admin'))
    
    conn.commit()
    conn.close()

# Hash password for storage
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Check if user is logged in
def is_logged_in():
    return 'user_id' in session

# Check if user is admin
def is_admin():
    return session.get('role') == 'admin'

# Home route
@app.route('/')
def home():
    return render_template('home.html')
# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password
        hashed_password = hash_password(password)
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Insert user into database with default voter role
            c.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                      (name, email, hashed_password, 'voter'))
            
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except pymysql.IntegrityError:
            flash('Email already exists!', 'error')
            return render_template('register.html')
    
    return render_template('register.html')
# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Hash the provided password
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id, name, email, role FROM users WHERE email=%s AND password=%s",
                  (email, hashed_password))
        user = c.fetchone()
        
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['email'] = user[2]
            session['role'] = user[3]
            flash('Login successful!', 'success')
            
            # Redirect based on role
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('voter_dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')
# Voter Dashboard route
@app.route('/voter/dashboard')
def voter_dashboard():
    if not is_logged_in() or is_admin():
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))
    
    # Get user applications
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get recent applications
    c.execute("SELECT id, full_name, status, created_at FROM voter_applications WHERE user_id=%s ORDER BY created_at DESC LIMIT 5", 
              (session['user_id'],))
    recent_applications = c.fetchall()
    
    conn.close()
    
    return render_template('voter/dashboard.html', recent_applications=recent_applications)
# New Voter Application Form
@app.route('/voter/new_application', methods=['GET', 'POST'])
def new_application():
    if not is_logged_in() or is_admin():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form['full_name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        address = request.form['address']
        state = request.form['state']
        district = request.form['district']
        pincode = request.form['pincode']
        id_proof_type = request.form['id_proof_type']
        id_proof_number = request.form['id_proof_number']
        
        # Save application
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("""INSERT INTO voter_applications 
                     (user_id, full_name, date_of_birth, gender, address, state, district, pincode, id_proof_type, id_proof_number)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                  (session['user_id'], full_name, date_of_birth, gender, address, state, district, pincode, id_proof_type, id_proof_number))
        
        conn.commit()
        conn.close()
        
        flash('Voter application submitted successfully!', 'success')
        return redirect(url_for('voter_dashboard'))
    
    return render_template('voter/new_application.html')
# View Applications
@app.route('/voter/applications')
def view_applications():
    if not is_logged_in() or is_admin():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    # Get all user applications
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id, full_name, status, created_at FROM voter_applications WHERE user_id=%s ORDER BY created_at DESC", 
              (session['user_id'],))
    applications = c.fetchall()
    
    conn.close()
    
    return render_template('voter/applications.html', applications=applications)
# Application Status
@app.route('/voter/application/<int:app_id>')
def application_status(app_id):
    if not is_logged_in() or is_admin():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    # Get application details
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if application belongs to user
    c.execute("SELECT * FROM voter_applications WHERE id=%s AND user_id=%s", 
              (app_id, session['user_id']))
    application = c.fetchone()
    
    if not application:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('view_applications'))
    
    # Get election card details if application is approved
    election_card = None
    if application[11] == 'approved':  # status column
        c.execute("SELECT election_card_number FROM election_cards WHERE application_id=%s", (app_id,))
        election_card = c.fetchone()
    
    conn.close()
    
    # Convert to dict for easier access in template
    app_dict = {
        'id': application[0],
        'full_name': application[2],
        'date_of_birth': application[3],
        'gender': application[4],
        'address': application[5],
        'state': application[6],
        'district': application[7],
        'pincode': application[8],
        'id_proof_type': application[9],
        'id_proof_number': application[10],
        'status': application[11],
        'admin_remarks': application[12],
        'created_at': application[13],
        'election_card_number': election_card[0] if election_card else None
    }
    
    return render_template('voter/application_status.html', application=app_dict)
# Edit Application Form
@app.route('/voter/application/<int:app_id>/edit', methods=['GET', 'POST'])
def edit_application(app_id):
    if not is_logged_in() or is_admin():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    # Check if application belongs to user
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT * FROM voter_applications WHERE id=%s AND user_id=%s", 
              (app_id, session['user_id']))
    application = c.fetchone()
    
    if not application:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('view_applications'))
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form['full_name']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        address = request.form['address']
        state = request.form['state']
        district = request.form['district']
        pincode = request.form['pincode']
        id_proof_type = request.form['id_proof_type']
        id_proof_number = request.form['id_proof_number']
        
        # Update application and set status to submitted
        c.execute("""UPDATE voter_applications 
                     SET full_name=%s, date_of_birth=%s, gender=%s, address=%s, state=%s, district=%s, pincode=%s, id_proof_type=%s, id_proof_number=%s, status='submitted'
                     WHERE id=%s AND user_id=%s""",
                  (full_name, date_of_birth, gender, address, state, district, pincode, id_proof_type, id_proof_number, app_id, session['user_id']))
        
        conn.commit()
        conn.close()
        
        flash('Application updated successfully!', 'success')
        return redirect(url_for('application_status', app_id=app_id))
    
    # Convert to dict for easier access in template
    app_dict = {
        'id': application[0],
        'user_id': application[1],
        'full_name': application[2],
        'date_of_birth': application[3],
        'gender': application[4],
        'address': application[5],
        'state': application[6],
        'district': application[7],
        'pincode': application[8],
        'id_proof_type': application[9],
        'id_proof_number': application[10],
        'status': application[11],
        'admin_remarks': application[12],
        'created_at': application[13],
        'updated_at': application[14]
    }
    
    conn.close()
    
    return render_template('voter/edit_application.html', application=app_dict)


# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get pending applications
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get pending applications
    c.execute("""SELECT va.id, va.full_name, va.status, va.created_at, u.name as user_name 
                 FROM voter_applications va 
                 JOIN users u ON va.user_id = u.id 
                 WHERE va.status IN ('submitted', 'in_review') 
                 ORDER BY va.created_at DESC LIMIT 10""")
    pending_applications = c.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                          pending_applications=pending_applications)

# Admin view application details
@app.route('/admin/application/<int:app_id>')
def admin_view_application(app_id):
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get application details
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT va.*, u.name as user_name, u.email 
                 FROM voter_applications va 
                 JOIN users u ON va.user_id = u.id 
                 WHERE va.id=%s""", (app_id,))
    application = c.fetchone()
    
    if not application:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    # Get election card details if application is approved
    election_card = None
    if application[11] == 'approved':  # status column
        c.execute("SELECT election_card_number, issued_date FROM election_cards WHERE application_id=%s", (app_id,))
        election_card = c.fetchone()
    
    conn.close()
    
    # Convert to dict for easier access in template
    app_dict = {
        'id': application[0],
        'user_id': application[1],
        'full_name': application[2],
        'date_of_birth': application[3],
        'gender': application[4],
        'address': application[5],
        'state': application[6],
        'district': application[7],
        'pincode': application[8],
        'id_proof_type': application[9],
        'id_proof_number': application[10],
        'status': application[11],
        'admin_remarks': application[12],
        'created_at': application[13],
        'updated_at': application[14],
        'user_name': application[15],
        'user_email': application[16],
        'election_card_number': election_card[0] if election_card else None,
        'election_card_issued_date': election_card[1] if election_card else None
    }
    
    return render_template('admin/application_detail.html', application=app_dict)

# Admin update application status
@app.route('/admin/application/<int:app_id>/update_status', methods=['POST'])
def admin_update_application_status(app_id):
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    status = request.form['status']
    remarks = request.form.get('remarks', '')
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get application details before updating
    c.execute("SELECT user_id FROM voter_applications WHERE id=%s", (app_id,))
    application = c.fetchone()
    
    if not application:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    user_id = application[0]
    
    # Update application status
    c.execute("UPDATE voter_applications SET status=%s, admin_remarks=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
              (status, remarks, app_id))
    
    # If application is approved, generate election card
    if status == 'approved':
        # Generate unique election card number
        import uuid
        election_card_number = f"EC-{uuid.uuid4().hex[:12].upper()}"
        
        # Insert election card record
        try:
            c.execute("INSERT INTO election_cards (application_id, user_id, election_card_number) VALUES (%s, %s, %s)",
                      (app_id, user_id, election_card_number))
        except Exception as e:
            # If there's an error inserting the election card, log it but don't fail the update
            print(f"Error creating election card: {e}")
    
    conn.commit()
    conn.close()
    
    flash('Application status updated successfully!', 'success')
    return redirect(url_for('admin_view_application', app_id=app_id))



# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)