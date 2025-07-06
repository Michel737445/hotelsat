import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TallyService:
    def __init__(self):
        self.base_url = "https://api.tally.so"
        self.api_key = None  # À configurer via les variables d'environnement
    
    def process_webhook_data(self, webhook_data):
        """Traite les données reçues du webhook Tally"""
        try:
            # Extraire les informations du webhook Tally
            # La structure peut varier selon la configuration du formulaire
            
            # Données de base
            submission_id = webhook_data.get('submissionId')
            form_id = webhook_data.get('formId')
            submitted_at = webhook_data.get('submittedAt')
            
            # Réponses du formulaire
            responses = webhook_data.get('data', {})
            
            # Mapper les réponses aux champs de notre modèle
            processed_data = {
                'tally_submission_id': submission_id,
                'submission_date': self._parse_date(submitted_at),
                'client_name': self._extract_field(responses, ['nom', 'name', 'client_name']),
                'client_email': self._extract_field(responses, ['email', 'e-mail', 'client_email']),
                'overall_rating': self._extract_rating(responses, ['note_globale', 'overall_rating', 'satisfaction_globale']),
                'accommodation_rating': self._extract_rating(responses, ['hebergement', 'accommodation', 'logement']),
                'service_rating': self._extract_rating(responses, ['service', 'service_client']),
                'cleanliness_rating': self._extract_rating(responses, ['proprete', 'cleanliness', 'nettoyage']),
                'food_rating': self._extract_rating(responses, ['restauration', 'food', 'nourriture']),
                'location_rating': self._extract_rating(responses, ['emplacement', 'location', 'localisation']),
                'value_rating': self._extract_rating(responses, ['rapport_qualite_prix', 'value', 'prix']),
                'would_recommend': self._extract_recommendation(responses),
                'comments': self._extract_field(responses, ['commentaires', 'comments', 'remarques'])
            }
            
            logger.info(f"Données Tally traitées pour la soumission {submission_id}")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données Tally: {e}")
            return None
    
    def _extract_field(self, responses, possible_keys):
        """Extrait un champ des réponses en essayant plusieurs clés possibles"""
        for key in possible_keys:
            if key in responses:
                return responses[key]
            # Essayer aussi avec des variations de casse
            for response_key in responses.keys():
                if response_key.lower() == key.lower():
                    return responses[response_key]
        return None
    
    def _extract_rating(self, responses, possible_keys):
        """Extrait une note et la convertit en float"""
        value = self._extract_field(responses, possible_keys)
        if value is not None:
            try:
                # Gérer différents formats de notes
                if isinstance(value, str):
                    # Extraire le nombre de chaînes comme "4/5" ou "4 étoiles"
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', value)
                    if match:
                        return float(match.group(1))
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"Impossible de convertir la note: {value}")
        return None
    
    def _extract_recommendation(self, responses):
        """Extrait la recommandation et la convertit en boolean"""
        value = self._extract_field(responses, ['recommandation', 'recommend', 'recommande'])
        if value is not None:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                value_lower = value.lower()
                return value_lower in ['oui', 'yes', 'true', '1', 'recommande']
        return None
    
    def _parse_date(self, date_string):
        """Parse une date depuis différents formats"""
        if not date_string:
            return datetime.utcnow()
        
        try:
            # Essayer le format ISO
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            try:
                # Essayer d'autres formats courants
                return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
            except:
                logger.warning(f"Format de date non reconnu: {date_string}")
                return datetime.utcnow()
    
    def validate_webhook_signature(self, payload, signature, secret):
        """Valide la signature du webhook Tally pour s'assurer de l'authenticité"""
        import hmac
        import hashlib
        
        if not secret:
            logger.warning("Aucun secret configuré pour la validation des webhooks")
            return True  # Accepter si pas de secret configuré
        
        try:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Erreur lors de la validation de la signature: {e}")
            return False
    
    def create_sample_webhook_data(self, hotel_name="Test Hotel"):
        """Crée des données d'exemple pour tester l'intégration"""
        return {
            'submissionId': f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'formId': 'test_form',
            'submittedAt': datetime.now().isoformat(),
            'data': {
                'nom': 'Jean Dupont',
                'email': 'jean.dupont@example.com',
                'note_globale': '4',
                'hebergement': '5',
                'service': '4',
                'proprete': '5',
                'restauration': '3',
                'emplacement': '4',
                'rapport_qualite_prix': '4',
                'recommandation': 'Oui',
                'commentaires': 'Très bon séjour, personnel accueillant. Seul bémol: la restauration pourrait être améliorée.'
            }
        }

