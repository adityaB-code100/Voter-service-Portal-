# Voter Service Portal

A Flask-based web application for voter registration and ID management.

## Features

### For Voters
- User registration and authentication
- Submit new voter applications
- Track application status
- Request updates to personal information
- View issued election cards

### For Administrators
- Review pending voter applications
- Approve or reject applications
- Process update requests
- Manage election cards

## Technology Stack

- **Backend**: Flask 2.3.3 (Python)
- **Database**: MySQL
- **Database Connector**: PyMySQL 1.1.0
- **Frontend**: HTML5, CSS3, JavaScript
- **Template Engine**: Jinja2 (built into Flask)

## Project Structure

```
Voter Service Portal/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── static/            # Static assets (CSS, JS)
├── templates/         # HTML templates
│   ├── admin/         # Admin-specific pages
│   └── voter/         # Voter-specific pages
└── documentation/     # Project documentation
    ├── database_diagram.md          # Database ER diagram
    ├── database_structure.md         # Database structure details
    ├── database_er_diagram.md        # Alternative database diagram
    └── PROJECT_STRUCTURE.md         # Full project structure documentation
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure database settings in `app.py` (Add Your Password)
4. Run the application:
   ```bash
   python app.py
   ```

## Database Schema

The application uses a normalized database structure with the following tables:
- `users`: User account information
- `voter_applications`: Main application records
- `personal_info`: Personal details for applications
- `addresses`: Address information
- `identifications`: ID proof details
- `election_cards`: Generated election cards
- `update_requests`: User update requests

## Usage

1. Start the application with `python app.py`
2. Access the portal at `http://localhost:5000`
3. Register as a new user or login as admin (default: admin@example.com / admin123)
4. Voters can submit applications and track their status
5. Administrators can review and approve applications

## Security

- Passwords are hashed using SHA-256
- Session-based authentication
- Role-based access control
- Input validation on both client and server sides

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is for  Made for educational purposes only.
Made By 
1) Aditya Bandewar
2) Pawan Wadje