-- Migration: Remove dosage column and add drugName column to prescription table
-- Run this on existing databases to update the schema

-- Step 1: Drop the dosage constraint
ALTER TABLE prescription_schema.prescription 
    DROP CONSTRAINT IF EXISTS ck_prescription_dosage_not_blank;

-- Step 2: Drop the dosage column
ALTER TABLE prescription_schema.prescription 
    DROP COLUMN IF EXISTS dosage;

-- Step 3: Add drugName column (with temporary default for existing rows)
ALTER TABLE prescription_schema.prescription 
    ADD COLUMN IF NOT EXISTS "drugName" VARCHAR(255);

-- Step 4: Update existing rows - populate drugName from drug table
UPDATE prescription_schema.prescription p
SET "drugName" = d."drugName"
FROM drug_schema.drug d
WHERE p."drugId" = d."drugId"
  AND p."drugName" IS NULL;

-- Step 5: Set NOT NULL constraint after data is populated
ALTER TABLE prescription_schema.prescription 
    ALTER COLUMN "drugName" SET NOT NULL;
