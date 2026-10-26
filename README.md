# Cloud-Based Inventory Monitoring and Management System

## Project Overview
A Flask-based inventory management application for tracking products,
managing stock, and controlling user access.

## Features
- User login and authentication
- Administrator and Inventory Operator roles
- Add and delete products (Administrator)
- Stock In and Stock Out operations
- Low-stock threshold support
- Stock transaction history
- SQLite database

## Technology Stack
- Python
- Flask
- SQLite
- HTML
- CSS
- AWS (deployment planned)

## Project Structure
- app.py: Flask application
- templates/: HTML templates
- static/css/: CSS stylesheet
- requirements.txt: Python dependencies
- DATABASE_SCHEMA.md: Database documentation
- TEST_CASES.md: Test cases

## Run Locally
1. Create and activate a Python virtual environment.
2. Install dependencies:

   pip install -r requirements.txt

3. Start the application:

   python app.py

4. Open http://127.0.0.1:5000/ in your browser.

## Security Notes
- Do not commit database files, passwords, secret keys, or AWS credentials.
- Configure a persistent Flask secret key before deployment.
- Use a production WSGI server for production deployment.

## Deployment Status
AWS deployment and final deployment testing are pending.
