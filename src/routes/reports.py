from flask import Blueprint, request, jsonify, send_file
from src.models.hotel import db, Hotel, SatisfactionResponse
from src.services.analytics_service import AnalyticsService
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import os
import tempfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/hotel/<int:hotel_id>/excel', methods=['GET'])
def export_hotel_excel(hotel_id):
    """Exporte les données d'un hôtel vers Excel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        responses = SatisfactionResponse.query.filter_by(hotel_id=hotel_id).all()
        
        if not responses:
            return jsonify({'error': 'Aucune donnée à exporter'}), 404
        
        # Créer le DataFrame
        data = []
        for response in responses:
            data.append({
                'Date de soumission': response.submission_date.strftime('%Y-%m-%d %H:%M:%S') if response.submission_date else '',
                'Nom du client': response.client_name or '',
                'Email du client': response.client_email or '',
                'Note globale': response.overall_rating or '',
                'Hébergement': response.accommodation_rating or '',
                'Service': response.service_rating or '',
                'Propreté': response.cleanliness_rating or '',
                'Restauration': response.food_rating or '',
                'Emplacement': response.location_rating or '',
                'Rapport qualité-prix': response.value_rating or '',
                'Recommandation': 'Oui' if response.would_recommend else 'Non' if response.would_recommend is not None else '',
                'Commentaires': response.comments or ''
            })
        
        df = pd.DataFrame(data)
        
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            # Créer un writer Excel avec plusieurs onglets
            with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
                # Onglet des données brutes
                df.to_excel(writer, sheet_name='Données', index=False)
                
                # Onglet des statistiques
                analytics_service = AnalyticsService(db)
                stats = analytics_service.get_hotel_statistics(hotel_id)
                
                if stats:
                    stats_data = [
                        ['Métrique', 'Valeur'],
                        ['Nombre total de réponses', stats['total_responses']],
                        ['Note moyenne globale', stats['average_overall_rating']],
                        ['Taux de recommandation (%)', stats['recommendation_rate']],
                        ['Réponses ce mois', stats['monthly_responses']],
                        ['', ''],
                        ['Moyennes par catégorie', ''],
                        ['Hébergement', stats['category_averages'].get('accommodation_rating', 0)],
                        ['Service', stats['category_averages'].get('service_rating', 0)],
                        ['Propreté', stats['category_averages'].get('cleanliness_rating', 0)],
                        ['Restauration', stats['category_averages'].get('food_rating', 0)],
                        ['Emplacement', stats['category_averages'].get('location_rating', 0)],
                        ['Rapport qualité-prix', stats['category_averages'].get('value_rating', 0)]
                    ]
                    
                    stats_df = pd.DataFrame(stats_data[1:], columns=stats_data[0])
                    stats_df.to_excel(writer, sheet_name='Statistiques', index=False)
            
            # Retourner le fichier
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'HotelSat_{hotel.name}_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export Excel pour l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur lors de l\'export'}), 500

@reports_bp.route('/reports/hotel/<int:hotel_id>/charts', methods=['GET'])
def generate_hotel_charts(hotel_id):
    """Génère des graphiques pour un hôtel"""
    try:
        hotel = Hotel.query.get_or_404(hotel_id)
        analytics_service = AnalyticsService(db)
        stats = analytics_service.get_hotel_statistics(hotel_id)
        
        if not stats or stats['total_responses'] == 0:
            return jsonify({'error': 'Aucune donnée pour générer les graphiques'}), 404
        
        # Configuration matplotlib
        plt.style.use('default')
        sns.set_palette("husl")
        
        charts = {}
        
        # Graphique 1: Notes par catégorie
        fig, ax = plt.subplots(figsize=(10, 6))
        categories = list(stats['category_averages'].keys())
        values = list(stats['category_averages'].values())
        
        category_labels = {
            'accommodation_rating': 'Hébergement',
            'service_rating': 'Service',
            'cleanliness_rating': 'Propreté',
            'food_rating': 'Restauration',
            'location_rating': 'Emplacement',
            'value_rating': 'Qualité-prix'
        }
        
        labels = [category_labels.get(cat, cat) for cat in categories]
        
        bars = ax.bar(labels, values, color=sns.color_palette("husl", len(categories)))
        ax.set_title(f'Notes par catégorie - {hotel.name}', fontsize=14, fontweight='bold')
        ax.set_ylabel('Note moyenne (/5)')
        ax.set_ylim(0, 5)
        
        # Ajouter les valeurs sur les barres
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                   f'{value:.1f}', ha='center', va='bottom')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Convertir en base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        charts['categories'] = chart_data
        plt.close()
        
        # Graphique 2: Distribution des notes globales
        responses = SatisfactionResponse.query.filter_by(hotel_id=hotel_id).all()
        overall_ratings = [r.overall_rating for r in responses if r.overall_rating is not None]
        
        if overall_ratings:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Compter les occurrences de chaque note
            rating_counts = {}
            for rating in range(1, 6):
                rating_counts[rating] = sum(1 for r in overall_ratings if int(r) == rating)
            
            ratings = list(rating_counts.keys())
            counts = list(rating_counts.values())
            
            bars = ax.bar(ratings, counts, color=sns.color_palette("viridis", len(ratings)))
            ax.set_title(f'Distribution des notes globales - {hotel.name}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Note (/5)')
            ax.set_ylabel('Nombre de réponses')
            ax.set_xticks(ratings)
            
            # Ajouter les valeurs sur les barres
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           str(int(count)), ha='center', va='bottom')
            
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            charts['distribution'] = chart_data
            plt.close()
        
        # Graphique 3: Évolution temporelle
        temporal_analysis = analytics_service.get_temporal_analysis(hotel_id, 60)
        
        if temporal_analysis and temporal_analysis['data']:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            dates = [datetime.strptime(d['week'], '%Y-%m-%d') for d in temporal_analysis['data']]
            ratings = [d['average_rating'] for d in temporal_analysis['data']]
            
            ax.plot(dates, ratings, marker='o', linewidth=2, markersize=6)
            ax.set_title(f'Évolution des notes dans le temps - {hotel.name}', fontsize=14, fontweight='bold')
            ax.set_xlabel('Semaine')
            ax.set_ylabel('Note moyenne (/5)')
            ax.set_ylim(0, 5)
            ax.grid(True, alpha=0.3)
            
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            charts['temporal'] = chart_data
            plt.close()
        
        return jsonify({
            'charts': charts,
            'hotel_name': hotel.name,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des graphiques pour l'hôtel {hotel_id}: {e}")
        return jsonify({'error': 'Erreur lors de la génération des graphiques'}), 500

@reports_bp.route('/reports/comparison', methods=['POST'])
def generate_comparison_report():
    """Génère un rapport de comparaison entre plusieurs hôtels"""
    try:
        data = request.get_json()
        hotel_ids = data.get('hotel_ids', [])
        
        if not hotel_ids or len(hotel_ids) < 2:
            return jsonify({'error': 'Au moins 2 hôtels requis pour la comparaison'}), 400
        
        analytics_service = AnalyticsService(db)
        comparison_data = analytics_service.get_comparative_analysis(hotel_ids)
        
        if not comparison_data:
            return jsonify({'error': 'Erreur lors de la génération du rapport'}), 500
        
        # Générer un graphique de comparaison
        fig, ax = plt.subplots(figsize=(12, 8))
        
        hotels = list(comparison_data.keys())
        categories = ['accommodation_rating', 'service_rating', 'cleanliness_rating', 
                     'food_rating', 'location_rating', 'value_rating']
        
        category_labels = {
            'accommodation_rating': 'Hébergement',
            'service_rating': 'Service',
            'cleanliness_rating': 'Propreté',
            'food_rating': 'Restauration',
            'location_rating': 'Emplacement',
            'value_rating': 'Qualité-prix'
        }
        
        x = range(len(categories))
        width = 0.8 / len(hotels)
        
        colors = sns.color_palette("husl", len(hotels))
        
        for i, hotel in enumerate(hotels):
            values = [comparison_data[hotel]['category_averages'].get(cat, 0) for cat in categories]
            offset = (i - len(hotels)/2 + 0.5) * width
            ax.bar([pos + offset for pos in x], values, width, label=hotel, color=colors[i])
        
        ax.set_title('Comparaison des notes par catégorie', fontsize=14, fontweight='bold')
        ax.set_ylabel('Note moyenne (/5)')
        ax.set_xlabel('Catégories')
        ax.set_xticks(x)
        ax.set_xticklabels([category_labels.get(cat, cat) for cat in categories], rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 5)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return jsonify({
            'comparison_data': comparison_data,
            'comparison_chart': chart_data
        })
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport de comparaison: {e}")
        return jsonify({'error': 'Erreur lors de la génération du rapport'}), 500

@reports_bp.route('/reports/global/excel', methods=['GET'])
def export_global_excel():
    """Exporte un rapport global de tous les hôtels"""
    try:
        hotels = Hotel.query.all()
        
        if not hotels:
            return jsonify({'error': 'Aucun hôtel trouvé'}), 404
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
                
                # Onglet de synthèse
                analytics_service = AnalyticsService(db)
                summary_data = []
                
                for hotel in hotels:
                    stats = analytics_service.get_hotel_statistics(hotel.id)
                    if stats:
                        summary_data.append({
                            'Hôtel': hotel.name,
                            'Localisation': hotel.location or '',
                            'Nombre de réponses': stats['total_responses'],
                            'Note moyenne': stats['average_overall_rating'],
                            'Taux de recommandation (%)': stats['recommendation_rate'],
                            'Hébergement': stats['category_averages'].get('accommodation_rating', 0),
                            'Service': stats['category_averages'].get('service_rating', 0),
                            'Propreté': stats['category_averages'].get('cleanliness_rating', 0),
                            'Restauration': stats['category_averages'].get('food_rating', 0),
                            'Emplacement': stats['category_averages'].get('location_rating', 0),
                            'Qualité-prix': stats['category_averages'].get('value_rating', 0)
                        })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Synthèse', index=False)
                
                # Onglet pour chaque hôtel avec ses données détaillées
                for hotel in hotels:
                    responses = SatisfactionResponse.query.filter_by(hotel_id=hotel.id).all()
                    if responses:
                        data = []
                        for response in responses:
                            data.append({
                                'Date': response.submission_date.strftime('%Y-%m-%d') if response.submission_date else '',
                                'Client': response.client_name or '',
                                'Email': response.client_email or '',
                                'Note globale': response.overall_rating or '',
                                'Hébergement': response.accommodation_rating or '',
                                'Service': response.service_rating or '',
                                'Propreté': response.cleanliness_rating or '',
                                'Restauration': response.food_rating or '',
                                'Emplacement': response.location_rating or '',
                                'Qualité-prix': response.value_rating or '',
                                'Recommandation': 'Oui' if response.would_recommend else 'Non' if response.would_recommend is not None else '',
                                'Commentaires': response.comments or ''
                            })
                        
                        df = pd.DataFrame(data)
                        # Limiter le nom de l'onglet à 31 caractères (limite Excel)
                        sheet_name = hotel.name[:31] if len(hotel.name) > 31 else hotel.name
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'HotelSat_Rapport_Global_{datetime.now().strftime("%Y%m%d")}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export global Excel: {e}")
        return jsonify({'error': 'Erreur lors de l\'export'}), 500

