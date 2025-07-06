#!/usr/bin/env python3
"""
Script d'importation simplifié pour les hôtels Top of Travel
"""

import sqlite3
import os

# Données des 16 hôtels
HOTELS_DATA = [
    ("Hôtel Baia Malva", "Italie", "https://docs.google.com/spreadsheets/d/1JjFeeAu1D5nFccACgE4Z8BDrBr5OS8by7LtYejsTiLY", "1JjFeeAu1D5nFccACgE4Z8BDrBr5OS8by7LtYejsTiLY", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Albatros", "Croatie", "https://docs.google.com/spreadsheets/d/1iOXnFYJrr5v6XD7Upu9wsoJlPnBeMQJgcRq0HQVmcto", "1iOXnFYJrr5v6XD7Upu9wsoJlPnBeMQJgcRq0HQVmcto", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Morenia", "Croatie", "https://docs.google.com/spreadsheets/d/1YxoVkCX1ArQRO03VR3xhWnXaF8wfWbmfnWVtybUmuNA", "1YxoVkCX1ArQRO03VR3xhWnXaF8wfWbmfnWVtybUmuNA", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Gabbiano", "Italie", "https://docs.google.com/spreadsheets/d/1E4vOTv3m7uUuCZ889rvwTXduFThcrRGGsbaJu4aJYks", "1E4vOTv3m7uUuCZ889rvwTXduFThcrRGGsbaJu4aJYks", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Alvor Baia", "Portugal", "https://docs.google.com/spreadsheets/d/11HlpPYdVpsT0NeG8nqwHjcgfsEfTlT5MuOTKOviKXgM", "11HlpPYdVpsT0NeG8nqwHjcgfsEfTlT5MuOTKOviKXgM", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Riviera", "Malte", "https://docs.google.com/spreadsheets/d/1N7Sxz0woMSq_ZPsKxhD2ZKQkBD3MS4aogmePxqHk38E", "1N7Sxz0woMSq_ZPsKxhD2ZKQkBD3MS4aogmePxqHk38E", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Atlantica Oasis", "Chypre", "https://docs.google.com/spreadsheets/d/1GQ6UJXL7eiRU9pDbyzHWC-lQpASUgiJtm52nNqI8KNE", "1GQ6UJXL7eiRU9pDbyzHWC-lQpASUgiJtm52nNqI8KNE", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Aquasun Village", "Crête", "https://docs.google.com/spreadsheets/d/1Df7h7P7TRwomlx2RKHPxPNWzsO5INjqGnUfF1BpWA8w", "1Df7h7P7TRwomlx2RKHPxPNWzsO5INjqGnUfF1BpWA8w", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Pestana Royal Océan", "Madère", "https://docs.google.com/spreadsheets/d/1e47IUWqQv-8Oh5-JJADgu9rfNW_6Iuw_OXzAIdLnBic", "1e47IUWqQv-8Oh5-JJADgu9rfNW_6Iuw_OXzAIdLnBic", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Sineva Park", "Bulgarie", "https://docs.google.com/spreadsheets/d/1-AgcmIZD1_1fGHnhyuzIrsAIXcMMMuQ1VefX4JUfdJk", "1-AgcmIZD1_1fGHnhyuzIrsAIXcMMMuQ1VefX4JUfdJk", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Dom Pedro Madeira", "Madère", "https://docs.google.com/spreadsheets/d/127fqvrErex8BDwkaE2VUugD4WHMn47SPENhrIQCYo-U", "127fqvrErex8BDwkaE2VUugD4WHMn47SPENhrIQCYo-U", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Top club cocoon - VM Resort", "Albanie", "https://docs.google.com/spreadsheets/d/1jO4REgqWiXeh3U9e2uueRoLsviB0o64Li5d39Fp38os", "1jO4REgqWiXeh3U9e2uueRoLsviB0o64Li5d39Fp38os", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Monchique", "Portugal", "https://docs.google.com/spreadsheets/d/1LyUJwlEfSEsNkeBOdUOhmXPkY70dkcKkcCF19--y2Dk", "1LyUJwlEfSEsNkeBOdUOhmXPkY70dkcKkcCF19--y2Dk", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Delphin", "Monténégro", "https://docs.google.com/spreadsheets/d/1ToPI9UtLbTwZrY8pX_4vT71dOPn35ZvOGKlKCNWWctU", "1ToPI9UtLbTwZrY8pX_4vT71dOPn35ZvOGKlKCNWWctU", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Alvor Baia Resort", "Portugal", "https://docs.google.com/spreadsheets/d/1mm2VGYefOx37T7_h6VZGN6Gt4mtF9njVOS344FaeyR0", "1mm2VGYefOx37T7_h6VZGN6Gt4mtF9njVOS344FaeyR0", "https://tally.so/r/nPgYLQ"),
    ("Hôtel Ariel Cala d'Or", "Majorque", "https://docs.google.com/spreadsheets/d/12bWFjpJ449YIUMHtV7-W7oggIL78hxjUGiFjGSO8NoA", "12bWFjpJ449YIUMHtV7-W7oggIL78hxjUGiFjGSO8NoA", "https://tally.so/r/nPgYLQ")
]

def create_database():
    """Crée la base de données et les tables"""
    db_path = "hotelsat/src/database/app.db"
    
    # Créer le dossier database s'il n'existe pas
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Créer la table hotels
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hotel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200) NOT NULL,
            location VARCHAR(100),
            google_sheet_url TEXT,
            google_sheet_id VARCHAR(100),
            tally_form_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Créer la table satisfaction_response
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS satisfaction_response (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER NOT NULL,
            client_name VARCHAR(200),
            client_email VARCHAR(200),
            overall_rating FLOAT,
            accommodation_rating FLOAT,
            service_rating FLOAT,
            cleanliness_rating FLOAT,
            food_rating FLOAT,
            location_rating FLOAT,
            value_rating FLOAT,
            would_recommend BOOLEAN,
            comments TEXT,
            submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hotel_id) REFERENCES hotel (id)
        )
    ''')
    
    conn.commit()
    return conn

def import_hotels():
    """Importe tous les hôtels"""
    print("🚀 Importation des hôtels Top of Travel")
    print("=" * 50)
    
    conn = create_database()
    cursor = conn.cursor()
    
    imported_count = 0
    updated_count = 0
    
    for hotel_data in HOTELS_DATA:
        name, location, sheet_url, sheet_id, tally_url = hotel_data
        
        # Vérifier si l'hôtel existe déjà
        cursor.execute("SELECT id FROM hotel WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # Mettre à jour
            cursor.execute('''
                UPDATE hotel 
                SET location = ?, google_sheet_url = ?, google_sheet_id = ?, tally_form_url = ?
                WHERE name = ?
            ''', (location, sheet_url, sheet_id, tally_url, name))
            updated_count += 1
            print(f"🔄 Mis à jour: {name} - {location}")
        else:
            # Insérer
            cursor.execute('''
                INSERT INTO hotel (name, location, google_sheet_url, google_sheet_id, tally_form_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, location, sheet_url, sheet_id, tally_url))
            imported_count += 1
            print(f"✅ Importé: {name} - {location}")
    
    conn.commit()
    
    print(f"\n🎉 Importation terminée!")
    print(f"📈 {imported_count} nouveaux hôtels importés")
    print(f"🔄 {updated_count} hôtels mis à jour")
    
    # Afficher la liste
    cursor.execute("SELECT id, name, location FROM hotel ORDER BY name")
    hotels = cursor.fetchall()
    
    print(f"\n📋 Liste des {len(hotels)} hôtels:")
    for hotel_id, name, location in hotels:
        print(f"{hotel_id:2d}. {name} ({location})")
    
    # Générer les URLs de webhook
    print(f"\n🔗 URLs de webhook à configurer:")
    print("=" * 60)
    for hotel_id, name, location in hotels:
        webhook_url = f"https://votre-domaine.com/api/webhooks/tally?hotel_id={hotel_id}"
        print(f"🏨 {name}")
        print(f"   🔗 {webhook_url}")
        print("-" * 40)
    
    conn.close()
    return True

if __name__ == "__main__":
    import_hotels()

