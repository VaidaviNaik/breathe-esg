# Data Model

## Core Design Decisions

### Multi-tenancy
Every `EmissionRecord` and `IngestionBatch` has a FK to `Client`. All queries filter by client_id. No row is accessible across client boundaries.

### Scope Classification
- Scope 1 (Direct): SAP fuel combustion data
- Scope 2 (Indirect - Energy): Utility electricity consumption
- Scope 3 (Value Chain): Corporate travel (flights, hotels, ground transport)

### Source-of-Truth Tracking
- `IngestionBatch` records every upload: when, from where, which file, how many rows parsed
- `EmissionRecord.raw_data` stores the original CSV row as JSON — never mutated
- `EmissionRecord.is_edited` + `edit_reason` track post-ingestion changes
- `source_row_id` links back to the original row identifier in the source system

### Unit Normalization
All quantities are normalized at ingestion time:
- Fuel: converted to liters (gallons × 3.785)
- Energy: stored as kWh
- Travel: distance in km, duration in nights
- `activity_unit_original` preserves what came in

### Audit Trail
- `created_at` / `updated_at` on all records
- `reviewed_by`, `reviewed_at`, `analyst_note` on EmissionRecord
- ParseError table logs every row that failed with original content