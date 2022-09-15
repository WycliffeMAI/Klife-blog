from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, URL, Length
from flask_ckeditor import CKEditorField


# WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField('submit comment')
