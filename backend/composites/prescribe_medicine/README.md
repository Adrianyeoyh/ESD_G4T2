# Prescribe Medicine Composite Service

Composite microservice that orchestrates the medication prescription workflow by coordinating with multiple downstream services.

## Service Flow

```
1. UI → Composite: POST /prescribe/{recordId}
2. Composite → Clinical Records: GET /clinical-record/{recordId} [OPTIONAL]
3. Clinical Records → Composite: Return record data
4. Composite → Drug Catalogue: GET /drug (fetch all available drugs)
5. Composite → Drug Catalogue: PUT /drug/{drugId} (update stock quantities)
6. Drug Catalogue → Composite: Confirm stock update
7. Composite → Prescription Service: POST /prescription (create prescription record)
8. Prescription Service → Composite: Return prescription details
9. Composite → Invoice Service: POST /invoice (create invoice)
10. Invoice Service → Composite: Return invoice details
11. Composite → UI: Return successful prescription result
```

## API Endpoint

### POST /prescribe/{recordId}

Physician prescribes medications to a patient for a clinical record.

**Parameters:**
- `recordId` (path, integer): Clinical record ID

**Request Body:**
```json
{
  "items": [
    {
      "drugId": 1,
      "quantity": 2,
      "dosage": "10mg twice daily"
    },
    {
      "drugId": 3,
      "quantity": 1,
      "dosage": "5mg at bedtime"
    }
  ]
}
```

**Success Response (201 Created):**
```json
{
  "recordId": 1234,
  "patientId": "P5678",
  "items": [
    {
      "drugId": 1,
      "drugName": "Ibuprofen",
      "quantity": 2,
      "dosage": "10mg twice daily",
      "unitPrice": "10.00",
      "lineTotal": "20.00",
      "prescriptionId": "RX-456"
    },
    {
      "drugId": 3,
      "drugName": "Aspirin",
      "quantity": 1,
      "dosage": "5mg at bedtime",
      "unitPrice": "5.00",
      "lineTotal": "5.00",
      "prescriptionId": "RX-457"
    }
  ],
  "invoice": {
    "invoiceId": "INV-789",
    "recordId": 1234,
    "patientId": "P5678",
    "total": "25.00",
    "status": "UNPAID"
  },
  "total": "25.00",
  "status": "success"
}
```

## Error Handling

### Validation Errors (400)
```json
{
  "message": "items array cannot be empty",
  "error": "VALIDATION_ERROR"
}
```

Common validation errors:
- Missing required field: `items`
- `items` must be an array
- `items` array cannot be empty
- `items[{idx}].drugId` must be a positive integer
- `items[{idx}].quantity` must be a positive integer
- `items[{idx}].dosage` cannot be empty

### Not Found Errors (404)
```json
{
  "message": "Clinical record 1234 not found",
  "error": "NOT_FOUND"
}
```

Common scenarios:
- Clinical record doesn't exist
- Drug with specified ID not found

### Conflict Errors (409)
```json
{
  "message": "Insufficient stock for drug 123. Available: 5, Requested: 10",
  "error": "CONFLICT"
}
```

Common scenarios:
- Insufficient drug stock
- Cannot prescribe for closed clinical record

### Application Errors (500)
```json
{
  "message": "Failed to create prescription | Stock rollback may be incomplete",
  "error": "APPLICATION_ERROR"
}
```

### Service Unavailable (503)
```json
{
  "message": "Downstream service unavailable or timeout",
  "error": "DOWNSTREAM_TIMEOUT",
  "details": {"timeout_seconds": 8}
}
```

## Compensation & Rollback

If any operation fails after drug stock has been deducted, the service automatically attempts to restore stock quantities:

1. Drug stock is updated (deducted)
2. If prescription or invoice creation fails → **Automatic rollback** of stock
3. If rollback fails → Error response includes rollback failure details for manual intervention

Example rollback error:
```json
{
  "message": "Prescription failed: Failed to create invoice | Stock rollback may be incomplete: [...]",
  "error": "APPLICATION_ERROR"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `docker` | Environment type (`local` or `docker`) |
| `PORT` | `5007` | Port number |
| `DRUG_CATALOGUE_URL` | `http://drug_service:5001` | Drug catalogue service URL |
| `INVOICE_SERVICE_URL` | `http://invoice_service:5003` | Invoice service URL |
| `PRESCRIPTION_SERVICE_URL` | Empty | Prescription service URL |
| `CLINICAL_RECORDS_URL` | `http://record_service:5006` | Clinical records service URL |
| `CLINICAL_RECORD_VALIDATE_PATH` | `/record/{record_id}` | Path template for clinical records |
| `CLINICAL_RECORDS_REQUIRED` | `false` | Whether clinical records are required |
| `HTTP_TIMEOUT_SECONDS` | `8` | HTTP request timeout in seconds |

## Running Locally

1. **Install dependencies:**
```bash
pip install -r ../../requirements/prescribe_medicine.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your service URLs
```

3. **Start the service:**
```bash
python run.py
```

The service will start on `http://localhost:5007`

## Testing Examples

### Test Case 1: Successful Prescription
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "drugId": 1,
        "quantity": 2,
        "dosage": "10mg twice daily"
      }
    ]
  }'
```

### Test Case 2: Insufficient Stock
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "drugId": 1,
        "quantity": 1000
      }
    ]
  }'
# Expected: 409 Conflict - "Insufficient stock for drug 1"
```

### Test Case 3: Invalid Request
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{"items": []}'
# Expected: 400 Bad Request - "items array cannot be empty"
```

### Test Case 4: Missing Drug
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "drugId": 99999,
        "quantity": 1,
        "dosage": "test"
      }
    ]
  }'
# Expected: 404 Not Found - "Drug with id 99999 not found"
```

### Test Case 5: Service Timeout
```bash
# When a downstream service is unreachable/slow
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "drugId": 1,
        "quantity": 1,
        "dosage": "10mg"
      }
    ]
  }'
# Expected: 503 Service Unavailable
```

## Architecture Notes

- **Async-safe**: Compensation logic rolls back changes if any step fails
- **Timeout handling**: All HTTP requests have a configurable timeout (default: 8s)
- **Optional dependency**: Clinical records can be optional or required based on configuration
- **Error propagation**: Service errors from downstream services are parsed and returned to the client
- **Decimal precision**: Prices and totals are handled as string decimals to avoid floating-point errors
