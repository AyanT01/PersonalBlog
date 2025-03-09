from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Configure your database URI (using SQLite here for simplicity)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----- Model -----
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


    def __repr__(self):
        return f"BlogPost('{self.title}', '{self.date_created}')"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    posts = db.relationship('BlogPost', backref='author', lazy=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)



# ----- Routes -----
@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_created.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)


@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        new_post = BlogPost(title=title, content=content)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('create_post.html')


@app.route('/user/<int:user_id>')
def user_posts(user_id):
    user = User.query.get_or_404(user_id)
    posts = BlogPost.query.filter_by(author=user).order_by(BlogPost.date_created.desc()).all()
    return render_template('user_posts.html', user=user, posts=posts)

@app.route('/search', methods=['GET'])
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
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

