from django.db import models

class PreExtractedLocation(models.Model):
    """
    Modèle pour stocker les lieux pré-extraits de Fès depuis OpenStreetMap
    """
    name = models.CharField(max_length=500, db_index=True)
    longitude = models.FloatField()
    latitude = models.FloatField()
    location_type = models.CharField(max_length=100, null=True, blank=True)
    
    # Index pour améliorer les performances de recherche
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['location_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.location_type})"
    
    @property
    def coordinates(self):
        """Retourne les coordonnées au format [longitude, latitude]"""
        return [self.longitude, self.latitude]

