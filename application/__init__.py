from flask import Flask
from config import configure_app
from database_config import init_db

# Initialize the Flask app
app = Flask(__name__)

# Configure the app
configure_app(app)

# Initialize the database
db = init_db(app)

# Import routes after app and db are initialized to avoid circular imports
from application import routes