# Sources Research

## SAP — Fuel & Procurement
**Format researched:** SAP MM (Materials Management) flat file export via MB51 (material document list) or ME2M (purchase orders). Standard columns include MANDT (client), WERKS (plant code), MATNR (material number), MENGE (quantity), MEINS (unit of measure), BUDAT (posting date), BELNR (document number).
**What I learned:** Units come as SAP internal codes (L=liters, KG=kilograms, M3=cubic meters, GAL=gallons). Dates vary by system locale — German installs use DD.MM.YYYY, international use YYYYMMDD. Material descriptions are often codes, not plain text.
**Sample data rationale:** Included both date formats, German column names, and a gallon entry to test normalization.
**What would break in real deployment:** Plant code to location mapping requires a separate SAP lookup (T001W table). Material codes need a master data mapping to fuel type.

## Utility — Electricity
**Format researched:** Utility portal CSV exports (MSEDCL, BESCOM, BSES in India context). Green Button CSV format for US utilities. Typical columns: account number, meter ID, billing period, consumption (kWh/units), demand (kVA), tariff category, amount billed.
**What I learned:** Billing periods rarely align with calendar months. Industrial meters bill on kVA demand + kWh consumption. Emission factors differ by grid zone (India CEA publishes state-wise emission factors annually).
**Sample data rationale:** Included overlapping billing periods and multiple facilities to test period handling.
**What would break:** Multi-tariff bills (day/night rates) would need row-level disaggregation. PDF bills from older utilities have no structured export.

## Corporate Travel — Flights, Hotels, Ground
**Format researched:** Concur Travel expense report export, Navan (formerly TripActions) CSV download. Standard columns: trip ID, employee ID, travel type, origin/destination (airport IATA codes for flights, city for hotels), departure/return dates, booking class, cost.
**What I learned:** Distance is often absent — must be derived from IATA pairs. Hotel emissions require per-night factors (DEFRA: ~31.2 kg CO2e/room/night average). Business class has ~3x the economy emission factor (ICAO methodology).
**Sample data rationale:** Included domestic Indian routes (BOM-DEL), international (LHR-JFK), hotel nights, and ground transport.
**What would break:** Connecting flights counted as single segments would undercount emissions. Employee-level aggregation requires HR department data not in travel exports.