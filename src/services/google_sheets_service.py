import os
import json
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.service = None
        self.template_sheet_id = "1BvAHpQxFd8fYGzQxKlMnOpQrStUvWxYz"  # ID du modèle de base
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialise le service Google Sheets avec les credentials"""
        try:
            # Essayer d'utiliser les credentials de service account depuis les variables d'environnement
            credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                credentials_info = json.loads(credentials_json)
                credentials = ServiceAccountCredentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                logger.info("Service Google Sheets initialisé avec les credentials de service account")
                return
            
            # Fallback: utiliser un fichier de credentials
            credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
            if os.path.exists(credentials_file):
                credentials = ServiceAccountCredentials.from_service_account_file(
                    credentials_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=credentials)
                logger.info("Service Google Sheets initialisé avec le fichier de credentials")
                return
            
            logger.warning("Aucun credentials Google trouvé. Le service Google Sheets ne sera pas disponible.")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service Google Sheets: {e}")
    
    def clone_template_sheet(self, hotel_name):
        """Clone le modèle de feuille de calcul pour un nouvel hôtel"""
        if not self.service:
            logger.error("Service Google Sheets non initialisé")
            return None, None
        
        try:
            # Créer une copie du modèle
            copy_request = {
                'name': f'HotelSat - {hotel_name}'
            }
            
            drive_service = build('drive', 'v3', credentials=self.service._http.credentials)
            copied_file = drive_service.files().copy(
                fileId=self.template_sheet_id,
                body=copy_request
            ).execute()
            
            new_sheet_id = copied_file['id']
            new_sheet_url = f"https://docs.google.com/spreadsheets/d/{new_sheet_id}"
            
            # Personnaliser la feuille avec le nom de l'hôtel
            self._customize_sheet_for_hotel(new_sheet_id, hotel_name)
            
            logger.info(f"Feuille clonée avec succès pour {hotel_name}: {new_sheet_id}")
            return new_sheet_id, new_sheet_url
            
        except HttpError as e:
            logger.error(f"Erreur lors du clonage de la feuille: {e}")
            return None, None
    
    def _customize_sheet_for_hotel(self, sheet_id, hotel_name):
        """Personnalise la feuille clonée avec les informations de l'hôtel"""
        try:
            # Mettre à jour le titre de la feuille
            requests = [
                {
                    'updateCells': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 1
                        },
                        'rows': [
                            {
                                'values': [
                                    {
                                        'userEnteredValue': {
                                            'stringValue': f'Données de satisfaction - {hotel_name}'
                                        }
                                    }
                                ]
                            }
                        ],
                        'fields': 'userEnteredValue'
                    }
                }
            ]
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id,
                body={'requests': requests}
            ).execute()
            
        except HttpError as e:
            logger.error(f"Erreur lors de la personnalisation de la feuille: {e}")
    
    def add_response_to_sheet(self, sheet_id, response_data):
        """Ajoute une nouvelle réponse à la feuille Google Sheets"""
        if not self.service:
            logger.error("Service Google Sheets non initialisé")
            return False
        
        try:
            # Préparer les données à insérer
            values = [
                response_data.get('submission_date', ''),
                response_data.get('client_name', ''),
                response_data.get('client_email', ''),
                response_data.get('overall_rating', ''),
                response_data.get('accommodation_rating', ''),
                response_data.get('service_rating', ''),
                response_data.get('cleanliness_rating', ''),
                response_data.get('food_rating', ''),
                response_data.get('location_rating', ''),
                response_data.get('value_rating', ''),
                'Oui' if response_data.get('would_recommend') else 'Non',
                response_data.get('comments', '')
            ]
            
            # Ajouter la ligne à la feuille
            body = {
                'values': [values]
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range='Données!A:L',  # Supposant que les données sont dans l'onglet "Données"
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Réponse ajoutée à la feuille {sheet_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Erreur lors de l'ajout de la réponse à la feuille: {e}")
            return False
    
    def get_sheet_data(self, sheet_id, range_name='Données!A:L'):
        """Récupère les données d'une feuille Google Sheets"""
        if not self.service:
            logger.error("Service Google Sheets non initialisé")
            return None
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
            
        except HttpError as e:
            logger.error(f"Erreur lors de la récupération des données: {e}")
            return None
    
    def create_sample_template(self):
        """Crée un modèle de feuille de calcul de base (pour les tests)"""
        if not self.service:
            logger.error("Service Google Sheets non initialisé")
            return None
        
        try:
            # Créer une nouvelle feuille de calcul
            spreadsheet = {
                'properties': {
                    'title': 'HotelSat - Modèle de Base'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'Données'
                        }
                    }
                ]
            }
            
            result = self.service.spreadsheets().create(body=spreadsheet).execute()
            sheet_id = result['spreadsheetId']
            
            # Ajouter les en-têtes
            headers = [
                'Date de soumission',
                'Nom du client',
                'Email du client',
                'Note globale',
                'Hébergement',
                'Service',
                'Propreté',
                'Restauration',
                'Emplacement',
                'Rapport qualité-prix',
                'Recommandation',
                'Commentaires'
            ]
            
            body = {
                'values': [headers]
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range='Données!A1:L1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Modèle de base créé: {sheet_id}")
            return sheet_id
            
        except HttpError as e:
            logger.error(f"Erreur lors de la création du modèle: {e}")
            return None

