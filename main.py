from functools import wraps
from dotenv import load_dotenv

from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import os

app = Flask(__name__)
load_dotenv()
key_ = os.environ.get("SECRET_KEY")
if key_:
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
else:
    app.config['SECRET_KEY'] = os.getenv("app.config['SECRET_KEY']")
# personal_access_token_GitHub = os.getenv("personal_access_token_GitHub")
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
uri = os.getenv("DATABASE_URL")  # or other relevant config var
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
else:
    uri = 'sqlite:///blog.db'
    
app.config['SQLALCHEMY_DATABASE_URI'] = uri

# rest of connection code using the connection string `uri`
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(
    app,
    size=100,
    rating='g',
    default='retro',
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    
    return decorated_function


# CONFIGURE TABLES
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = db.relationship("BlogPost", backref="author")
    comments = db.relationship("Comment", backref="comment_author")


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    comments = db.relationship("Comment", backref="parent_post")


class Comment(UserMixin, db.Model):
    __tablename__ = "Comments"
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    
    comment_poster = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_commented = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))


# db.create_all()


@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User.query.filter_by(email=form.email.data).first()
        if new_user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        else:
            new_user = User(
                email=form.email.data,
                name=form.username.data,
                password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            
            return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("get_all_posts", name=user.name))
            else:
                flash('Password incorrect, please try again.')
                return redirect(url_for('login'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout', methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            comment = Comment(
                comment=form.comment_text.data,
                comment_poster=current_user.id,
                post_commented=requested_post.id
            )
            db.session.add(comment)
            db.session.commit()
            return redirect(url_for("show_post", post_id=requested_post.id))
        else:
            flash('Please login to comment.')
            return redirect(url_for('login'))
    comments = Comment.query.all()
    return render_template("post.html", post=requested_post, current_user=current_user, form=form, comments=comments)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    
    return render_template("make-post.html", form=form, current_user=current_user)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=current_user,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
