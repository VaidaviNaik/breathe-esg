# Decisions

## SAP: Flat File CSV/TXT (not IDoc or OData)
Chose flat file export because: IDocs require SAP middleware, OData needs API credentials. Most clients' sustainability teams export via SAP transaction ME2M or MB51 to CSV. Handled YYYYMMDD and DD.MM.YYYY date formats (both are real). German column headers (WERKS, MENGE, MEINS) are preserved as field names. Ignored MANDT cross-client complexity — assumed single-client extract.

## Utility: Portal CSV Export (not PDF, not API)
PDF requires OCR which adds unreliable complexity. Utility APIs (Green Button) are only available from ~30% of utilities in India. CSV portal export is universal. Handled misaligned billing periods (not always calendar months) via separate period_start/period_end fields.

## Travel: Concur/Navan-style CSV Export (not API pull)
Real Navan/Concur APIs require OAuth enterprise setup. CSV export is how 90% of finance/sustainability teams actually share this data. Handled missing distances by maintaining an airport-pair lookup table. Hotels use per-night emission factors (DEFRA guidance).

## What I'd ask the PM
1. Which SAP transaction codes does the client export from?
2. Are utility meters in multiple regulatory jurisdictions? (affects emission factor)
3. Does travel data include employee department for cost-center allocation?