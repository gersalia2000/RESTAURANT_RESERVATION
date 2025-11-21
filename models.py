# models.py
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    people = db.Column(db.Integer, nullable=False)
    items = db.Column(db.Text, nullable=True)  # store JSON string
    payment_status = db.Column(db.String(20), nullable=True)

    def items_list(self):
        return json.loads(self.items) if self.items else []
