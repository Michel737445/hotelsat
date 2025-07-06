import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from sqlalchemy import func
from src.models.hotel import SatisfactionResponse, Hotel

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db):
        self.db = db
    
    def get_hotel_statistics(self, hotel_id):
        """Calcule les statistiques de satisfaction pour un hôtel"""
        try:
            responses = SatisfactionResponse.query.filter_by(hotel_id=hotel_id).all()
            
            if not responses:
                return {
                    'total_responses': 0,
                    'average_overall_rating': 0,
                    'recommendation_rate': 0,
                    'category_averages': {},
                    'monthly_responses': 0
                }
            
            # Convertir en DataFrame pour faciliter les calculs
            data = [response.to_dict() for response in responses]
            df = pd.DataFrame(data)
            
            # Statistiques de base
            total_responses = len(responses)
            
            # Note moyenne globale
            overall_ratings = [r.overall_rating for r in responses if r.overall_rating is not None]
            average_overall_rating = np.mean(overall_ratings) if overall_ratings else 0
            
            # Taux de recommandation
            recommendations = [r.would_recommend for r in responses if r.would_recommend is not None]
            recommendation_rate = (sum(recommendations) / len(recommendations) * 100) if recommendations else 0
            
            # Moyennes par catégorie
            categories = [
                'accommodation_rating',
                'service_rating',
                'cleanliness_rating',
                'food_rating',
                'location_rating',
                'value_rating'
            ]
            
            category_averages = {}
            for category in categories:
                values = [getattr(r, category) for r in responses if getattr(r, category) is not None]
                category_averages[category] = np.mean(values) if values else 0
            
            # Réponses du mois en cours
            current_month = datetime.now().replace(day=1)
            monthly_responses = SatisfactionResponse.query.filter(
                SatisfactionResponse.hotel_id == hotel_id,
                SatisfactionResponse.submission_date >= current_month
            ).count()
            
            return {
                'total_responses': total_responses,
                'average_overall_rating': round(average_overall_rating, 1),
                'recommendation_rate': round(recommendation_rate, 1),
                'category_averages': {k: round(v, 1) for k, v in category_averages.items()},
                'monthly_responses': monthly_responses
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques pour l'hôtel {hotel_id}: {e}")
            return None
    
    def get_comparative_analysis(self, hotel_ids):
        """Effectue une analyse comparative entre plusieurs hôtels"""
        try:
            comparative_data = {}
            
            for hotel_id in hotel_ids:
                hotel = Hotel.query.get(hotel_id)
                if hotel:
                    stats = self.get_hotel_statistics(hotel_id)
                    comparative_data[hotel.name] = stats
            
            return comparative_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse comparative: {e}")
            return None
    
    def get_temporal_analysis(self, hotel_id, period_days=30):
        """Analyse l'évolution temporelle des données de satisfaction"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            responses = SatisfactionResponse.query.filter(
                SatisfactionResponse.hotel_id == hotel_id,
                SatisfactionResponse.submission_date >= start_date
            ).order_by(SatisfactionResponse.submission_date).all()
            
            if not responses:
                return {'data': [], 'trend': 'stable'}
            
            # Grouper par semaine
            weekly_data = {}
            for response in responses:
                week_start = response.submission_date - timedelta(days=response.submission_date.weekday())
                week_key = week_start.strftime('%Y-%m-%d')
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = []
                
                if response.overall_rating:
                    weekly_data[week_key].append(response.overall_rating)
            
            # Calculer les moyennes hebdomadaires
            temporal_data = []
            for week, ratings in weekly_data.items():
                temporal_data.append({
                    'week': week,
                    'average_rating': round(np.mean(ratings), 1),
                    'response_count': len(ratings)
                })
            
            # Déterminer la tendance
            if len(temporal_data) >= 2:
                first_half = temporal_data[:len(temporal_data)//2]
                second_half = temporal_data[len(temporal_data)//2:]
                
                first_avg = np.mean([d['average_rating'] for d in first_half])
                second_avg = np.mean([d['average_rating'] for d in second_half])
                
                if second_avg > first_avg + 0.2:
                    trend = 'improving'
                elif second_avg < first_avg - 0.2:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'
            
            return {
                'data': temporal_data,
                'trend': trend
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse temporelle: {e}")
            return None
    
    def get_detailed_analysis(self, hotel_id):
        """Effectue une analyse détaillée des données de satisfaction"""
        try:
            responses = SatisfactionResponse.query.filter_by(hotel_id=hotel_id).all()
            
            if not responses:
                return None
            
            # Analyse des commentaires
            comments = [r.comments for r in responses if r.comments]
            
            # Mots-clés fréquents (analyse simple)
            all_words = []
            for comment in comments:
                words = comment.lower().split()
                # Filtrer les mots courts et courants
                filtered_words = [w for w in words if len(w) > 3 and w not in ['très', 'bien', 'avec', 'pour', 'dans', 'cette', 'tout', 'plus']]
                all_words.extend(filtered_words)
            
            word_freq = {}
            for word in all_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Top 10 des mots les plus fréquents
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Distribution des notes
            rating_distribution = {}
            for i in range(1, 6):
                rating_distribution[str(i)] = len([r for r in responses if r.overall_rating and int(r.overall_rating) == i])
            
            # Corrélations entre catégories
            categories = ['accommodation_rating', 'service_rating', 'cleanliness_rating', 'food_rating', 'location_rating', 'value_rating']
            correlations = {}
            
            for i, cat1 in enumerate(categories):
                for cat2 in categories[i+1:]:
                    values1 = [getattr(r, cat1) for r in responses if getattr(r, cat1) is not None]
                    values2 = [getattr(r, cat2) for r in responses if getattr(r, cat2) is not None]
                    
                    if len(values1) > 1 and len(values2) > 1:
                        correlation = np.corrcoef(values1, values2)[0, 1]
                        correlations[f"{cat1}_vs_{cat2}"] = round(correlation, 2)
            
            return {
                'top_keywords': top_keywords,
                'rating_distribution': rating_distribution,
                'correlations': correlations,
                'total_comments': len(comments)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse détaillée: {e}")
            return None
    
    def generate_insights(self, hotel_id):
        """Génère des insights automatiques basés sur les données"""
        try:
            stats = self.get_hotel_statistics(hotel_id)
            detailed = self.get_detailed_analysis(hotel_id)
            temporal = self.get_temporal_analysis(hotel_id)
            
            if not stats or not detailed:
                return []
            
            insights = []
            
            # Insight sur la note globale
            if stats['average_overall_rating'] >= 4.5:
                insights.append({
                    'type': 'positive',
                    'title': 'Excellente satisfaction globale',
                    'description': f"Votre hôtel obtient une note moyenne de {stats['average_overall_rating']}/5, ce qui est excellent."
                })
            elif stats['average_overall_rating'] < 3.5:
                insights.append({
                    'type': 'warning',
                    'title': 'Satisfaction à améliorer',
                    'description': f"La note moyenne de {stats['average_overall_rating']}/5 indique des axes d'amélioration."
                })
            
            # Insight sur le taux de recommandation
            if stats['recommendation_rate'] >= 80:
                insights.append({
                    'type': 'positive',
                    'title': 'Fort taux de recommandation',
                    'description': f"{stats['recommendation_rate']}% de vos clients recommandent votre hôtel."
                })
            elif stats['recommendation_rate'] < 60:
                insights.append({
                    'type': 'warning',
                    'title': 'Taux de recommandation faible',
                    'description': f"Seulement {stats['recommendation_rate']}% de recommandation. Identifiez les points d'amélioration."
                })
            
            # Insight sur la catégorie la mieux notée
            best_category = max(stats['category_averages'], key=stats['category_averages'].get)
            worst_category = min(stats['category_averages'], key=stats['category_averages'].get)
            
            category_names = {
                'accommodation_rating': 'Hébergement',
                'service_rating': 'Service',
                'cleanliness_rating': 'Propreté',
                'food_rating': 'Restauration',
                'location_rating': 'Emplacement',
                'value_rating': 'Rapport qualité-prix'
            }
            
            insights.append({
                'type': 'info',
                'title': 'Point fort identifié',
                'description': f"Votre meilleur atout est '{category_names.get(best_category, best_category)}' avec {stats['category_averages'][best_category]}/5."
            })
            
            if stats['category_averages'][worst_category] < 4.0:
                insights.append({
                    'type': 'improvement',
                    'title': 'Axe d\'amélioration prioritaire',
                    'description': f"'{category_names.get(worst_category, worst_category)}' obtient {stats['category_averages'][worst_category]}/5 et mérite attention."
                })
            
            # Insight sur la tendance
            if temporal and temporal['trend'] == 'improving':
                insights.append({
                    'type': 'positive',
                    'title': 'Tendance positive',
                    'description': 'Vos notes de satisfaction sont en amélioration ces dernières semaines.'
                })
            elif temporal and temporal['trend'] == 'declining':
                insights.append({
                    'type': 'warning',
                    'title': 'Tendance à surveiller',
                    'description': 'Vos notes de satisfaction montrent une baisse récente.'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'insights: {e}")
            return []

