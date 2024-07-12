from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

db=SQLAlchemy()
app = Flask(__name__)
bcrypt=Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///doctordb.db'
app.config['SECRET_KEY']='!Qy7faRque9N~+oxx}UA406\£h}!oua7FylE#8f,]@x!L(YTWd'
db.init_app(app)

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

@login_manager.user_loader
def load_user(user_id):
    return Doctor.query.get(int(user_id))

class Doctor(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20), nullable=False, unique=True)
    password=db.Column(db.String(80), nullable=False)
    Type=db.Column(db.String(20), nullable=False)

class DoctorForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    type=SelectField(u'Type', choices=["Heart", "Bones", "Eyes", "Normal"], validate_choice=True)
    submit=SubmitField("Register")
    def validate_username(self, username):
        existing_user_username=Doctor.query.filter_by(username=username.data).first()
        if existing_user_username:
            flash("Username already taken")
            raise ValidationError("Username already taken")

class LoginForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit=SubmitField("Login")

@app.route('/', methods=['GET', 'POST'])
def doctorlogin():
    form=LoginForm()
    if form.validate_on_submit():
        user=Doctor.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('doctordashboard'))
            else:
                flash("Wrong Password! Please try again.")
        else:
            flash("Not register")
    return render_template("doctorlogin.html", form=form)

@app.route('/doctorregister', methods=['GET', 'POST'])
def doctorregister():
    form=DoctorForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data)
        new_user=Doctor(username=form.username.data, password=hashed_password, Type=form.type.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('doctorlogin'))
    return render_template("doctorregister.html", form=form)

@app.route('/doctordashboard', methods=['GET', 'POST'])
@login_required
def doctordashboard():
    return render_template("doctordashboard.html")

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    form=LoginForm()
    return render_template("doctorlogin.html", form=form)

if __name__ == '__main__':
    app.run(debug=True, port=5001)