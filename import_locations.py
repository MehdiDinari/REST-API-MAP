import os
import sys
import django
import json

# Ajouter le chemin du projet Django
sys.path.append('/home/ubuntu/project/route_finder_project/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'route_finder.settings')

# Configurer Django
django.setup()

from api.models import PreExtractedLocation

def import_locations_from_json(json_file_path):
    """
    Importe les lieux depuis le fichier JSON dans la base de données Django
    """
    print(f"Importation des lieux depuis {json_file_path}...")
    
    # Vider la table existante
    PreExtractedLocation.objects.all().delete()
    print("Table PreExtractedLocation vidée.")
    
    # Charger les données JSON
    with open(json_file_path, 'r', encoding='utf-8') as f:
        locations_data = json.load(f)
    
    print(f"Chargement de {len(locations_data)} lieux...")
    
    # Importer les lieux par lots pour améliorer les performances
    batch_size = 1000
    locations_to_create = []
    
    for i, location in enumerate(locations_data):
        name = location.get('name', '')
        coordinates = location.get('coordinates', [])
        location_type = location.get('type', '')
        
        # Vérifier que les coordonnées sont valides
        if len(coordinates) == 2 and isinstance(coordinates[0], (int, float)) and isinstance(coordinates[1], (int, float)):
            longitude, latitude = coordinates
            
            # Créer l'objet PreExtractedLocation
            location_obj = PreExtractedLocation(
                name=name,
                longitude=longitude,
                latitude=latitude,
                location_type=str(location_type) if location_type else None
            )
            locations_to_create.append(location_obj)
            
            # Insérer par lots
            if len(locations_to_create) >= batch_size:
                PreExtractedLocation.objects.bulk_create(locations_to_create)
                print(f"Importé {i + 1} lieux...")
                locations_to_create = []
    
    # Insérer le dernier lot
    if locations_to_create:
        PreExtractedLocation.objects.bulk_create(locations_to_create)
    
    total_count = PreExtractedLocation.objects.count()
    print(f"Importation terminée. {total_count} lieux importés dans la base de données.")

if __name__ == "__main__":
    json_file_path = "fess_locations.json"
    import_locations_from_json(json_file_path)

