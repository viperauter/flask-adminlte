from models import db


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.String)
    content = db.Column(db.String)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)
    owner = db.relationship('User', backref='documents')
