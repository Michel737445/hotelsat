from flask import Blueprint, request, jsonify
from src.models.hotel import db, Hotel, SatisfactionResponse
from src.services.tally_service import TallyService
from src.services.google_sheets_service import GoogleSheetsService
import logging
import os

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__)
tally_service = TallyService()
google_sheets_service = GoogleSheetsService()

@webhooks_bp.route('/webhooks/tally', methods=['POST'])
def handle_tally_webhook():
    """Traite les webhooks reçus de Tally"""
    try:
        # Récupérer les données du webhook
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({'error': 'Aucune donnée reçue'}), 400
        
        # Valider la signature si configurée
        signature = request.headers.get('X-Tally-Signature')
        webhook_secret = os.getenv('TALLY_WEBHOOK_SECRET')
        
        if webhook_secret and signature:
            payload = request.get_data(as_text=True)
            if not tally_service.validate_webhook_signature(payload, signature, webhook_secret):
                logger.warning("Signature de webhook invalide")
                return jsonify({'error': 'Signature invalide'}), 401
        
        # Traiter les données
        processed_data = tally_service.process_webhook_data(webhook_data)
        
        if not processed_data:
            return jsonify({'error': 'Erreur lors du traitement des données'}), 400
        
        # Identifier l'hôtel (plusieurs stratégies possibles)
        hotel = None
        
        # Stratégie 1: Utiliser un paramètre dans l'URL du webhook
        hotel_id = request.args.get('hotel_id')
        if hotel_id:
            hotel = Hotel.query.get(hotel_id)
        
        # Stratégie 2: Chercher par URL de formulaire Tally
        if not hotel:
            form_id = webhook_data.get('formId')
            if form_id:
                hotel = Hotel.query.filter(Hotel.tally_form_url.contains(form_id)).first()
        
        # Stratégie 3: Utiliser le premier hôtel (pour les tests)
        if not hotel:
            hotel = Hotel.query.first()
        
        if not hotel:
            logger.error("Aucun hôtel trouvé pour ce webhook")
            return jsonify({'error': 'Hôtel non identifié'}), 400
        
        # Vérifier si cette soumission existe déjà
        existing_response = SatisfactionResponse.query.filter_by(
            tally_submission_id=processed_data['tally_submission_id']
        ).first()
        
        if existing_response:
            logger.info(f"Soumission déjà traitée: {processed_data['tally_submission_id']}")
            return jsonify({'message': 'Soumission déjà traitée'}), 200
        
        # Créer la nouvelle réponse
        response = SatisfactionResponse(
            hotel_id=hotel.id,
            **processed_data
        )
        
        db.session.add(response)
        db.session.commit()
        
        # Ajouter à Google Sheets si configuré
        if hotel.google_sheet_id:
            google_sheets_service.add_response_to_sheet(
                hotel.google_sheet_id,
                processed_data
            )
        
        logger.info(f"Nouvelle réponse ajoutée pour l'hôtel {hotel.name}: {response.id}")
        
        return jsonify({
            'message': 'Réponse traitée avec succès',
            'response_id': response.id,
            'hotel_name': hotel.name
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors du traitement du webhook Tally: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@webhooks_bp.route('/webhooks/test', methods=['POST'])
def test_webhook():
    """Endpoint de test pour simuler un webhook Tally"""
    try:
        # Récupérer l'ID de l'hôtel depuis les paramètres
        hotel_id = request.args.get('hotel_id')
        if not hotel_id:
            return jsonify({'error': 'hotel_id requis'}), 400
        
        hotel = Hotel.query.get(hotel_id)
        if not hotel:
            return jsonify({'error': 'Hôtel non trouvé'}), 404
        
        # Créer des données de test
        test_data = tally_service.create_sample_webhook_data(hotel.name)
        
        # Traiter comme un vrai webhook
        processed_data = tally_service.process_webhook_data(test_data)
        
        # Créer la réponse de test
        response = SatisfactionResponse(
            hotel_id=hotel.id,
            **processed_data
        )
        
        db.session.add(response)
        db.session.commit()
        
        # Ajouter à Google Sheets si configuré
        if hotel.google_sheet_id:
            google_sheets_service.add_response_to_sheet(
                hotel.google_sheet_id,
                processed_data
            )
        
        logger.info(f"Réponse de test créée pour l'hôtel {hotel.name}: {response.id}")
        
        return jsonify({
            'message': 'Réponse de test créée avec succès',
            'response_id': response.id,
            'test_data': test_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur lors de la création de la réponse de test: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

@webhooks_bp.route('/webhooks/status', methods=['GET'])
def webhook_status():
    """Vérifie le statut des webhooks"""
    try:
        # Compter les réponses par hôtel
        hotels_with_responses = db.session.query(
            Hotel.name,
            db.func.count(SatisfactionResponse.id).label('response_count')
        ).outerjoin(SatisfactionResponse).group_by(Hotel.id, Hotel.name).all()
        
        status = {
            'total_hotels': Hotel.query.count(),
            'total_responses': SatisfactionResponse.query.count(),
            'hotels_data': [
                {
                    'hotel_name': name,
                    'response_count': count
                }
                for name, count in hotels_with_responses
            ]
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        return jsonify({'error': 'Erreur serveur'}), 500

