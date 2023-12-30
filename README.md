Flask Blog Project
This project is a blog web application developed using Flask, SQLAlchemy, Flask-Login, Flask-WTF, and other related libraries. It allows users to register, create blog posts, leave comments, and perform various account-related functions.

Installation
Clone this repository to your local machine using git clone https://github.com/your_username/Flask-Blog.git.

Navigate into the project directory.

Set up a virtual environment:

bash
Copy code
# On Windows
python -m venv venv
# On macOS and Linux
python3 -m venv venv
Activate the virtual environment:

bash
Copy code
# On Windows
venv\Scripts\activate
# On macOS and Linux
source venv/bin/activate
Install the required packages:

bash
Copy code
pip install -r requirements.txt
Set up the database:

Modify the SQLALCHEMY_DATABASE_URI in app.py to your preferred database (SQLite, PostgreSQL, etc.).

Run the following commands:

bash
Copy code
python
from app import db
db.create_all()
exit()
Usage
Run the Flask application:

bash
Copy code
python app.py
Access the application in your browser at http://localhost:5000.

Features
User Registration and Authentication: Users can register accounts and log in securely.
Create and Edit Blog Posts: Authenticated users can create, edit, and delete their blog posts.
Leave Comments: Users can leave comments on blog posts.
User Profile: View individual user profiles and their authored posts.
Change Password and Username: Users can change their account password and username.
Reset Password: Users can reset their account password using the reset functionality.
Contributing
Contributions are welcome! Feel free to open issues and pull requests.

License
This project is licensed under the MIT License - see the LICENSE file for details.
