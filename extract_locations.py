import osmnx as ox
import json
import os

# Définir la ville et le pays
city = "Fès"
country = "Maroc"
place_name = f"{city}, {country}"

# Définir les tags pour les lieux et les routes
tags = {
    "place": ["city", "town", "village", "hamlet", "suburb", "quarter", "neighbourhood", "isolated_dwelling"],
    "highway": ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "service", "pedestrian", "track", "path"],
    "amenity": True,
    "building": True,
    "shop": True,
    "tourism": True,
    "leisure": True,
    "name": True
}

# Obtenir le graphe de la ville pour les routes
G = ox.graph_from_place(place_name, network_type="all")

# Extraire les nœuds et les arêtes (routes) avec leurs noms
named_edges = []
for u, v, k, data in G.edges(keys=True, data=True):
    if "name" in data:
        if isinstance(data["name"], list):
            for name in data["name"]:
                named_edges.append({"name": name, "coordinates": [[G.nodes[u]["x"], G.nodes[u]["y"]], [G.nodes[v]["x"], G.nodes[v]["y"]]], "type": "highway"})
        else:
            named_edges.append({"name": data["name"], "coordinates": [[G.nodes[u]["x"], G.nodes[u]["y"]], [G.nodes[v]["x"], G.nodes[v]["y"]]], "type": "highway"})

# Extraire les lieux (points d'intérêt) en utilisant ox.features_from_place
places = ox.features_from_place(place_name, tags)

# Filtrer et formater les lieux
formatted_places = []
for idx, row in places.iterrows():
    name = row.get("name")
    if name:
        geom = row.geometry
        if geom.geom_type == "Point":
            coords = [geom.x, geom.y]
        elif geom.geom_type in ["Polygon", "MultiPolygon"]:
            coords = [geom.centroid.x, geom.centroid.y]
        else:
            continue
        formatted_places.append({"name": name, "coordinates": coords, "type": row.get("highway") or row.get("amenity") or row.get("building") or row.get("shop") or row.get("tourism") or row.get("leisure") or row.get("place")})

# Combiner les routes et les lieux
all_locations = named_edges + formatted_places

# Sauvegarder les données dans un fichier JSON dans le même répertoire que le script
output_file = os.path.join(os.path.dirname(__file__), "fess_locations.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_locations, f, ensure_ascii=False, indent=4)

print(f"Extraction terminée. {len(all_locations)} lieux et routes sauvegardés dans {output_file}")