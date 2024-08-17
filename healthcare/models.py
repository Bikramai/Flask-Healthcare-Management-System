import uuid
from datetime import datetime, timedelta

from flask_login import UserMixin, current_user
from flask_mail import Message

from healthcare import db, login_manager, mail


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(100), unique=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    app = db.relationship('App', backref='user', lazy=True, cascade='all, delete')


class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    business_email = db.Column(db.String(100), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(100), nullable=False)


class ClientProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    specialization = db.Column(db.String(100), nullable=True)
    credentials = db.Column(db.String(100), nullable=True)
    experience = db.Column(db.String(100), nullable=True)
    current_role = db.Column(db.String(100), nullable=True)
    areas_of_interest = db.Column(db.String(100), nullable=True)

    user = db.relationship('User', backref='client_profile', lazy=True, cascade='all, delete')

    def unread_messages(self):
        current_user_last_message = Chat.query.filter_by(sender_id=current_user.id).order_by(
            Chat.datetime.desc()).first()

        client_last_message = Chat.query.filter_by(sender_id=self.user.id).order_by(
            Chat.datetime.desc()).first()

        if current_user_last_message and client_last_message:
            if current_user_last_message.datetime < client_last_message.datetime:
                return True
            else:
                return False
        elif client_last_message:
            return True

        return False


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(255), nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_chats', lazy='joined',
                             cascade='all, delete')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_chats', lazy='joined',
                               cascade='all, delete')


class App(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    app_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    app_logo = db.Column(db.String(100), nullable=True)
    app_url = db.Column(db.String(100), nullable=True)
    price = db.Column(db.String(100), nullable=False)
    request_payment = db.Column(db.Boolean, default=False)
    deadline = db.Column(db.String(100), nullable=False)
    assigned_to = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contract_file = db.Column(db.String(100), nullable=True)

    payment_requests = db.relationship('PaymentRequest', backref='app', lazy=True, cascade='all, delete')


class PaymentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    client_email = db.Column(db.String(100), nullable=False)
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(100), nullable=False)

    def send_payment_request_email(self):
        msg = Message(f'Payment Request for {self.app.app_name}', recipients=[self.client_email])
        msg.html = f'Hello <b>{self.client_name}</b>,<br><br>You have a payment request for the app <b>{self.app.app_name}</b> with amount <b>{self.amount}</b>.'
        mail.send(msg)


class ResetLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), nullable=False, default=str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reset_link', lazy=True)

    def is_expired(self):
        return datetime.utcnow() > self.created_at + timedelta(minutes=3)

    def send_reset_email(self, reset_link):
        msg = Message('Password Reset Request', recipients=[self.user.email])
        msg.html = f'Click the following link to reset your password: <a href="{reset_link}">{reset_link}</a>'
        mail.send(msg)

        return True
