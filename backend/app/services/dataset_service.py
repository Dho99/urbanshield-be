from datetime import datetime, timezone

DATASETS = [
    {"id": 1, "name": "OSM Waterways", "source": "OSM", "description": "Canals, rivers, streams, drains", "last_update": datetime.now(timezone.utc), "completeness": 0.92, "record_count": 1240},
    {"id": 2, "name": "OSM Road Network", "source": "OSM", "description": "Highway network", "last_update": datetime.now(timezone.utc), "completeness": 0.95, "record_count": 5820},
    {"id": 3, "name": "Administrative Boundaries", "source": "OSM", "description": "District polygons Bandung", "last_update": datetime.now(timezone.utc), "completeness": 1.0, "record_count": 30},
    {"id": 4, "name": "Historical Flood Events", "source": "BNPB", "description": "Flood occurrence records", "last_update": datetime.now(timezone.utc), "completeness": 0.78, "record_count": 86},
    {"id": 5, "name": "Rainfall Observations", "source": "BMKG", "description": "Daily rainfall proxy", "last_update": datetime.now(timezone.utc), "completeness": 0.85, "record_count": 365},
    {"id": 6, "name": "Population Statistics", "source": "BPS", "description": "District population density", "last_update": datetime.now(timezone.utc), "completeness": 0.88, "record_count": 30},
    {"id": 7, "name": "Elevation Model", "source": "DEM", "description": "SRTM-derived elevation per district", "last_update": datetime.now(timezone.utc), "completeness": 0.9, "record_count": 30},
]

def list_datasets(source: str | None = None):
    if source:
        return [d for d in DATASETS if d["source"].lower() == source.lower()]
    return DATASETS
