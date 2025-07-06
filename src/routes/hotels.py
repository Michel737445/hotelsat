from flask import Blueprint, request, jsonify
from src.models.hotel import db, Hotel, SatisfactionResponse
from src.services.google_sheets_service import GoogleSheetsService
from src.services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

hotels_bp = Blueprint('hotels', __name__)
google_sheets_service = GoogleSheetsService()

@hotels_bp.route('/hotels', methods=['GET'])
def get_hotels():
    """Récupère la liste de tous les hôtels"""
    try:
        hotels = Hotel.query.all()
        return jsonify([hotel.to_dict() for hotel in hotels])
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des hôtels: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@hotels_bp.route('/hotels', methods=['POST'])
def create_hotel():
    """Crée un nouvel hôtel et clone automatiquement une Google Sheet"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Le nom de l\'hôtel est requis'}), 400
        
        # Créer l'hôtel
        hotel = Hotel(
            name=data['name'],
            location=data.get('location'),
            tally_form_url=data.get('tally_form_url')
        )
        
        db.session.add(hotel)
        db.session.flush()  # Pour obtenir l'ID
        
        # Cloner la Google Sheet
        sheet_id, sheet_url = google_sheets_service.clone_template_sheet(hotel.name)
        
        if sheet_id:
            hotel.google_sheet_id = sheet_id
            hotel.google_sheet_url = sheet_url
        
        db.session.commit()
        
        logger.info(f"Hôtel créé: {hotel.name} (ID: {hotel.id})")
        return jsonify(hotel.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de l'hôtel: {e}")
        return jsonify({'error': 'Erreur lors de la création de l\'hôtel'}), 500

@hotels_bp.route('/hotels/<int:hotel_id>', methods=['GET'])
def get_hotel(hotel_id):
    """Récupère les détails d'un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        return jsonify(hotel.to_dict())
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Hôtel non trouvé'}), 404

@hotels_bp.route('/hotels/<int:hotel_id>', methods=['PUT'])
def update_hotel(hotel_id):
    """Met à jour un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        data = request.get_json()
        
        if data.get('name'):
            hotel.name = data['name']
        if data.get('location'):
            hotel.location = data['location']
        if data.get('tally_form_url'):
            hotel.tally_form_url = data['tally_form_url']
        
        db.session.commit()
        
        logger.info(f"Hôtel mis à jour: {hotel.name} (ID: {hotel.id})")
        return jsonify(hotel.to_dict())
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la mise à jour de l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur lors de la mise à jour'}), 500

@hotels_bp.route('/hotels/<int:hotel_id>', methods=['DELETE'])
def delete_hotel(hotel_id):
    """Supprime un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        db.session.delete(hotel)
        db.session.commit()
        
        logger.info(f"Hôtel supprimé: {hotel.name} (ID: {hotel.id})")
        return jsonify({'message': 'Hôtel supprimé avec succès'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la suppression de l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur lors de la suppression'}), 500

@hotels_bp.route('/hotels/<int:hotel_id>/statistics', methods=['GET'])
def get_hotel_statistics(hotel_id):
    """Récupère les statistiques de satisfaction d'un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        analytics_service = AnalyticsService(db)
        stats = analytics_service.get_hotel_statistics(hotel_id)
        
        if stats is None:
            return jsonify({'error': 'Erreur lors du calcul des statistiques'}), 500
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques pour l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@hotels_bp.route('/hotels/<int:hotel_id>/responses', methods=['GET'])
def get_hotel_responses(hotel_id):
    """Récupère les réponses de satisfaction d'un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        
        # Paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        responses = SatisfactionResponse.query.filter_by(hotel_id=hotel_id)\
            .order_by(SatisfactionResponse.submission_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'responses': [response.to_dict() for response in responses.items],
            'total': responses.total,
            'pages': responses.pages,
            'current_page': page
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des réponses pour l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@hotels_bp.route('/hotels/<int:hotel_id>/insights', methods=['GET'])
def get_hotel_insights(hotel_id):
    """Récupère les insights automatiques pour un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        analytics_service = AnalyticsService(db)
        insights = analytics_service.generate_insights(hotel_id)
        
        return jsonify({'insights': insights})
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération d'insights pour l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@hotels_bp.route('/hotels/compare', methods=['POST'])
def compare_hotels():
    """Compare plusieurs hôtels"""
    try:
        data = request.get_json()
        hotel_ids = data.get('hotel_ids', [])
        
        if not hotel_ids or len(hotel_ids) < 2:
            return jsonify({'error': 'Au moins 2 hôtels sont requis pour la comparaison'}), 400
        
        analytics_service = AnalyticsService(db)
        comparison = analytics_service.get_comparative_analysis(hotel_ids)
        
        if comparison is None:
            return jsonify({'error': 'Erreur lors de la comparaison'}), 500
        
        return jsonify(comparison)
        
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison des hôtels: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@hotels_bp.route('/hotels/<int:hotel_id>/temporal-analysis', methods=['GET'])
def get_temporal_analysis(hotel_id):
    """Récupère l'analyse temporelle pour un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        period_days = request.args.get('period_days', 30, type=int)
        
        analytics_service = AnalyticsService(db)
        analysis = analytics_service.get_temporal_analysis(hotel_id, period_days)
        
        if analysis is None:
            return jsonify({'error': 'Erreur lors de l\'analyse temporelle'}), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse temporelle pour l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

