from flask import Flask, render_template, Blueprint, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import login_required, current_user, logout_user
from healthcare.models import User, Chat, App, ClientProfile, PaymentRequest
import os
from healthcare import flask_app, db

client = Blueprint('client', __name__, template_folder='templates', url_prefix='/client')


@flask_app.route('/client_panel')
def client_panel():
    # Find the admin user
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        flash('Admin not found!')
        return redirect(url_for('client_panel'))

    # Find the app associated with the current user
    app = App.query.filter_by(user_id=current_user.id).first()
    if not app:
        flash("No app details available for the current user.", "info")
        logout_user()
        return redirect(url_for('login'))  # Redirect if no app is associated

    # Find the client profile associated with the current user
    client = ClientProfile.query.filter_by(user_id=current_user.id).first()
    if not client:
        flash("No client profile found for the current user.", 'info')
        return redirect(url_for('home'))  # Redirect to a relevant page

    # Query all payment requests
    payment_requests = PaymentRequest.query.all()

    unpaid_request = PaymentRequest.query.filter_by(client_email=current_user.email, status='Unpaid').first()
    payment_request_amount = unpaid_request.amount if unpaid_request else None
    unpaid_request_exists = unpaid_request is not None

    return render_template('client_panel.html', admin=admin, app=app, client=client, payment_requests=payment_requests,
                           unpaid_request_exists=unpaid_request_exists,
                           payment_request_amount=payment_request_amount,
                           current_user=current_user)



@flask_app.route('/update_client_profile', methods=['POST'])
def update_client_profile():
    data = request.get_json()
    client_id = data.get("client_id")

    if not client_id:
        return jsonify(success=False, message="Client ID is missing"), 400

    client = ClientProfile.query.get(client_id)
    if not client:
        return jsonify(success=False, message="Client not found"), 404

    # Update client profile data
    client.specialization = data.get("specialization", client.specialization)
    client.credentials = data.get("credentials", client.credentials)
    client.experience = data.get("experience", client.experience)
    client.current_role = data.get("current_role", client.current_role)
    client.areas_of_interest = data.get("areas_of_interest", client.areas_of_interest)

    try:
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500

@flask_app.route('/app/<int:app_id>')
def view_app(app_id):
    app = App.query.get_or_404(app_id)
    return render_template('app.html', app=app)

@flask_app.route('/download_contract/<int:app_id>')
@login_required
def download_contract(app_id):
    app = App.query.get_or_404(app_id)
    if app.user_id != current_user.id:
        flash("You do not have permission to access this file.", "error")
        return redirect(url_for('client_panel'))

    contract_file = app.contract_file
    if contract_file:
        directory = os.path.join(flask_app.root_path, 'static', 'Contract_File')
        try:
            return send_from_directory(directory, contract_file, as_attachment=True)
        except FileNotFoundError:
            os.abort(404)  # Not found if the file does not exist
    else:
        flash("No contract file available for download.", "error")
        return redirect(url_for('client_panel'))

@flask_app.route('/send_message/<int:receiver_id>', methods=['POST'], endpoint='client_send_message')
@login_required
def send_message(receiver_id):
    message = request.form.get('message')
    if message:
        new_message = Chat(sender_id=current_user.id, receiver_id=receiver_id, message=message)
        db.session.add(new_message)
        db.session.commit()
    return redirect(request.referrer)


@flask_app.route('/client/chat/<int:admin_id>')
@login_required
def client_chat(admin_id):
    print(current_user.is_admin)
    if current_user.is_admin == True:
        return redirect(url_for('login'))
    admin = User.query.get_or_404(admin_id)
    chats = Chat.query.filter(
        ((Chat.sender_id == current_user.id) & (Chat.receiver_id == admin_id)) |
        ((Chat.receiver_id == current_user.id) & (Chat.sender_id == admin_id))
    ).order_by(Chat.datetime.asc())
    return render_template('client_chat.html', chats=chats, admin=admin)


