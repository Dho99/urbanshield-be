CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS administrative_boundary (
  id SERIAL PRIMARY KEY,
  osm_id BIGINT,
  name TEXT NOT NULL,
  admin_level INT,
  parent_region TEXT,
  geom GEOMETRY(MultiPolygon, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_admin_geom ON administrative_boundary USING GIST (geom);

CREATE TABLE IF NOT EXISTS osm_waterways (
  id SERIAL PRIMARY KEY,
  osm_id BIGINT,
  osm_type TEXT,
  name TEXT,
  waterway TEXT,
  tags JSONB,
  kec_id INT REFERENCES administrative_boundary(id) ON DELETE SET NULL,
  geom GEOMETRY(Geometry, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_waterways_geom ON osm_waterways USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_waterways_kec ON osm_waterways (kec_id);

CREATE TABLE IF NOT EXISTS osm_roads (
  id SERIAL PRIMARY KEY,
  osm_id BIGINT,
  osm_type TEXT,
  name TEXT,
  highway TEXT,
  tags JSONB,
  kec_id INT REFERENCES administrative_boundary(id) ON DELETE SET NULL,
  geom GEOMETRY(Geometry, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_roads_geom ON osm_roads USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_roads_kec ON osm_roads (kec_id);

CREATE TABLE IF NOT EXISTS osm_facilities (
  id SERIAL PRIMARY KEY,
  osm_id BIGINT,
  osm_type TEXT,
  name TEXT,
  category TEXT NOT NULL,
  amenity TEXT,
  tags JSONB,
  kec_id INT REFERENCES administrative_boundary(id) ON DELETE SET NULL,
  geom GEOMETRY(Geometry, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_facilities_geom ON osm_facilities USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_facilities_kec ON osm_facilities (kec_id);

CREATE TABLE IF NOT EXISTS osm_buildings (
  id SERIAL PRIMARY KEY,
  osm_id BIGINT,
  osm_type TEXT,
  name TEXT,
  building TEXT,
  tags JSONB,
  kec_id INT REFERENCES administrative_boundary(id) ON DELETE SET NULL,
  geom GEOMETRY(Geometry, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_buildings_geom ON osm_buildings USING GIST (geom);

CREATE TABLE IF NOT EXISTS osm_landuse (
  id SERIAL PRIMARY KEY,
  osm_id BIGINT,
  osm_type TEXT,
  name TEXT,
  landuse TEXT,
  tags JSONB,
  kec_id INT REFERENCES administrative_boundary(id) ON DELETE SET NULL,
  geom GEOMETRY(Geometry, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_landuse_geom ON osm_landuse USING GIST (geom);

CREATE TABLE IF NOT EXISTS urban_features (
  kec_id INT PRIMARY KEY REFERENCES administrative_boundary(id) ON DELETE CASCADE,
  kec_name TEXT NOT NULL,
  drainase_m DOUBLE PRECISION DEFAULT 0,
  jalan_m DOUBLE PRECISION DEFAULT 0,
  sekolah_n INT DEFAULT 0,
  rs_n INT DEFAULT 0,
  fasum_n INT DEFAULT 0,
  buildings_n INT DEFAULT 0,
  drainase_density DOUBLE PRECISION DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);
