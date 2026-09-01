

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Regexp

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def strip_whitespace(value):
    if value is not None:
        return value.strip()
    return value


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        filters=[strip_whitespace],
        validators=[
            DataRequired(message="Email is required."),
            Regexp(EMAIL_PATTERN, message="Enter a valid email address.")
        ]
    )
    password = PasswordField("Password", validators=[DataRequired(message="Password is required.")])
    submit = SubmitField("Log In")