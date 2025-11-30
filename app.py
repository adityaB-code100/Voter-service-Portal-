from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import hashlib

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
    
    # Create voter applications table (core fields only)
    c.execute('''CREATE TABLE IF NOT EXISTS voter_applications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        status VARCHAR(50) DEFAULT 'submitted',
        admin_remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')
    
    # Create personal info table
    c.execute('''CREATE TABLE IF NOT EXISTS personal_info (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        full_name VARCHAR(255) NOT NULL,
        date_of_birth DATE NOT NULL,
        gender VARCHAR(50) NOT NULL,
        FOREIGN KEY (application_id) REFERENCES voter_applications(id) ON DELETE CASCADE
    )''')
    
    # Create addresses table
    c.execute('''CREATE TABLE IF NOT EXISTS addresses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        address_line TEXT NOT NULL,
        state VARCHAR(100) NOT NULL,
        district VARCHAR(100) NOT NULL,
        pincode VARCHAR(20) NOT NULL,
        FOREIGN KEY (application_id) REFERENCES voter_applications(id) ON DELETE CASCADE
    )''')
    
    # Create identifications table
    c.execute('''CREATE TABLE IF NOT EXISTS identifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        id_proof_type VARCHAR(100) NOT NULL,
        id_proof_number VARCHAR(100) NOT NULL,
        FOREIGN KEY (application_id) REFERENCES voter_applications(id) ON DELETE CASCADE
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
    
    # Create update requests table
    c.execute('''CREATE TABLE IF NOT EXISTS update_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        application_id INT,
        field_name VARCHAR(100) NOT NULL,
        old_value TEXT,
        new_value TEXT NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        admin_remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (application_id) REFERENCES voter_applications(id) ON DELETE SET NULL
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
    
    # Get user applications with personal info from the new normalized schema
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get recent applications
    c.execute("""SELECT va.id, pi.full_name, va.status, va.created_at 
                 FROM voter_applications va
                 LEFT JOIN personal_info pi ON va.id = pi.application_id
                 WHERE va.user_id=%s 
                 ORDER BY va.created_at DESC LIMIT 5""", 
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
        
        # Validate id_proof_number based on id_proof_type
        validation_error = validate_id_proof(id_proof_type, id_proof_number)
        if validation_error:
            flash(validation_error, 'error')
            return render_template('voter/new_application.html')
        
        # Save application using the new normalized schema
        conn = get_db_connection()
        c = conn.cursor()
        
        try:
            # Insert main application record
            c.execute("INSERT INTO voter_applications (user_id) VALUES (%s)",
                      (session['user_id'],))
            
            # Get the ID of the newly inserted application
            application_id = c.lastrowid
            
            # Insert personal info
            c.execute("""INSERT INTO personal_info 
                         (application_id, full_name, date_of_birth, gender)
                         VALUES (%s, %s, %s, %s)""",
                      (application_id, full_name, date_of_birth, gender))
            
            # Insert address info
            c.execute("""INSERT INTO addresses 
                         (application_id, address_line, state, district, pincode)
                         VALUES (%s, %s, %s, %s, %s)""",
                      (application_id, address, state, district, pincode))
            
            # Insert identification info
            c.execute("""INSERT INTO identifications 
                         (application_id, id_proof_type, id_proof_number)
                         VALUES (%s, %s, %s)""",
                      (application_id, id_proof_type, id_proof_number))
            
            conn.commit()
            flash('Voter application submitted successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Error submitting application. Please try again.', 'error')
            print(f"Error: {e}")
        finally:
            conn.close()
        
        return redirect(url_for('voter_dashboard'))
    
    return render_template('voter/new_application.html')
# View Applications
@app.route('/voter/applications')
def view_applications():
    if not is_logged_in() or is_admin():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    # Get all user applications with personal info from the new normalized schema
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT va.id, pi.full_name, va.status, va.created_at 
                 FROM voter_applications va
                 LEFT JOIN personal_info pi ON va.id = pi.application_id
                 WHERE va.user_id=%s 
                 ORDER BY va.created_at DESC""", 
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
    
    # Get application with all related data from the new normalized schema
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT va.id, va.status, va.admin_remarks, va.created_at,
                        pi.full_name, pi.date_of_birth, pi.gender, 
                        a.address_line, a.state, a.district, a.pincode,
                        i.id_proof_type, i.id_proof_number
                 FROM voter_applications va
                 LEFT JOIN personal_info pi ON va.id = pi.application_id
                 LEFT JOIN addresses a ON va.id = a.application_id
                 LEFT JOIN identifications i ON va.id = i.application_id
                 WHERE va.id=%s AND va.user_id=%s""", 
              (app_id, session['user_id']))
    application = c.fetchone()
    
    if not application:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('view_applications'))
    
    # Get all election card details if application is approved
    election_cards = []
    if application[1] == 'approved':  # status column
        c.execute("SELECT election_card_number, issued_date FROM election_cards WHERE application_id=%s ORDER BY issued_date DESC", (app_id,))
        election_cards = c.fetchall()
    
    conn.close()
    
    # Convert to dict for easier access in template
    app_dict = {
        'id': application[0],
        'full_name': application[4],  # From personal_info
        'date_of_birth': application[5],  # From personal_info
        'gender': application[6],  # From personal_info
        'address': application[7],  # From addresses
        'state': application[8],  # From addresses
        'district': application[9],  # From addresses
        'pincode': application[10],  # From addresses
        'id_proof_type': application[11],  # From identifications
        'id_proof_number': application[12],  # From identifications
        'status': application[1],
        'admin_remarks': application[2],
        'created_at': application[3],
        'election_cards': election_cards  # List of all election cards
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
    
    # Get application with all related data from the new normalized schema
    c.execute("""SELECT va.id, va.user_id, va.status, va.admin_remarks, va.created_at, va.updated_at,
                        pi.full_name, pi.date_of_birth, pi.gender, 
                        a.address_line, a.state, a.district, a.pincode,
                        i.id_proof_type, i.id_proof_number
                 FROM voter_applications va
                 LEFT JOIN personal_info pi ON va.id = pi.application_id
                 LEFT JOIN addresses a ON va.id = a.application_id
                 LEFT JOIN identifications i ON va.id = i.application_id
                 WHERE va.id=%s AND va.user_id=%s""", 
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
        
        # Validate id_proof_number based on id_proof_type
        validation_error = validate_id_proof(id_proof_type, id_proof_number)
        if validation_error:
            flash(validation_error, 'error')
            # Get the existing data to populate the form
            app_dict = {
                'id': application[0],
                'user_id': application[1],
                'full_name': full_name,  # Use the form data to preserve user's input
                'date_of_birth': date_of_birth,
                'gender': gender,
                'address': address,
                'state': state,
                'district': district,
                'pincode': pincode,
                'id_proof_type': id_proof_type,
                'id_proof_number': id_proof_number,
                'status': application[2],
                'admin_remarks': application[3],
                'created_at': application[4],
                'updated_at': application[5]
            }
            conn.close()
            return render_template('voter/edit_application.html', application=app_dict)
        
        try:
            # Update personal info
            c.execute("""UPDATE personal_info 
                         SET full_name=%s, date_of_birth=%s, gender=%s
                         WHERE application_id=%s""",
                      (full_name, date_of_birth, gender, app_id))
            
            # Update address info
            c.execute("""UPDATE addresses 
                         SET address_line=%s, state=%s, district=%s, pincode=%s
                         WHERE application_id=%s""",
                      (address, state, district, pincode, app_id))
            
            # Update identification info
            c.execute("""UPDATE identifications 
                         SET id_proof_type=%s, id_proof_number=%s
                         WHERE application_id=%s""",
                      (id_proof_type, id_proof_number, app_id))
            
            # Update main application and set status to submitted
            c.execute("""UPDATE voter_applications 
                         SET status='submitted', updated_at=CURRENT_TIMESTAMP
                         WHERE id=%s AND user_id=%s""",
                      (app_id, session['user_id']))
            
            conn.commit()
            flash('Application updated successfully!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Error updating application. Please try again.', 'error')
            print(f"Error: {e}")
        finally:
            conn.close()
        
        return redirect(url_for('application_status', app_id=app_id))
    
    # Convert to dict for easier access in template
    app_dict = {
        'id': application[0],
        'user_id': application[1],
        'full_name': application[6],  # From personal_info
        'date_of_birth': application[7],  # From personal_info
        'gender': application[8],  # From personal_info
        'address': application[9],  # From addresses
        'state': application[10],  # From addresses
        'district': application[11],  # From addresses
        'pincode': application[12],  # From addresses
        'id_proof_type': application[13],  # From identifications
        'id_proof_number': application[14],  # From identifications
        'status': application[2],
        'admin_remarks': application[3],
        'created_at': application[4],
        'updated_at': application[5]
    }
    
    conn.close()
    
    return render_template('voter/edit_application.html', application=app_dict)

# Update Request Form
@app.route('/voter/update_request', methods=['GET', 'POST'])
def update_request():
    if not is_logged_in() or is_admin():
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        field_name = request.form['field_name']
        new_value = request.form['new_value']
        application_id = request.form.get('application_id')
        
        # Validate the field name
        allowed_fields = ['full_name', 'date_of_birth', 'gender', 'address', 'state', 
                         'district', 'pincode', 'id_proof_type', 'id_proof_number']
        if field_name not in allowed_fields:
            flash('Invalid field name.', 'error')
            return render_template('voter/update_request.html')
        
        # Get the old value if application_id is provided
        old_value = None
        if application_id:
            try:
                conn = get_db_connection()
                c = conn.cursor()
                
                # Get the old value based on the field name
                if field_name in ['full_name', 'date_of_birth', 'gender']:
                    c.execute("SELECT {} FROM personal_info WHERE application_id=%s".format(field_name), (application_id,))
                elif field_name in ['address', 'state', 'district', 'pincode']:
                    c.execute("SELECT {} FROM addresses WHERE application_id=%s".format(field_name), (application_id,))
                elif field_name in ['id_proof_type', 'id_proof_number']:
                    c.execute("SELECT {} FROM identifications WHERE application_id=%s".format(field_name), (application_id,))
                
                result = c.fetchone()
                if result:
                    old_value = result[0]
                
                conn.close()
            except Exception as e:
                print(f"Error retrieving old value: {e}")
        
        # Save the update request
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            c.execute("""INSERT INTO update_requests 
                         (user_id, application_id, field_name, old_value, new_value) 
                         VALUES (%s, %s, %s, %s, %s)""",
                      (session['user_id'], application_id, field_name, old_value, new_value))
            
            conn.commit()
            flash('Update request submitted successfully!', 'success')
        except Exception as e:
            if conn:
                conn.rollback()
            flash('Error submitting update request. Please try again.', 'error')
            print(f"Error submitting update request: {e}")
        finally:
            if conn:
                conn.close()
        
        return redirect(url_for('voter_dashboard'))
    
    return render_template('voter/update_request.html')


# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get pending applications with personal info from the new normalized schema
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get pending applications
    c.execute("""SELECT va.id, pi.full_name, va.status, va.created_at, u.name as user_name 
                 FROM voter_applications va 
                 JOIN users u ON va.user_id = u.id 
                 LEFT JOIN personal_info pi ON va.id = pi.application_id
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
    
    # Get application details from the new normalized schema
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT va.id, va.user_id, va.status, va.admin_remarks, va.created_at, va.updated_at,
                        u.name as user_name, u.email,
                        pi.full_name, pi.date_of_birth, pi.gender, 
                        a.address_line, a.state, a.district, a.pincode,
                        i.id_proof_type, i.id_proof_number
                 FROM voter_applications va 
                 JOIN users u ON va.user_id = u.id
                 LEFT JOIN personal_info pi ON va.id = pi.application_id
                 LEFT JOIN addresses a ON va.id = a.application_id
                 LEFT JOIN identifications i ON va.id = i.application_id
                 WHERE va.id=%s""", (app_id,))
    application = c.fetchone()
    
    if not application:
        flash('Application not found!', 'error')
        conn.close()
        return redirect(url_for('admin_dashboard'))
    
    # Get all election card details if application is approved
    election_cards = []
    if application[2] == 'approved':  # status column
        c.execute("SELECT election_card_number, issued_date FROM election_cards WHERE application_id=%s ORDER BY issued_date DESC", (app_id,))
        election_cards = c.fetchall()
    
    conn.close()
    
    # Convert to dict for easier access in template
    app_dict = {
        'id': application[0],
        'user_id': application[1],
        'full_name': application[8],  # From personal_info
        'date_of_birth': application[9],  # From personal_info
        'gender': application[10],  # From personal_info
        'address': application[11],  # From addresses
        'state': application[12],  # From addresses
        'district': application[13],  # From addresses
        'pincode': application[14],  # From addresses
        'id_proof_type': application[15],  # From identifications
        'id_proof_number': application[16],  # From identifications
        'status': application[2],
        'admin_remarks': application[3],
        'created_at': application[4],
        'updated_at': application[5],
        'user_name': application[6],
        'user_email': application[7],
        'election_cards': election_cards  # List of all election cards
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
        # Check if election card already exists for this application
        c.execute("SELECT COUNT(*) FROM election_cards WHERE application_id=%s", (app_id,))
        existing_card_count = c.fetchone()[0]
        
        if existing_card_count == 0:
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
        else:
            print(f"Election card already exists for application {app_id}, skipping creation")

    conn.commit()
    conn.close()
    
    flash('Application status updated successfully!', 'success')
    return redirect(url_for('admin_view_application', app_id=app_id))

# Admin view update requests
@app.route('/admin/update_requests')
def admin_update_requests():
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get pending update requests
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""SELECT ur.*, u.name as user_name 
                 FROM update_requests ur 
                 JOIN users u ON ur.user_id = u.id 
                 WHERE ur.status = 'pending' 
                 ORDER BY ur.created_at DESC""")
    update_requests = c.fetchall()
    
    conn.close()
    
    return render_template('admin/update_requests.html', update_requests=update_requests)

# Admin process update request
@app.route('/admin/update_request/<int:request_id>/process', methods=['GET', 'POST'])
def admin_process_update_request(request_id):
    if not is_logged_in() or not is_admin():
        flash('Access denied!', 'error')
        return redirect(url_for('login'))
    
    # Get the update request
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("SELECT * FROM update_requests WHERE id=%s", (request_id,))
        update_request = c.fetchone()
        
        if not update_request:
            flash('Update request not found!', 'error')
            conn.close()
            return redirect(url_for('admin_update_requests'))
        
        if request.method == 'POST':
            status = request.form['status']
            remarks = request.form.get('remarks', '')
            
            try:
                # Update the request status
                c.execute("UPDATE update_requests SET status=%s, admin_remarks=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                          (status, remarks, request_id))
                
                # If approved, update the actual field
                if status == 'approved':
                    field_name = update_request[3]
                    new_value = update_request[5]
                    application_id = update_request[2]
                    
                    # Update the appropriate table based on the field name
                    if field_name in ['full_name', 'date_of_birth', 'gender']:
                        c.execute(f"UPDATE personal_info SET {field_name}=%s WHERE application_id=%s",
                                  (new_value, application_id))
                    elif field_name in ['address', 'state', 'district', 'pincode']:
                        c.execute(f"UPDATE addresses SET {field_name}=%s WHERE application_id=%s",
                                  (new_value, application_id))
                    elif field_name in ['id_proof_type', 'id_proof_number']:
                        c.execute(f"UPDATE identifications SET {field_name}=%s WHERE application_id=%s",
                                  (new_value, application_id))
                    
                    # If this update is for an approved application and the field is critical,
                    # we might want to regenerate the election card
                    # For now, we'll just update the application status to 'submitted' to require re-approval
                    if application_id:
                        c.execute("UPDATE voter_applications SET status='submitted', updated_at=CURRENT_TIMESTAMP WHERE id=%s",
                                  (application_id,))
                
                conn.commit()
                flash('Update request processed successfully!', 'success')
            except Exception as e:
                conn.rollback()
                flash('Error processing update request. Please try again.', 'error')
                print(f"Error processing update request: {e}")
            finally:
                conn.close()
            
            return redirect(url_for('admin_update_requests'))
        
        conn.close()
        
        # Convert to dict for easier access in template
        request_dict = {
            'id': update_request[0],
            'user_id': update_request[1],
            'application_id': update_request[2],
            'field_name': update_request[3],
            'old_value': update_request[4],
            'new_value': update_request[5],
            'status': update_request[6],
            'admin_remarks': update_request[7],
            'created_at': update_request[8],
            'updated_at': update_request[9]
        }
        
        return render_template('admin/process_update_request.html', update_request=request_dict)
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        flash('Error accessing update request. Please try again.', 'error')
        print(f"Error accessing update request: {e}")
        return redirect(url_for('admin_update_requests'))

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Add ID proof validation function
def validate_id_proof(id_proof_type, id_proof_number):
    """
    Validate ID proof number based on ID proof type
    Returns error message if validation fails, None if valid
    """
    if not id_proof_number:
        return "ID Proof Number is required"
    
    # Clean the input
    id_proof_number = id_proof_number.strip().upper()
    
    # Validation based on ID proof type
    if id_proof_type == "Aadhaar Card":
        # Aadhaar card should be 12 digits
        if not id_proof_number.isdigit() or len(id_proof_number) != 12:
            return "Aadhaar Card number must be 12 digits"
    
    elif id_proof_type == "Pan Card":
        # PAN card should be 10 characters: 5 letters + 4 digits + 1 letter
        if len(id_proof_number) != 10 or not (id_proof_number[:5].isalpha() and 
                                              id_proof_number[5:9].isdigit() and 
                                              id_proof_number[9:].isalpha()):
            return "PAN Card number must be 10 characters (5 letters + 4 digits + 1 letter)"
    
    elif id_proof_type == "Passport":
        # Passport should start with a letter followed by digits, typically 6-9 characters
        if len(id_proof_number) < 6 or len(id_proof_number) > 9 or not (
                id_proof_number[0].isalpha() and id_proof_number[1:].isdigit()):
            return "Passport number should start with a letter followed by 5-8 digits"
    
    elif id_proof_type == "Driving License":
        # Driving license format varies by state but typically 10-16 characters
        if len(id_proof_number) < 10 or len(id_proof_number) > 16:
            return "Driving License number should be between 10-16 characters"
    
    return None  # Valid

if __name__ == '__main__':
    init_db()
    app.run(debug=True)