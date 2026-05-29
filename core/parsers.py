import csv, io
from datetime import datetime, date

# --- SAP Parser ---
# We chose SAP flat file (CSV/tab-delimited) export format.
# Real SAP exports use transaction ME2M/MB51 exported as .txt or .csv.
# Common headers (sometimes German): MANDT, WERKS (plant), MATNR (material),
# MENGE (quantity), MEINS (unit), BUDAT (posting date), BELNR (document number)

SAP_EMISSION_FACTOR = {
    'diesel': 2.68,    # kg CO2e per liter
    'petrol': 2.31,
    'lpg': 1.51,
    'natural_gas': 2.04,  # per cubic meter
}

UNIT_NORMALIZATION = {
    'L': 'liters', 'LTR': 'liters', 'liters': 'liters',
    'KG': 'kg', 'KGS': 'kg',
    'M3': 'm3', 'cubic_meter': 'm3',
    'GAL': 'liters',  # US gallon -> we'll multiply by 3.785
}

def normalize_unit(value, unit):
    unit = unit.strip().upper()
    if unit == 'GAL':
        return value * 3.785, 'liters'
    return value, UNIT_NORMALIZATION.get(unit, unit.lower())

def parse_sap_csv(file_content, batch, client):
    records = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader, start=1):
        try:
            material = row.get('MATNR', row.get('material', '')).lower().strip()
            qty_raw = float(row.get('MENGE', row.get('quantity', 0)))
            unit_raw = row.get('MEINS', row.get('unit', 'L')).strip()
            date_raw = row.get('BUDAT', row.get('date', ''))
            plant = row.get('WERKS', row.get('plant', ''))

            # Parse date: SAP uses YYYYMMDD or DD.MM.YYYY
            try:
                if '.' in date_raw:
                    parsed_date = datetime.strptime(date_raw, '%d.%m.%Y').date()
                elif len(date_raw) == 8:
                    parsed_date = datetime.strptime(date_raw, '%Y%m%d').date()
                else:
                    parsed_date = datetime.strptime(date_raw, '%Y-%m-%d').date()
            except:
                parsed_date = date.today()

            qty_normalized, unit_normalized = normalize_unit(qty_raw, unit_raw)

            fuel_type = 'diesel'
            for key in SAP_EMISSION_FACTOR:
                if key in material:
                    fuel_type = key
                    break

            co2e = qty_normalized * SAP_EMISSION_FACTOR.get(fuel_type, 2.68)

            records.append({
                'client': client,
                'batch': batch,
                'scope': 1,
                'category': fuel_type,
                'activity_value': qty_normalized,
                'activity_unit': unit_normalized,
                'activity_unit_original': unit_raw,
                'co2e_kg': co2e,
                'period_start': parsed_date,
                'period_end': parsed_date,
                'location': plant,
                'source_row_id': str(i),
                'raw_data': dict(row),
                'status': 'PENDING',
            })
        except Exception as e:
            errors.append({'row_number': i, 'raw_row': dict(row), 'error_message': str(e)})

    return records, errors


# --- Utility Parser ---
# Portal CSV export (most common: Green Button data or utility portal download)
# Typical columns: meter_id, billing_period_start, billing_period_end, kwh, tariff

ELECTRICITY_EF = 0.82  # kg CO2e per kWh — India grid average (CEA 2023)

def parse_utility_csv(file_content, batch, client):
    records = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader, start=1):
        try:
            kwh_raw = float(row.get('kwh', row.get('consumption_kwh', row.get('units', 0))))
            meter_id = row.get('meter_id', row.get('account_number', ''))
            start_raw = row.get('billing_period_start', row.get('period_start', ''))
            end_raw = row.get('billing_period_end', row.get('period_end', ''))
            location = row.get('facility', row.get('site', ''))

            def parse_date(s):
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        return datetime.strptime(s.strip(), fmt).date()
                    except:
                        continue
                return date.today()

            co2e = kwh_raw * ELECTRICITY_EF

            records.append({
                'client': client,
                'batch': batch,
                'scope': 2,
                'category': 'electricity',
                'activity_value': kwh_raw,
                'activity_unit': 'kWh',
                'activity_unit_original': 'kWh',
                'co2e_kg': co2e,
                'period_start': parse_date(start_raw),
                'period_end': parse_date(end_raw),
                'location': f"{location} | meter:{meter_id}",
                'source_row_id': meter_id or str(i),
                'raw_data': dict(row),
                'status': 'PENDING',
            })
        except Exception as e:
            errors.append({'row_number': i, 'raw_row': dict(row), 'error_message': str(e)})

    return records, errors


# --- Travel Parser ---
# Based on Concur/Navan export format
# Columns: trip_id, employee_id, travel_type (flight/hotel/car), 
#          origin, destination, departure_date, return_date, distance_km, class

TRAVEL_EF = {
    'flight_economy': 0.255,   # kg CO2e per km (ICAO average)
    'flight_business': 0.765,
    'flight_first': 1.02,
    'car_rental': 0.171,       # per km
    'hotel': 31.2,             # per night (kg CO2e)
    'train': 0.041,            # per km
}

AIRPORT_DISTANCES = {
    ('BOM', 'DEL'): 1148, ('DEL', 'BOM'): 1148,
    ('BOM', 'BLR'): 845,  ('BLR', 'BOM'): 845,
    ('DEL', 'BLR'): 1740, ('BLR', 'DEL'): 1740,
    ('BOM', 'CCU'): 1650, ('CCU', 'BOM'): 1650,
    ('LHR', 'JFK'): 5540, ('JFK', 'LHR'): 5540,
    ('LHR', 'BOM'): 7191, ('BOM', 'LHR'): 7191,
}

def parse_travel_csv(file_content, batch, client):
    records = []
    errors = []
    reader = csv.DictReader(io.StringIO(file_content))

    for i, row in enumerate(reader, start=1):
        try:
            travel_type = row.get('travel_type', 'flight').lower().strip()
            cabin = row.get('class', 'economy').lower().strip()
            origin = row.get('origin', '').strip().upper()
            destination = row.get('destination', '').strip().upper()
            dep_date = row.get('departure_date', '')
            ret_date = row.get('return_date', dep_date)

            def parse_date(s):
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(s.strip(), fmt).date()
                    except:
                        continue
                return date.today()

            if travel_type == 'hotel':
                nights = float(row.get('nights', 1))
                ef_key = 'hotel'
                activity_value = nights
                activity_unit = 'nights'
                co2e = nights * TRAVEL_EF['hotel']
                loc = row.get('city', destination)
            else:
                dist_raw = row.get('distance_km', '')
                if dist_raw:
                    dist = float(dist_raw)
                else:
                    dist = AIRPORT_DISTANCES.get((origin, destination), 1000)

                if 'flight' in travel_type:
                    ef_key = f"flight_{cabin}" if f"flight_{cabin}" in TRAVEL_EF else 'flight_economy'
                elif 'car' in travel_type:
                    ef_key = 'car_rental'
                else:
                    ef_key = 'train'

                activity_value = dist
                activity_unit = 'km'
                co2e = dist * TRAVEL_EF[ef_key]
                loc = f"{origin} → {destination}"

            records.append({
                'client': client,
                'batch': batch,
                'scope': 3,
                'category': travel_type,
                'activity_value': activity_value,
                'activity_unit': activity_unit,
                'activity_unit_original': activity_unit,
                'co2e_kg': co2e,
                'period_start': parse_date(dep_date),
                'period_end': parse_date(ret_date),
                'location': loc,
                'source_row_id': row.get('trip_id', str(i)),
                'raw_data': dict(row),
                'status': 'PENDING',
            })
        except Exception as e:
            errors.append({'row_number': i, 'raw_row': dict(row), 'error_message': str(e)})

    return records, errors