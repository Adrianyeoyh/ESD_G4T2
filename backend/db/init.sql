CREATE SCHEMA IF NOT EXISTS invoice_schema;
CREATE SCHEMA IF NOT EXISTS payment_schema;
CREATE SCHEMA IF NOT EXISTS records_schema;
CREATE SCHEMA IF NOT EXISTS patient_schema;
CREATE SCHEMA IF NOT EXISTS drug_schema;

CREATE TABLE IF NOT EXISTS drug_schema.drug (
    "drugId"   SERIAL PRIMARY KEY,
    "drugName" VARCHAR(255) NOT NULL,
    quantity   INTEGER      NOT NULL DEFAULT 0,
    price      NUMERIC(10, 2) NOT NULL,
    purpose    VARCHAR(255),
    "recommendedDosage" VARCHAR(255),
    remarks    VARCHAR(500),
    CONSTRAINT uq_drug_name            UNIQUE ("drugName"),
    CONSTRAINT ck_quantity_non_negative CHECK (quantity >= 0),
    CONSTRAINT ck_price_positive        CHECK (price > 0)
);

CREATE INDEX IF NOT EXISTS ix_drug_name_ci ON drug_schema.drug (lower("drugName"));
