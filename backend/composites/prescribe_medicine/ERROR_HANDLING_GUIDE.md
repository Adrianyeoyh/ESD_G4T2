# Error Handling Guide - Prescribe Medicine Composite Service

This guide explains the comprehensive error handling implemented in the prescribe medicine composite service.

## Error Handling Architecture

The service implements multi-layer error handling:

1. **Input Validation Layer** (Controller): Validates request format and data types
2. **Business Logic Layer** (Service): Validates business constraints and orchestration
3. **Integration Layer** (Service): Handles downstream service errors
4. **Global Error Handlers**: Standardized error responses across all error types

## Error Response Format

All error responses follow this standard format:

```json
{
  "message": "Human-readable error description",
  "error": "ERROR_CODE",
  "details": {
    "additional": "information (optional)"
  }
}
```

## Error Types and HTTP Status Codes

### 400 - Bad Request (Validation Errors)

**When:** Request data is invalid or missing required fields

**Examples:**
```json
{
  "message": "items array cannot be empty",
  "error": "VALIDATION_ERROR"
}
```

```json
{
  "message": "items[0].quantity must be a positive integer",
  "error": "VALIDATION_ERROR"
}
```

**Common validation errors:**
- Missing required fields: `items`, `drugId`, `quantity`, `dosage`
- Invalid data types: `drugId` must be integer, `quantity` must be positive integer
- Invalid formats: `dosage` cannot be empty, exceeds length limits
- Empty arrays: `items` array cannot be empty
- Invalid JSON structure

**How to fix:**
- Ensure all required fields are present
- Use correct data types (integers for drugId/quantity)
- Provide non-empty strings for dosage
- Send at least one item in the items array

---

### 404 - Not Found

**When:** A required resource doesn't exist

**Examples:**
```json
{
  "message": "Clinical record 1234 not found",
  "error": "NOT_FOUND"
}
```

```json
{
  "message": "Drug with id 999 not found",
  "error": "NOT_FOUND"
}
```

**Common scenarios:**
- Clinical record doesn't exist in the clinical records service
- Drug with specified ID not found in drug catalogue
- Patient record not found

**How to fix:**
- Verify the recordId exists in clinical records service
- Verify the drugId exists in the drug catalogue
- Check if the record/drug was recently deleted

---

### 409 - Conflict

**When:** Resource state conflicts with the operation

**Examples:**
```json
{
  "message": "Insufficient stock for drug 1. Available: 5, Requested: 10",
  "error": "CONFLICT"
}
```

```json
{
  "message": "Cannot prescribe for closed clinical record 1234",
  "error": "CONFLICT"
}
```

**Common scenarios:**
- Drug quantity available is less than requested
- Clinical record is marked as closed
- Another concurrent operation interferes

**How to fix:**
- Check available drug quantities before prescribing
- Ensure the clinical record is open
- Verify the drug was not already deducted by another operation
- Retry the operation

---

### 500 - Internal Server Error

**When:** Application encounters an unexpected error or downstream service fails critically

**Examples:**
```json
{
  "message": "Failed to create prescription | Stock rollback may be incomplete",
  "error": "APPLICATION_ERROR"
}
```

**Common scenarios:**
- Prescription service is unavailable
- Invoice service returns an error
- Database error during operations
- Rollback operation fails

**How to fix:**
- Contact system administrator
- Check if downstream services are running
- Review server logs for detailed error information
- If stock rollback failed, manual stock adjustment may be needed

---

### 503 - Service Unavailable

**When:** A downstream service is unavailable or request times out

**Examples:**
```json
{
  "message": "Downstream service unavailable or timeout",
  "error": "DOWNSTREAM_TIMEOUT",
  "details": {
    "timeout_seconds": 8
  }
}
```

```json
{
  "message": "Unable to reach downstream service. Service may be unavailable.",
  "error": "DOWNSTREAM_CONNECTION_ERROR"
}
```

**Common scenarios:**
- Clinical records service is down
- Drug catalogue service is down
- Prescription service is down
- Invoice service is down
- Network connectivity issues
- Request exceeds timeout threshold (default: 8 seconds)

**How to fix:**
- Verify all downstream services are running
- Check network connectivity
- Retry the operation (with exponential backoff recommended)
- Check service health endpoints
- Increase timeout if services are slow (adjust `HTTP_TIMEOUT_SECONDS`)

---

## Compensation and Rollback

The service implements automatic rollback when operations fail after stock has been deducted:

### Rollback Flow

```
1. Deduct drug stock ✓
2. Create prescription ✗ (fails)
   ↓
3. Rollback: Restore drug stock
```

### Rollback Success

If rollback succeeds, the error message indicates clean failure:
```json
{
  "message": "Failed to create prescription",
  "error": "APPLICATION_ERROR"
}
```
**Status:** Clean state restored, can retry safely

### Rollback Failure

If rollback also fails, manual intervention is needed:
```json
{
  "message": "Prescription failed: Failed to create prescription | Stock rollback may be incomplete: [...]",
  "error": "APPLICATION_ERROR"
}
```
**Status:** Stock quantities may be inconsistent - requires manual fix

---

## Error Handling Strategies

### For Client Applications

1. **Retry with Exponential Backoff**
   ```python
   # Retry on 503 with exponential backoff
   import time
   
   max_retries = 3
   for attempt in range(max_retries):
       try:
           response = prescribe_medicine(record_id, items)
           break
       except Exception as e:
           if e.status_code == 503 and attempt < max_retries - 1:
               wait_time = 2 ** attempt  # 1, 2, 4 seconds
               time.sleep(wait_time)
           else:
               raise
   ```

2. **Validate Input Before Sending**
   ```python
   # Validate locally before API call
   def validate_prescription_request(items):
       if not items:
           raise ValueError("Items cannot be empty")
       
       for idx, item in enumerate(items):
           if not isinstance(item['drugId'], int):
               raise ValueError(f"items[{idx}].drugId must be integer")
           if item['quantity'] <= 0:
               raise ValueError(f"items[{idx}].quantity must be positive")
           if not item['dosage'].strip():
               raise ValueError(f"items[{idx}].dosage cannot be empty")
   ```

3. **Handle Specific Error Codes**
   ```python
   def handle_prescription_response(response):
       if response.status_code == 201:
           return response.json()  # Success
       
       error_data = response.json()
       error_code = error_data.get('error')
       
       if error_code == 'VALIDATION_ERROR':
           # Show validation errors to user
           log_and_display_error(error_data['message'])
       elif error_code == 'NOT_FOUND':
           # Handle missing resources
           notify_user_check_ids()
       elif error_code == 'CONFLICT':
           # Handle conflicts (e.g., insufficient stock)
           log_stock_update_needed()
       elif error_code == 'DOWNSTREAM_TIMEOUT':
           # Recommend retry
           schedule_retry()
       else:
           # Generic error handling
           log_critical_error(error_data)
   ```

### For Operations/Administrators

1. **Monitor for Rollback Failures**
   - Watch application logs for "Stock rollback may be incomplete" messages
   - These indicate manual stock reconciliation may be needed

2. **Check Service Health**
   ```bash
   # Verify all downstream services
   curl http://localhost:5001/health  # Drug catalogue
   curl http://localhost:5003/health  # Invoice service
   curl http://localhost:5005/health  # Prescription service
   curl http://localhost:5006/health  # Clinical records (if configured)
   ```

3. **Review Timeout Configuration**
   - Default timeout: 8 seconds (`HTTP_TIMEOUT_SECONDS`)
   - Increase if services are slow but reliable
   - Decrease if services should be more responsive

---

## Error Prevention Best Practices

### 1. Input Validation

```python
# Good - Validate before API call
def prescribe_medicine_safe(record_id, items):
    # Validate record_id
    if not isinstance(record_id, int) or record_id <= 0:
        raise ValueError("Invalid record_id")
    
    # Validate items
    if not items or not isinstance(items, list):
        raise ValueError("Items must be non-empty list")
    
    for item in items:
        if 'drugId' not in item or item['drugId'] <= 0:
            raise ValueError("Valid drugId required")
    
    # Now safe to call service
    return prescribe_medicine(record_id, items)
```

### 2. Use Strong Types

```python
# Good - Type hints prevent common errors
from typing import List, Dict

def prescribe_medicine(
    record_id: int,
    items: List[Dict[str, any]]
) -> Dict:
    ...
```

### 3. Implement Idempotency (if applicable)

```python
# Use idempotency keys to prevent duplicate prescriptions
prescribe_medicine(
    record_id=1234,
    items=items,
    idempotency_key="unique-prescription-123"
)
```

### 4. Log Comprehensive Information

```python
# Log context about errors for debugging
logger.error(
    "Prescription failed",
    extra={
        "record_id": record_id,
        "item_count": len(items),
        "error": str(error),
        "downstream_service": service_name
    }
)
```

---

## Testing Error Scenarios

### Unit Tests
```python
def test_insufficient_stock_error():
    service = PrescribeMedicineService()
    with pytest.raises(ConflictError) as exc:
        service.prescribe_medicine(1234, [
            {"drugId": 1, "quantity": 1000000, "dosage": "test"}
        ])
    assert "Insufficient stock" in str(exc.value.message)
```

### Integration Tests
```bash
# Test 404 error
curl -X POST http://localhost:5007/prescribe/99999 \
  -H "Content-Type: application/json" \
  -d '{"items": [{"drugId": 1, "quantity": 1, "dosage": "test"}]}'

# Test 400 validation error
curl -X POST http://localhost:5007/prescribe/1234 \
  -H "Content-Type: application/json" \
  -d '{"items": []}'
```

---

## Quick Reference

| Error | HTTP Code | Recovery | Retry |
|-------|-----------|----------|-------|
| Validation Error | 400 | Fix request | No |
| Not Found | 404 | Check IDs | No |
| Insufficient Stock | 409 | Adjust quantity | Maybe |
| Service Error | 500 | Check service logs | Maybe |
| Service Timeout | 503 | Retry later | Yes |
| Rollback Failure | 500 | Manual intervention | No |

---

## Support and Debugging

For detailed errors, check application logs:

```bash
# View recent errors
docker logs <container-name>

# View specific error patterns
docker logs <container-name> | grep "ERROR"
docker logs <container-name> | grep "Stock rollback"
```

Contact: [Admin Email/Support Channel]
