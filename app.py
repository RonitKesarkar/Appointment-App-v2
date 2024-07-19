from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import datetime 

db=SQLAlchemy()
app = Flask(__name__)
bcrypt=Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///userdb.db'
app.config['SQLALCHEMY_BINDS']={"doctor":'sqlite:///doctordb.db',
                                "bookings":'sqlite:///bookings.db'}
app.config['SECRET_KEY']='!Qy7faRque9N~+oxx}UA406\£h}!oua7FylE#8f,]@x!L(YTWd'
db.init_app(app)

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20), nullable=False, unique=True)
    password=db.Column(db.String(80), nullable=False)

class Doctor(db.Model, UserMixin):
    __bind_key__="doctor"
    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20), nullable=False, unique=True)
    password=db.Column(db.String(80), nullable=False)
    Type=db.Column(db.String(20), nullable=False)

class Booking(db.Model, UserMixin):
    __bind_key__="bookings"
    id=db.Column(db.Integer, primary_key=True)
    userid=db.Column(db.Integer, nullable=False)
    doctorid=db.Column(db.Integer, nullable=False)
    doctorname=db.Column(db.String)
    username=db.Column(db.String)
    date=db.Column(db.String)
    starttime=db.Column(db.String)
    endtime=db.Column(db.String)
    timetaken=db.Column(db.String)
    mode=db.Column(db.String)
    def __repr__(self)->str:
        return f"{self.id} - {self.title}"

class RegisterForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit=SubmitField("Register")
    def validate_username(self, username):
        existing_user_username=User.query.filter_by(username=username.data).first()
        if existing_user_username:
            flash("Username already taken")
            raise ValidationError("Username already taken")

class LoginForm(FlaskForm):
    username=StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password=PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit=SubmitField("Login")

@app.route('/', methods=['GET', 'POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return render_template("dashboard.html", user=user)
            else:
                flash("Wrong Password! Please try again.")
    return render_template("login.html", form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data)
        new_user=User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html", form=form)

@app.route('/dashboard/<int:id>', methods=['GET', 'POST'])
@login_required
def dashboard(id):
    user=User.query.filter_by(id=id).first()
    return render_template("dashboard.html",user=user)

@app.route('/myappointments/<int:id>', methods=['GET', 'POST'])
@login_required
def myappointments(id):
    user=User.query.filter_by(id=id).first()
    bookings=Booking.query.filter_by(userid=id, mode="Patient").order_by(Booking.id.desc()).all()
    return render_template("myappointments.html",user=user,bookings=bookings)

@app.route('/completedappointments/<int:id>', methods=['GET', 'POST'])
@login_required
def completedappointments(id):
    user=User.query.filter_by(id=id).first()
    bookings=Booking.query.filter_by(userid=id, mode="Completed").order_by(Booking.id.desc()).all()
    return render_template("completedappointments.html",user=user,bookings=bookings)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/doctortype/<type>/<int:id>', methods=['GET', 'POST'])
@login_required
def doctortype(type, id):
    doctors=db.session.query(Doctor).filter_by(Type=type).all()
    user=User.query.filter_by(id=id).first()
    return render_template("doctortype.html", doctors=doctors, user=user)

@app.route('/book/<int:doctorid>/<int:userid>', methods=['GET', 'POST'])
@login_required
def book(doctorid,userid):
    doctor=Doctor.query.filter_by(id=doctorid).first()
    checkupdate(doctor)
    user=User.query.filter_by(id=userid).first()
    booking=db.session.query(Booking).filter_by(doctorid=doctor.id).order_by(Booking.id.desc()).first()
    return render_template("book.html", doctor=doctor, booking=booking, user=user)

@app.route('/booked/<int:doctorid>/<int:userid>', methods=['GET', 'POST'])
@login_required
def booked(doctorid,userid):
    last_booking=db.session.query(Booking).filter_by(doctorid=doctorid).order_by(Booking.id.desc()).first()
    date=datetime.datetime.now()
    update_date=date.strftime("%d/%m/%y")
    user_id=userid
    doctor_id=doctorid
    doctor=Doctor.query.filter_by(id=doctorid).first()
    doctor_name=doctor.username
    user=User.query.filter_by(id=userid).first()
    user_name=user.username
    current_date=update_date
    start_time=last_booking.endtime
    temp_time=datetime.datetime.strptime(last_booking.endtime,"%H:%M:%S")+datetime.timedelta(minutes=15)
    end_time=temp_time.strftime("%H:%M:%S")
    time_taken="15"
    mode="Patient"
    booked=Booking(userid=user_id, doctorid=doctor_id, doctorname=doctor_name, username=user_name, date=current_date, starttime=start_time, endtime=end_time, timetaken=time_taken, mode=mode)
    db.session.add(booked)
    db.session.commit()
    doctor=Doctor.query.filter_by(id=doctorid).first()
    flash("Your appointment is scheduled at"+last_booking.endtime)
    user=User.query.filter_by(id=userid).first()
    return render_template("dashboard.html", user=user)

with app.app_context():
    def checkupdate(doctor):
        print(doctor)
        if db.session.query(Booking).filter_by(doctorid=doctor.id).order_by(Booking.id.desc()).first():
            date=datetime.datetime.now()
            date=date.replace(minute=00, hour=10, second=00)
            update_date=date.strftime("%d/%m/%y")
            booking=db.session.query(Booking).filter_by(doctorid=doctor.id).order_by(Booking.id.desc()).first()
            if update_date!=booking.date:
                user_id=doctor.id
                doctor_id=doctor.id
                doctor=Doctor.query.filter_by(id=doctor.id).first()
                doctor_name=doctor.username
                user_name="Initial Booking"
                current_date=update_date
                start_time=date.strftime("%H:%M:%S")
                end_time=date.strftime("%H:%M:%S")
                time_taken="0"
                mode="Initial"
                booked=Booking(userid=user_id, doctorid=doctor_id, doctorname=doctor_name, username=user_name, date=current_date, starttime=start_time, endtime=end_time, timetaken=time_taken, mode=mode)
                db.session.add(booked)
                db.session.commit()
        else:
            date=datetime.datetime.now()
            date=date.replace(minute=00, hour=10, second=00)
            update_date=date.strftime("%d/%m/%y")
            user_id=doctor.id
            doctor_id=doctor.id
            doctor=Doctor.query.filter_by(id=doctor.id).first()
            doctor_name=doctor.username
            user_name="Initial Booking"
            current_date=update_date
            start_time=date.strftime("%H:%M:%S")
            end_time=date.strftime("%H:%M:%S")
            time_taken="0"
            mode="Initial"
            booked=Booking(userid=user_id, doctorid=doctor_id, doctorname=doctor_name, username=user_name, date=current_date, starttime=start_time, endtime=end_time, timetaken=time_taken, mode=mode)
            db.session.add(booked)
            db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
