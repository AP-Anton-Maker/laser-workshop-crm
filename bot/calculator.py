def calculate_price(calc_type, params, base_price, min_price):
    try:
        if calc_type == 'fixed':
            price = float(params.get('quantity', 1)) * float(base_price)
        elif calc_type in ('area_cm2', 'photo_raster'):
            price = float(params.get('length', 0)) * float(params.get('width', 0)) * float(base_price)
        elif calc_type == 'meter_thickness':
            price = float(params.get('meters', 0)) * float(base_price) * (float(params.get('thickness', 3)) / 3.0)
        elif calc_type == 'per_minute':
            price = float(params.get('minutes', 0)) * float(base_price)
        elif calc_type == 'per_char':
            price = float(params.get('chars', 0)) * float(base_price)
        elif calc_type == 'vector_length':
            price = float(params.get('vector_meters', 0)) * float(base_price)
        elif calc_type == 'setup_batch':
            setup = float(params.get('setup_cost', base_price))
            per_unit = float(params.get('per_unit_price', 0))
            qty = float(params.get('quantity', 1))
            price = setup + (per_unit * qty)
        elif calc_type == 'cylindrical':
            diameter = float(params.get('diameter', 0))
            length_cm = float(params.get('length', 0))
            area = (diameter * 3.14 * length_cm) / 100
            price = area * float(base_price)
        elif calc_type == 'volume_3d':
            area_cm2 = float(params.get('area', 0))
            depth_mm = float(params.get('depth', 1))
            price = area_cm2 * depth_mm * float(base_price)
        elif calc_type == 'complex':
            material = float(params.get('material_cost', 0))
            cutting = float(params.get('cutting_meters', 0))
            rate = float(params.get('cutting_rate', base_price))
            price = material + (cutting * rate)
        else:
            price = float(base_price)
        return max(float(price), float(min_price))
    except:
        return float(min_price)
