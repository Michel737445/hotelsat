from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Hotel(db.Model):
    __tablename__ = 'hotels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    tally_form_url = db.Column(db.String(500), nullable=True)
    google_sheet_id = db.Column(db.String(200), nullable=True)
    google_sheet_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation avec les réponses
    responses = db.relationship('SatisfactionResponse', backref='hotel', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'tally_form_url': self.tally_form_url,
            'google_sheet_id': self.google_sheet_id,
            'google_sheet_url': self.google_sheet_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class SatisfactionResponse(db.Model):
    __tablename__ = 'satisfaction_responses'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    
    # Informations du client
    client_name = db.Column(db.String(200), nullable=True)
    client_email = db.Column(db.String(200), nullable=True)
    
    # Notes de satisfaction (sur 5)
    overall_rating = db.Column(db.Float, nullable=True)
    accommodation_rating = db.Column(db.Float, nullable=True)
    service_rating = db.Column(db.Float, nullable=True)
    cleanliness_rating = db.Column(db.Float, nullable=True)
    food_rating = db.Column(db.Float, nullable=True)
    location_rating = db.Column(db.Float, nullable=True)
    value_rating = db.Column(db.Float, nullable=True)
    
    # Recommandation
    would_recommend = db.Column(db.Boolean, nullable=True)
    
    # Commentaires
    comments = db.Column(db.Text, nullable=True)
    
    # Métadonnées
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    tally_submission_id = db.Column(db.String(200), nullable=True, unique=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'overall_rating': self.overall_rating,
            'accommodation_rating': self.accommodation_rating,
            'service_rating': self.service_rating,
            'cleanliness_rating': self.cleanliness_rating,
            'food_rating': self.food_rating,
            'location_rating': self.location_rating,
            'value_rating': self.value_rating,
            'would_recommend': self.would_recommend,
            'comments': self.comments,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'tally_submission_id': self.tally_submission_id
        }
    
    def get_average_rating(self):
        """Calcule la note moyenne en excluant les valeurs nulles"""
        ratings = [
            self.accommodation_rating,
            self.service_rating,
            self.cleanliness_rating,
            self.food_rating,
            self.location_rating,
            self.value_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        return sum(valid_ratings) / len(valid_ratings) if valid_ratings else None

