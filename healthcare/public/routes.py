from datetime import datetime
from sqlite3 import IntegrityError

from flask import render_template, Blueprint, request, redirect, url_for, flash
from flask_login import login_user, logout_user

from healthcare import flask_app, db, bcrypt
from healthcare.models import Enquiry, ResetLink
from healthcare.models import User
from healthcare.public.forms import LoginForm

public = Blueprint('public', __name__, template_folder='templates', url_prefix='/public')


@flask_app.route('/about')
def about():  # put flask_application's code here
    return render_template('about.html')


@flask_app.route('/')
@flask_app.route('/home')
def home():  # put flask_application's code here
    return render_template('home.html')


@flask_app.route('/enquiry', methods=['GET'])
def enquiry():
    return render_template('enquiry.html')


@flask_app.route('/enquiry', methods=['POST'])
def submit_enquiry():
    # Process the submitted form data and save it to the database
    fullname = request.form.get('fullname')
    business_email = request.form.get('business_email')
    company_name = request.form.get('company_name')
    phone = request.form.get('phone')
    description = request.form.get('description')

    # Creating a new Enquiry instance
    enquiry = Enquiry(
        fullname=fullname,
        business_email=business_email,
        company_name=company_name,
        phone=phone,
        description=description,
        datetime=datetime.utcnow(),
        status="New"  # Assuming a default status for new enquiries
    )
    # Adding the new enquiry to the database
    db.session.add(enquiry)
    try:
        # existing code to process form and add to DB
        db.session.commit()
        flash('Your enquiry has been submitted successfully! We will get back to you shortly.', 'success')
    except IntegrityError as e:
        db.session.rollback()
        flash('This email or phone number has already been used for an enquiry.', 'error')
    except Exception as e:
        db.session.rollback()
        flash('Error: Unable to submit enquiry. Please try again.', 'error')
        print(e)  # or log to a file or logging service

    # Redirect to the enquiry page or elsewhere after successful form submission
    return redirect(url_for('enquiry'))
    # put flask_application's code here


@flask_app.route('/faq')
def faq():  # put flask_application's code here
    return render_template('faq.html')


@flask_app.route('/login', methods=['GET', 'POST'])
def login():  # put flask_application's code here
    form = LoginForm()
    # if current_user.is_authenticated:
    #     return redirect(url_for('managerDashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Please check your user details and try again.', 'danger')
            return redirect(url_for('login'))

        if not bcrypt.check_password_hash(user.password, password):
            flash('Please check your user details and try again.', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=True)
        return redirect_flask_appropriate_dashboard(user.is_admin)
    return render_template('login.html', form=form)


def redirect_flask_appropriate_dashboard(role):
    if role == True:
        return redirect(url_for('admin_panel'))
    elif role == False:
        return redirect(url_for('client_panel'))
    else:
        flash('Your account does not have a valid role assigned. Please contact support.', 'warning')
        return redirect(url_for('login'))


@flask_app.route("/forgot_password/<token>", methods=['GET', 'POST'])
def forgot_password(token):
    reset_request = ResetLink.query.filter_by(token=token).first()
    if not reset_request:
        flash('Invalid or expired token. Please try again.', 'danger')
        return redirect(url_for('login'))

    if reset_request.is_expired():
        flash('Invalid or expired token. Please try again.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('forgot_password', token=token))

        user = reset_request.user
        user.password = bcrypt.generate_password_hash(new_password)
        db.session.delete(reset_request)
        db.session.commit()
        flash('Password updated successfully. You can now login.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html'
                           , token=token)


@flask_app.route("/email_for_otp", methods=['GET', 'POST'])
def email_for_otp():
    if request.method == 'POST':
        user_email = request.form.get('email')
        user = User.query.filter_by(email=user_email).first()
        if not user:
            flash('Please check your user details and try again.', 'danger')
            return redirect(url_for('forgot_password'))

        reset_link = ResetLink(user=user)
        db.session.add(reset_link)
        db.session.commit()

        flash("Reset link has been sent to your email address, Make sure to check your spam folder as well", 'success')
        reset_link.send_reset_email(url_for('forgot_password', token=reset_link.token, _external=True))
        return redirect(url_for('login'))

    return render_template('email_for_otp.html')


@flask_app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
