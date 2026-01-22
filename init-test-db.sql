-- Create test database
CREATE DATABASE taxonomy_builder_test;
GRANT ALL PRIVILEGES ON DATABASE taxonomy_builder_test TO taxonomy;

-- Create Keycloak database and user
CREATE USER keycloak WITH PASSWORD 'keycloak';
CREATE DATABASE keycloak OWNER keycloak;
GRANT ALL PRIVILEGES ON DATABASE keycloak TO keycloak;
