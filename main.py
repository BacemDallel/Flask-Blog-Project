from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap5
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date, datetime
from flask import flash  # Add this import for message flashing
from sqlalchemy.exc import IntegrityError
import random
from email_sender import EmailSender


'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy()
db.init_app(app)

# Configure Flask-Login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Define the database models (BlogPost, User, Comment, Vote)
# CONFIGURE TABLE
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    author = db.relationship('User', backref='posts', foreign_keys=[user_id])
    comments = db.relationship('Comment', backref='related_post', lazy=True)

    def __repr__(self):
        return f"BlogPost('{self.title}')"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def is_comment_liked(self, comment_id):
        comment = Comment.query.get(comment_id)
        if comment:
            return Vote.query.filter_by(user_id=self.id, comment_id=comment.id).first() is not None
        return False


    def __repr__(self):
        return self.username


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref='comments')
    post = db.relationship('BlogPost', backref='related_comments')
    comment_votes = db.relationship('Vote', cascade='all,delete-orphan')

    def __repr__(self):
        return f"Comment('{self.body}')"


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id', ondelete='CASCADE'))
    vote_type = db.Column(db.String(10), nullable=False)  # 'upvote' or 'downvote'

    user = db.relationship('User', backref='votes')
    comment = db.relationship('Comment')




with app.app_context():
    db.create_all()


class AddPostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# TODO: Create a RegisterForm to register new users
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email Adress", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign up")


# TODO: Create a LoginForm to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email Adress", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")



# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    body = CKEditorField("Leave a comment:", validators=[DataRequired()])
    submit = SubmitField('Submit')


# TODO: Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('register'))

        # Hash the user's password
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')

        # Create a new user object with hashed password
        new_user = User(
            username=form.name.data,
            email=form.email.data,
            password=hashed_password
        )

        # Add the new user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            # In case of any database integrity errors
            db.session.rollback()
            flash('Registration failed. Please try again later.', 'error')
            return redirect(url_for('register'))

    return render_template("register.html", form=form)


# TODO: Add voting logic
@app.route('/vote-comment/<comment_id>/<vote_type>', methods=['POST'])
@login_required
def vote_comment(comment_id, vote_type):
    comment = Comment.query.get_or_404(comment_id)
    user = current_user

    existing_vote = Vote.query.filter_by(user_id=user.id, comment_id=comment.id).first()

    if existing_vote:
        # If the user has voted for this comment before
        if existing_vote.vote_type == vote_type:
            # If the user is attempting to vote the same way again, cancel their vote
            db.session.delete(existing_vote)
            if vote_type == 'upvote':
                comment.upvotes -= 1
            else:
                comment.downvotes -= 1
        else:
            # If the user is changing their vote, update the vote type
            existing_vote.vote_type = vote_type
            if vote_type == 'upvote':
                comment.upvotes += 1
                comment.downvotes -= 1
            else:
                comment.downvotes += 1
                comment.upvotes -= 1
    else:
        # If the user is voting for the first time
        new_vote = Vote(user_id=user.id, comment_id=comment.id, vote_type=vote_type)
        db.session.add(new_vote)
        if vote_type == 'upvote':
            comment.upvotes += 1
        else:
            comment.downvotes += 1

    db.session.commit()
    return redirect(url_for('show_post', post_id=comment.post_id))

# Make a login route logic
# check for the user profile existing and password
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Find user by email entered.
        user = User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('get_all_posts'))
            else:
                flash('Invalid email or password.', 'error')
        else:
            flash('User not found.', 'error')

    return render_template('login.html', form=form)


@app.route('/')
def get_all_posts():
    # TODO: Query the database for all the posts. Convert the data to a python list.
    posts = BlogPost.query.order_by(BlogPost.id).all()

    # Fetch the current user's name
    user_name = f"{current_user.username}'s Blog" if current_user.is_authenticated else "Super Blog"

    return render_template("index.html", all_posts=posts, user_name=user_name)


# TODO: Show the profile of a user.
@app.route('/profile/<profile_id>', methods=['GET'])
def profile(profile_id):
    # Fetch the user from the database
    user = User.query.get_or_404(profile_id)
    user_name = user.username
    user_id = user.id

    # Fetch all posts by this user
    user_posts = BlogPost.query.filter_by(user_id=profile_id).all()
    return render_template('profile.html', username=user_name, user_posts=user_posts, user_id=user_id)


# TODO: Add a route so that you can click on individual posts.
@app.route('/show-post/<post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    form = CommentForm()
    requested_post = BlogPost.query.get_or_404(post_id)
    from sqlalchemy import desc

    all_comments = Comment.query.filter_by(post_id=post_id).order_by(desc(Comment.upvotes)).all()

    if form.validate_on_submit():
        # If the form is submitted, add the comment
        new_comment = Comment(
            body=form.body.data,
            user_id=current_user.id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))

    return render_template("post.html", post=requested_post, form=form, comments=all_comments)


# TODO: add_new_post() to create a new blog post
@app.route('/make-post', methods=['GET', 'POST'])
@login_required
def add_new_post():
    form = AddPostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            user_id=current_user.id,  # Assign the user_id to the current user's ID
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, post_type='New Post')


# TODO: edit_post() to change an existing blog post
@app.route('/edit-post/<post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post_to_edit = BlogPost.query.get_or_404(post_id)

    if current_user.id != post_to_edit.user_id and current_user.id != 1:
        flash("You don't have permission to edit this post.")
        # If the current user is not the author of the post, redirect back to the post

        return redirect(url_for('show_post', post_id=post_id))

    form = AddPostForm()

    if form.validate_on_submit():
        # Update the post-details with the edited form data
        post_to_edit.title = form.title.data
        post_to_edit.subtitle = form.subtitle.data
        post_to_edit.body = form.body.data
        post_to_edit.img_url = form.img_url.data

        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))

    # Populate the form with the existing post data
    form.title.data = post_to_edit.title
    form.subtitle.data = post_to_edit.subtitle
    form.author.data = current_user.username
    form.body.data = post_to_edit.body
    form.img_url.data = post_to_edit.img_url

    return render_template("make-post.html", form=form, post_type='Edit Post')


# TODO: delete_post() to remove a blog post from the database

@app.route('/delete-post/<post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    if current_user.id == post_to_delete.user_id and current_user.id != 1:
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    else:
        flash("You don't have permission to delete this post.")
        return redirect(url_for('show_post', post_id=post_id))

# Delete logic
@app.route('/delete-comment/<comment_id>', methods=['GET', 'POST'])
@login_required
def delete_comment(comment_id):
    comment_to_delete = Comment.query.get_or_404(comment_id)
    if current_user.id == comment_to_delete.user_id or current_user.id == 1:
        db.session.delete(comment_to_delete)
        db.session.commit()
        # Redirect to the post where the comment was deleted
        return redirect(url_for('show_post', post_id=comment_to_delete.post_id))
    else:
        flash("You don't have permission to delete this comment.")
        # Redirect to the same post if permission is denied
        return redirect(url_for('show_post', post_id=comment_to_delete.post_id))

# Logout route that deconect the user and redirect to home page.
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


# Define a form for changing the user's password
class ChangePasswordForm(FlaskForm):
    current_password = StringField("Current Password", validators=[DataRequired()])
    new_password = StringField("New Password", validators=[DataRequired()])
    submit = SubmitField("Apply changes")


# Define a form for changing the user's username
class ChangeUsernameForm(FlaskForm):
    new_username = StringField('New Username', validators=[DataRequired()])
    submit = SubmitField('Change Username')


# TODO: Settings.
@app.route('/settings/<setting>', methods=['GET', 'POST'])
@login_required
def settings(setting):
    # Create instances of ChangePasswordForm and ChangeUsernameForm
    change_password_form = ChangePasswordForm()
    change_username_form = ChangeUsernameForm()

    # Logic for changing password if 'Security' setting is selected
    if setting == 'Security' and change_password_form.validate_on_submit():
        # Fetch the user's profile
        user = User.query.get_or_404(current_user.id)

        # Extract form data
        current_password = change_password_form.current_password.data
        new_password = change_password_form.new_password.data

        # Check if the entered current password matches the user's actual password
        if check_password_hash(user.password, current_password):
            # Hash and update the new password
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.password = hashed_password
            db.session.commit()

            flash('Password changed successfully!', 'success')
            return redirect(url_for('settings', setting='Security'))
        else:
            flash('Incorrect current password. Please try again.', 'error')

    # Logic for changing username if 'Account' setting is selected
    if setting == 'Account' and change_username_form.validate_on_submit():
        new_username = change_username_form.new_username.data

        # Check if the new username already exists in the database
        existing_user = User.query.filter_by(username=new_username).first()

        if not existing_user:
            # Fetch the user's profile
            user = User.query.get_or_404(current_user.id)

            # Update the user's username
            user.username = new_username
            db.session.commit()

            flash('Username changed successfully!', 'success')
            return redirect(url_for('settings', setting='Account'))
        else:
            flash('Username already exists. Please choose a different username.', 'error')

    # Render the settings template with forms and setting information
    return render_template('settings.html', setting=setting, change_password_form=change_password_form,
                           change_username_form=change_username_form)



# Define a form for reseting user's password if forgottent.
class ResetPasswordForm(FlaskForm):
    email = StringField("Please enter your email to search for your account.", validators=[DataRequired()])
    submit = SubmitField("Search")


class ResetPasswordForm(FlaskForm):
    # Form field for entering the email to search for the user's account
    email = StringField("Please enter your email to search for your account.", validators=[DataRequired()])
    # Button to submit the email for password reset
    submit = SubmitField("Search")

@app.route('/reset-password/', methods=['GET', 'POST'])
def reset_password():
    # Create an instance of the ResetPasswordForm
    reset_form = ResetPasswordForm()

    if reset_form.validate_on_submit():
        email = reset_form.email.data
        # Check if the entered email exists in the database
        user_email = User.query.filter_by(email=email).first()

        if user_email:
            # Generate a random token for password reset
            token = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            email_sender = EmailSender(email)

            # Send an email to the user with the generated token
            email_sent = email_sender.send_email(token)

            if email_sent:
                # Email sent successfully, store the token in the session for verification
                session['reset_token'] = token

                # Redirect to a page for entering the token received in the email
                return redirect(url_for('enter_token', email=email))
            else:
                # Failed to send email
                flash('Failed to send email. Please try again.', 'error')
        else:
            # Invalid email entered
            flash('Invalid email!', 'error')

    # Render the reset-password.html template with the reset_form
    return render_template('reset-password.html', reset_form=reset_form)



class TokenForm(FlaskForm):
    # Form field for entering the token code sent to the user's email
    token = StringField("Please enter the token code sent to your email:", validators=[DataRequired()])
    # Button to submit the token
    submit = SubmitField("Submit")

@app.route('/enter-token/<email>', methods=['GET', 'POST'])
def enter_token(email):
    token_form = TokenForm()  # Create an instance of the TokenForm

    if token_form.validate_on_submit():
        entered_token = token_form.token.data
        # Retrieve the expected token sent to the user's email for verification
        expected_token = session.get('reset_token')  # Retrieve the expected token from the session

        if entered_token == expected_token:
            # Token matches, proceed to reset password for the provided email
            return redirect(url_for('reset_password_process', email=email))
        else:
            # Invalid token entered, redirect to enter the token again
            flash('Invalid token. Please try again.', 'error')
            return redirect(url_for('enter_token', email=email))

    # Render the enter-token.html template with the token_form and email
    return render_template('enter-token.html', token_form=token_form, email=email)



@app.route('/resend/<email>', methods=['GET', 'POST'])
def resend_token(email):
    token_form = TokenForm()  # Create an instance of the TokenForm to capture the token

    user_email = User.query.filter_by(email=email).first()

    if user_email:
        # Generate a random token
        token = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        email_sender = EmailSender(email)

        # Send an email with the generated token
        email_sent = email_sender.send_email(token)

        if email_sent:
            # Email sent successfully, store the token in the session for verification
            session['reset_token'] = token

            # Redirect to a page where users can enter the token received in their email
            return redirect(url_for('enter_token', email=email))
        else:
            # Failed to send email
            flash('Failed to send email. Please try again.', 'error')
    else:
        # Invalid email entered
        flash('Invalid email!', 'error')

    # Render the enter-token.html template with the token_form and email
    return render_template('enter-token.html', token_form=token_form, email=email)



class ResetPasswordProcess(FlaskForm):
    # Form field for entering the new password
    new_password = StringField("Enter your new password", validators=[DataRequired()])
    # Button to submit the new password
    submit = SubmitField("Search")

@app.route('/reset-password-process/<email>', methods=['GET', 'POST'])
def reset_password_process(email):
    reset_password_form = ResetPasswordProcess()

    if reset_password_form.validate_on_submit():
        # Retrieve the user based on the provided email
        user = User.query.filter_by(email=email).first()

        if user:
            new_password = reset_password_form.new_password.data
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            user.password = hashed_password
            db.session.commit()

            flash('Password reset successfully!', 'success')
            return redirect(url_for('login'))  # Redirect to the login page after successful password reset
        else:
            flash('Invalid user!', 'error')
            return redirect(url_for('login'))  # Redirect to the login page or reset-password page

    # Render the reset_password_process.html template with the reset_password_form
    return render_template('reset_password_process.html', reset_password_form=reset_password_form)




if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
