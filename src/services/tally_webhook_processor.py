"""
Processeur de webhook Tally pour les formulaires Top of Travel
Adapté à la structure spécifique des formulaires de satisfaction
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TallyWebhookProcessor:
    """Processeur pour les webhooks Tally des formulaires Top of Travel"""
    
    # Mapping des champs Tally vers les champs de l'application
    FIELD_MAPPING = {
        # Identité
        'email': 'client_email',
        'nom': 'client_name',
        'aeroport_depart': 'departure_airport',
        'agence_voyages': 'travel_agency',
        'code_postal': 'postal_code',
        'date_depart': 'departure_date',
        'duree_voyage': 'trip_duration',
        'nombre_voyageurs': 'number_travelers',
        
        # Appréciations globales
        'conformite_prestations_brochure': 'conformity_rating',
        'rapport_qualite_prix': 'value_rating',
        'appreciation_globale_vacances': 'overall_rating',
        'recommanderiez_vous_voyage': 'would_recommend',
        
        # Transports
        'aerien_accueil_confort': 'flight_comfort_rating',
        'aerien_ponctualite': 'flight_punctuality_rating',
        'navette_securite': 'shuttle_safety_rating',
        'navette_conducteur': 'shuttle_driver_rating',
        'navette_confort_proprete': 'shuttle_comfort_rating',
        
        # Hébergement
        'hebergement_accueil': 'accommodation_welcome_rating',
        'cadre_environnement': 'environment_rating',
        'proprete_parties_communes': 'common_areas_cleanliness_rating',
        'cadre_restaurants': 'restaurant_setting_rating',
        'qualite_variete_plats': 'food_quality_rating',
        
        # Chambres
        'chambres_proprete': 'room_cleanliness_rating',
        'chambres_confort': 'room_comfort_rating',
        'chambres_taille': 'room_size_rating',
        'chambres_salle_bain': 'bathroom_rating',
        
        # Piscine
        'piscine_amenagements': 'pool_facilities_rating',
        'piscine_hygiene': 'pool_hygiene_rating',
        'piscine_securite': 'pool_safety_rating',
        
        # Animation
        'equipements_sportifs': 'sports_equipment_rating',
        'animation_soiree': 'evening_entertainment_rating',
        'variete_activites': 'activities_variety_rating',
        'convivialite_equipe_animation': 'animation_team_rating',
        'activites_enfants': 'children_activities_rating',
        'animation_journee': 'day_entertainment_rating',
        
        # Équipes
        'assistant_aeroport_arrivee': 'arrival_assistant_rating',
        'assistant_aeroport_depart': 'departure_assistant_rating',
        'representant_reunion_info': 'info_meeting_rating',
        'representant_presence_convivialite': 'representative_presence_rating',
        'representant_anticipation_besoins': 'needs_anticipation_rating',
        'representant_reactivite_solutions': 'reactivity_solutions_rating',
        
        # Excursions
        'excursions_qualite': 'excursions_quality_rating',
        'excursions_transport': 'excursions_transport_rating',
        'excursions_guides': 'excursions_guides_rating',
        'excursions_restauration': 'excursions_food_rating',
        
        # Profil voyageur
        'vous_voyagez': 'travel_type',
        'ages': 'age_group',
        'tour_operateurs': 'previous_operators',
        'preparation_voyage': 'trip_preparation',
        'votre_avis_compte': 'additional_comments'
    }
    
    # Mapping des valeurs pour les champs spéciaux
    VALUE_MAPPING = {
        'would_recommend': {
            'Oui': True,
            'Non': False
        },
        'trip_duration': {
            '7 jours': 7,
            '14 jours': 14,
            'Autres': None
        },
        'travel_type': {
            'En solo': 'solo',
            'En couple sans enfant': 'couple',
            'En famille': 'family',
            'Entre amis': 'friends'
        },
        'age_group': {
            '18-30': '18-30',
            '31-40': '31-40',
            '41-50': '41-50',
            '51-60': '51-60',
            '60 et plus': '60+'
        }
    }
    
    @classmethod
    def process_webhook_data(cls, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite les données du webhook Tally et les convertit au format de l'application
        
        Args:
            webhook_data: Données brutes du webhook Tally
            
        Returns:
            Dict contenant les données formatées pour l'application
        """
        try:
            logger.info(f"Traitement des données webhook Tally: {len(webhook_data)} champs")
            
            # Extraire les données du formulaire
            form_data = webhook_data.get('data', {})
            if not form_data:
                logger.warning("Aucune donnée de formulaire trouvée dans le webhook")
                return {}
            
            processed_data = {}
            
            # Traiter chaque champ du formulaire
            for tally_field, app_field in cls.FIELD_MAPPING.items():
                if tally_field in form_data:
                    value = form_data[tally_field]
                    
                    # Appliquer les transformations de valeurs si nécessaire
                    if app_field in cls.VALUE_MAPPING and value in cls.VALUE_MAPPING[app_field]:
                        value = cls.VALUE_MAPPING[app_field][value]
                    
                    # Convertir les ratings en float
                    if 'rating' in app_field and isinstance(value, str):
                        try:
                            # Extraire le nombre d'étoiles (format "X étoiles")
                            if 'étoiles' in value or 'étoile' in value:
                                value = float(value.split()[0])
                            else:
                                value = float(value)
                        except (ValueError, IndexError):
                            logger.warning(f"Impossible de convertir la note: {value}")
                            value = None
                    
                    processed_data[app_field] = value
            
            # Ajouter des métadonnées
            processed_data['submission_date'] = datetime.utcnow().isoformat()
            processed_data['source'] = 'tally_webhook'
            
            # Calculer la note globale moyenne si pas fournie
            if 'overall_rating' not in processed_data:
                processed_data['overall_rating'] = cls._calculate_average_rating(processed_data)
            
            logger.info(f"Données traitées avec succès: {len(processed_data)} champs")
            return processed_data
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des données webhook: {e}")
            return {}
    
    @classmethod
    def _calculate_average_rating(cls, data: Dict[str, Any]) -> Optional[float]:
        """
        Calcule la note moyenne basée sur les principales catégories
        
        Args:
            data: Données traitées
            
        Returns:
            Note moyenne ou None si pas assez de données
        """
        try:
            # Principales catégories pour le calcul de la moyenne
            main_ratings = [
                'accommodation_welcome_rating',
                'room_cleanliness_rating',
                'room_comfort_rating',
                'food_quality_rating',
                'value_rating'
            ]
            
            ratings = []
            for rating_field in main_ratings:
                if rating_field in data and data[rating_field] is not None:
                    ratings.append(float(data[rating_field]))
            
            if len(ratings) >= 3:  # Au moins 3 notes pour calculer une moyenne
                return round(sum(ratings) / len(ratings), 1)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la note moyenne: {e}")
            return None
    
    @classmethod
    def validate_webhook_data(cls, webhook_data: Dict[str, Any]) -> bool:
        """
        Valide les données du webhook Tally
        
        Args:
            webhook_data: Données du webhook
            
        Returns:
            True si les données sont valides, False sinon
        """
        try:
            # Vérifications de base
            if not isinstance(webhook_data, dict):
                logger.error("Les données du webhook ne sont pas un dictionnaire")
                return False
            
            form_data = webhook_data.get('data', {})
            if not form_data:
                logger.error("Aucune donnée de formulaire trouvée")
                return False
            
            # Vérifier qu'au moins un champ requis est présent
            required_fields = ['email', 'nom', 'appreciation_globale_vacances']
            has_required = any(field in form_data for field in required_fields)
            
            if not has_required:
                logger.error("Aucun champ requis trouvé dans les données")
                return False
            
            logger.info("Validation des données webhook réussie")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation des données webhook: {e}")
            return False
    
    @classmethod
    def extract_hotel_info(cls, webhook_data: Dict[str, Any]) -> Optional[str]:
        """
        Extrait les informations sur l'hôtel depuis les données du webhook
        
        Args:
            webhook_data: Données du webhook
            
        Returns:
            Nom de l'hôtel ou None si non trouvé
        """
        try:
            # Essayer d'extraire depuis l'URL ou les métadonnées
            form_url = webhook_data.get('form_url', '')
            if 'hotel' in form_url.lower():
                # Logique pour extraire le nom de l'hôtel depuis l'URL
                pass
            
            # Pour l'instant, retourner None car l'hôtel est identifié par l'URL du webhook
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des infos hôtel: {e}")
            return None

