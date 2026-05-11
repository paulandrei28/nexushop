-- Create separate databases for each microservice
-- (simulates database-per-service pattern on a single PostgreSQL instance)

CREATE DATABASE orders_db;
CREATE DATABASE inventory_db;

-- Grant access to the ecommerce user
GRANT ALL PRIVILEGES ON DATABASE orders_db TO ecommerce;
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO ecommerce;
