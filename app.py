from flask import Flask, render_template, request, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os




app = Flask(__name__)
# Configure your database URI (using SQLite here for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24).hex() #this is used to encrypt the session cookie


login_manager = LoginManager(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        hashed_password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            username=request.form['username'],
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            return "Invalid email or password"
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
# ----- Model -----
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __repr__(self):
        return f"BlogPost('{self.title}', '{self.date_created}')"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    posts = db.relationship('BlogPost', backref='author', lazy=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True) #when a user signs up, they are active


# ----- Routes -----
@app.route('/')
def index():
    if current_user.is_authenticated:
        posts = BlogPost.query.order_by(BlogPost.date_created.desc()).all()
        return render_template('index.html', posts=posts)
    else:
        return redirect(url_for('welcome'))


@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        new_post = BlogPost(title=title, content=content)
        new_post.author_id = current_user.id
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('create_post.html')


@app.route('/user/<int:user_id>')
@login_required
def user_posts(user_id):
    user = User.query.get_or_404(user_id)
    posts = BlogPost.query.filter_by(author=user).order_by(BlogPost.date_created.desc()).all()
    return render_template('user_posts.html', user=user, posts=posts)

@app.route('/search', methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '')
    posts = BlogPost.query.filter(BlogPost.title.contains(query) | BlogPost.content.contains(query)).all()
    return render_template('index.html', posts=posts)

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('view_post', post_id=post.id))

    return render_template('edit_post.html', post=post)


@app.route('/delete/<int:post_id>')
@login_required
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

