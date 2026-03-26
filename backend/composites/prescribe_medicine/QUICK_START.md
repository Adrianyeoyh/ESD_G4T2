# Quick Start Guide - Prescribe Medicine Composite

## 🚀 Getting Started

### 1. Start the Service

```bash
# Install dependencies
pip install -r ../../requirements/prescribe_medicine.txt

# Configure environment
cp .env.example .env
# Edit .env with your service URLs

# Run the service
python run.py
```

The service will be available at: `http://localhost:5007`

---

## 📋 Basic Usage

### Successful Prescription

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

**Response (201 Created):**
```json
{
  "recordId": 1234,
  "patientId": 5678,
  "items": [{
    "drugId": 1,
    "drugName": "Ibuprofen",
    "quantity": 2,
    "dosage": "10mg twice daily",
    "unitPrice": "10.00",
    "lineTotal": "20.00",
    "prescriptionId": "RX-456"
  }],
  "invoice": {...},
  "total": "20.00",
  "status": "success"
}
```

---

## ❌ Common Error Scenarios

### 1. Validation Error (400)
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{"items": []}'
```
**Response:**
```json
{
  "message": "items array cannot be empty",
  "error": "VALIDATION_ERROR"
}
```

### 2. Insufficient Stock (409)
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{
      "drugId": 1,
      "quantity": 10000,
      "dosage": "10mg"
    }]
  }'
```
**Response:**
```json
{
  "message": "Insufficient stock for drug 1. Available: 50, Requested: 10000",
  "error": "CONFLICT"
}
```

### 3. Drug Not Found (404)
```bash
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{
      "drugId": 99999,
      "quantity": 1,
      "dosage": "10mg"
    }]
  }'
```
**Response:**
```json
{
  "message": "Drug with id 99999 not found",
  "error": "NOT_FOUND"
}
```

### 4. Service Unavailable (503)
```json
{
  "message": "Downstream service unavailable or timeout",
  "error": "DOWNSTREAM_TIMEOUT",
  "details": {"timeout_seconds": 8}
}
```
**Solution:** Retry after a delay, or check if downstream services are running

---

## 🧪 Testing

### Run all test cases
```bash
bash test_cases.sh
```

### Run specific test cases
```bash
# Successful prescription
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{"items": [{"drugId": 1, "quantity": 2, "dosage": "10mg twice daily"}]}'

# Multiple items
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"drugId": 1, "quantity": 2, "dosage": "10mg twice daily"},
      {"drugId": 2, "quantity": 1, "dosage": "5mg at bedtime"}
    ]
  }'
```

### Run unit tests
```bash
pytest tests/test_prescription.py -v
```

---

## 📚 Full Documentation

- **API Documentation**: See [README.md](README.md)
- **Error Handling Guide**: See [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)
- **Implementation Details**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## 🔧 Configuration

Edit `.env` to configure:

```bash
# Service port
PORT=5007

# Downstream service URLs
DRUG_CATALOGUE_URL=http://drug_service:5001
INVOICE_SERVICE_URL=http://invoice_service:5003
PRESCRIPTION_SERVICE_URL=
CLINICAL_RECORDS_URL=http://record_service:5006

# Settings
CLINICAL_RECORDS_REQUIRED=false  # Set to 'true' to require clinical records
HTTP_TIMEOUT_SECONDS=8           # Timeout for downstream calls
```

---

## 🛡️ Error Handling Features

- ✅ Automatic stock rollback on failure
- ✅ Comprehensive validation of all inputs
- ✅ Clear, actionable error messages
- ✅ Structured error responses
- ✅ Timeout handling for downstream services
- ✅ Proper HTTP status codes

---

## 🔍 Debugging

### View application logs
```bash
# Using Docker
docker logs <container-name>

# View error messages
docker logs <container-name> | grep ERROR

# View rollback events
docker logs <container-name> | grep "rollback"
```

### Check service health
```bash
curl http://localhost:5001/health  # Drug catalogue
curl http://localhost:5003/health  # Invoice service
curl http://localhost:5005/health  # Prescription service
```

---

## 📞 Troubleshooting

| Issue | Solution |
|-------|----------|
| 503 Service Unavailable | Check if downstream services are running |
| 404 Not Found | Verify the recordId and drugIds exist |
| 409 Insufficient Stock | Check available drug quantities, reduce prescribed amount |
| 400 Validation Error | Review error message, ensure correct field names and types |
| Rollback incomplete | Check admin logs, manual stock adjustment may be needed |

---

## 💡 Key Features

1. **Orchestrates 4 Microservices** - Clinical Records, Drug Catalogue, Prescription, Invoice
2. **Automatic Compensation** - Rolls back stock changes if anything fails
3. **Comprehensive Error Handling** - 7 error scenarios with clear messages
4. **Request Validation** - Validates all inputs with specific error feedback
5. **Type Safety** - Proper type checking for all fields
6. **Timeout Management** - Configurable timeouts for all services
7. **Well Documented** - Complete API docs and error handling guide

---

**For more details, see:** [README.md](README.md) | [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)
