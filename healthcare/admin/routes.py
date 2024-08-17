import os

from flask import Flask, render_template, Blueprint, jsonify, request, flash, redirect, url_for, abort, session
from flask_bcrypt import generate_password_hash
from datetime import datetime

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from healthcare import flask_app, db
from healthcare.models import Enquiry, ClientProfile, User, App, Chat, PaymentRequest

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@flask_app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():  # put flask_application's code here
    new_enquiries_exist = Enquiry.query.filter_by(status='New').count() > 0

    clients = User.query.filter_by(is_admin=False).all()
    apps = App.query.join(User, App.user_id == User.id).filter_by(is_admin=False).all()

    return render_template('admin_panel.html', new_enquiries_exist=new_enquiries_exist, apps=apps, clients=clients)


@flask_app.route('/update_app_status', methods=['POST'])
def update_app_status():
    data = request.get_json()
    app_id = data.get("app_id")
    new_status = data.get("status")
    print(app_id, new_status)

    if not app_id or not new_status:
        return jsonify(success=False, message="Invalid data"), 400

    app = App.query.get(app_id)
    if not app:
        return jsonify(success=False, message="App not found"), 404

    try:
        app.status = new_status
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500


# @flask_app.route('/request_payment', methods=['POST'])
# def request_payment():
#     data = request.get_json()
#     app_id = data.get("app_id")
#
#     if not app_id:
#         return jsonify(success=False, message="Invalid data"), 400
#
#     app = App.query.get(app_id)
#     if not app:
#         return jsonify(success=False, message="App not found"), 404
#
#     try:
#         app.request_payment = True
#         db.session.commit()
#         return jsonify(success=True)
#     except Exception as e:
#         db.session.rollback()
#         return jsonify(success=False, message=str(e)), 500


@flask_app.route('/check_new_enquiries')
def check_new_enquiries():
    new_enquiries_exist = Enquiry.query.filter_by(status='New').count() > 0
    return jsonify(new_enquiries_exist=new_enquiries_exist)


@flask_app.route('/mark_enquiries_viewed')
def mark_enquiries_viewed():
    try:
        # Update the status of all 'New' enquiries to 'Viewed'
        new_enquiries = Enquiry.query.filter_by(status='New').all()
        for enquiry in new_enquiries:
            enquiry.status = 'Viewed'
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify(success=False), 500


# @flask_app.route('/user_setup', methods=['GET', 'POST'])
# def user_setup():  # put flask_application's code here@flask_app.route('/user_setup', methods=['GET', 'POST'])
#     if request.method == 'POST':
#         username = request.form.get('username')
#         fullname = request.form.get('fullname')
#         password = request.form.get('password')
#         email = request.form.get('email')
#         phone = request.form.get('phone')
#
#         hashed_password = generate_password_hash(password)
#         user = User(username=username, fullname=fullname, password=hashed_password, email=email, phone=phone)
#         db.session.add(user)
#         db.session.flush()
#
#         client_profile = ClientProfile(user_id=user.id, created_at=datetime.utcnow())
#         db.session.add(client_profile)
#         db.session.commit()
#         flash('User created successfully!', 'success')
#         return redirect(url_for('user_setup'))
#
#     users = User.query.filter_by(is_admin=False).all()
#     clients = ClientProfile.query.all()
#     return render_template('user_setup.html', users=users, clients=clients)


#***********************************************************************************************************

@flask_app.route('/user_setup', methods=['GET', 'POST'])
def user_setup():
    if request.method == 'POST':
        username = request.form.get('username')
        fullname = request.form.get('fullname')
        password = request.form.get('password')
        email = request.form.get('email')
        phone = request.form.get('phone')
        print(fullname)
        hashed_password = generate_password_hash(password)
        user = User(username=username, fullname=fullname, password=hashed_password, email=email, phone=phone)
        db.session.add(user)
        db.session.flush()

        client_profile = ClientProfile(user_id=user.id, created_at=datetime.utcnow())
        db.session.add(client_profile)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('user_setup'))

    users = User.query.filter_by(is_admin=False).all()
    clients = ClientProfile.query.all()
    enquiries = Enquiry.query.all()  # Fetch all enquiries from the database
    return render_template('user_setup.html', users=users, clients=clients, enquiries=enquiries)



@flask_app.route('/app_details', methods=['GET', 'POST'])
def app_details():
    app_logo = None

    if request.method == 'POST':
        app_name = request.form.get('app_name')
        app_url = request.form.get('app_url')
        client_email = request.form.get('client_email')
        description = request.form.get('description')
        price = request.form.get('price')
        deadline = request.form.get('deadline')
        assigned_to = request.form.get('assigned_to')
        status = request.form.get('status')

        user = User.query.filter_by(email=client_email).first()
        if not user:
            flash('App details successfully added.', 'error')
            return render_template('app_details.html', app_logo=app_logo)

        if 'app_logo' in request.files:
            file = request.files['app_logo']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(flask_app.config['APP_LOGO'], filename)
                file.save(filepath)
                app_logo = filename
        else:
            flash('No App Icon provided.', 'danger')

        contract_file = None
        if 'contract_file' in request.files:
            file = request.files['contract_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(flask_app.config['CONTRACT_FILE'], filename)
                file.save(filepath)
                contract_file = filename
            else:
                flash('No file part or invalid file name.', 'error')

        if not contract_file:
            flash('No file selected or file upload failed.', 'error')
        else:
            new_app = App(
                user_id=user.id,  # Link the flask_application to the user via user_id
                app_name=app_name,
                app_url=app_url,
                app_logo=app_logo,
                description=description,
                price=price,
                deadline=deadline,
                assigned_to=assigned_to,
                status=status,
                contract_file=contract_file
            )
            db.session.add(new_app)
            db.session.commit()
            flash('Project details submitted successfully.', 'success')
            return redirect(url_for('app_details'))

    # Check for an existing app logo
    existing_app = App.query.first()
    if existing_app:
        app_logo = existing_app.app_logo

    users = User.query.filter_by(is_admin=False) # Fetch all users from the database
    return render_template('app_details.html', app_logo=app_logo, users=users)


@flask_app.route('/clients')
def clients():  # put flask_application's code here
    search_query = request.args.get('search', '')
    if search_query:
        clients = ClientProfile.query.join(User).filter(User.is_admin == False,
                                                        User.fullname.like(f'%{search_query}%')).all()
    else:
        clients = ClientProfile.query.filter(User.is_admin == False).all()

    return render_template('clients.html', clients=clients)


@flask_app.route('/client_profile/<int:client_id>')
def client_profile(client_id):
    client = ClientProfile.query.join(User).filter(User.id == client_id, User.is_admin == False).first()
    if not client:
        abort(404)
    return render_template('client_profile.html', client=client)

@flask_app.route('/edit_client_profile/<int:client_id>', methods=['GET', 'POST'])
def edit_client_profile(client_id):
    client = ClientProfile.query.get_or_404(client_id)
    print(client)
    if request.method == 'POST':
        client.user.fullname = request.form.get('fullname')
        client.user.username = request.form.get('username')
        client.user.email = request.form.get('email')
        client.user.phone = request.form.get('phone')

        new_password = request.form.get('new-password')
        if new_password:
            client.user.password = generate_password_hash(new_password)

        db.session.commit()
        return redirect(url_for('edit_client_profile', client_id=client_id))
    flash('Client profile updated successfully!', 'success')
    return render_template('edit_client_profile.html', client=client)

@flask_app.route('/admin/chat/<int:client_id>')
@login_required
def admin_chat(client_id):
    if not current_user.is_admin:
        return redirect(url_for('login'))
    client = User.query.get_or_404(client_id)
    chats = Chat.query.filter(
        ((Chat.sender_id == current_user.id) & (Chat.receiver_id == client_id)) |
        ((Chat.receiver_id == current_user.id) & (Chat.sender_id == client_id))
    ).order_by(Chat.datetime.asc())
    return render_template('admin_chat.html', chats=chats, client=client)

@flask_app.route('/enquiry_requests')
def enquiry_requests():  # put flask_application's code here
    all_enquiries = Enquiry.query.all()
    mark_enquiries_viewed()
    return render_template('enquiry_requests.html', enquiries=all_enquiries)


@flask_app.route('/send_message/<int:receiver_id>', methods=['POST'], endpoint='admin_send_message')
@login_required
def send_message(receiver_id):
    message = request.form.get('message')
    if message:
        new_message = Chat(sender_id=current_user.id, receiver_id=receiver_id, message=message)
        db.session.add(new_message)
        db.session.commit()
    return redirect(request.referrer)



@flask_app.route('/payment')
def payment():
    apps = App.query.all()
    app_details = []

    for app in apps:
        user = User.query.get(app.user_id)
        app_details.append({
            'id': app.id,
            'app_name': app.app_name,
            'client_name': user.fullname if user else '',
            'client_email': user.email if user else '',
            'deadline': app.deadline,
            'assigned_to': app.assigned_to,
            'status': app.status,
            'price': app.price
        })

    payment_requests = PaymentRequest.query.all()

    return render_template('payment.html', app_details=app_details, payment_requests=payment_requests)


@flask_app.route('/request_payment', methods=['POST'])
def request_payment():
    app_id = request.form['app_id']
    price = request.form['price']
    app = App.query.get(app_id)
    user = User.query.get(app.user_id)

    if app and user:
        new_payment = PaymentRequest(
            app_id=app.id,
            client_name=user.fullname,
            client_email=user.email,
            amount=price,
            status='Unpaid'
        )

        db.session.add(new_payment)
        app.request_payment = True
        db.session.commit()

        new_payment.send_payment_request_email()

        # Set session variables for the unpaid request
        session['unpaid_request_exists'] = True
        session['payment_request_amount'] = price  # Assuming price is the amount

        return jsonify({'success': True, 'app_id': app_id})

    return jsonify({'success': False})


@flask_app.route('/mark_as_paid/<int:payment_id>', methods=['POST'])
def mark_as_paid(payment_id):
    payment = PaymentRequest.query.get(payment_id)
    if payment:
        payment.status = 'Paid'
        db.session.commit()
        return jsonify({'success': True})

    return jsonify({'success': False})


@flask_app.route("/delete_client_profile/<int:client_id>")
def delete_client_profile(client_id):
    client = ClientProfile.query.get(client_id)
    user = client.user
    if client:
        db.session.delete(client)
        db.session.commit()
        flash("Client profile deleted successfully!", "success")

    return redirect(request.referrer)


