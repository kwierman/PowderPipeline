import math
from snowpack.models import Station


def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula for distance between two points on Earth
    R = 6371  # Radius of Earth in kilometers
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


def get_closest_object(user_lat, user_lon):
    closest_object = None
    min_distance = float("inf")

    for obj in Station.objects.all():
        distance = calculate_distance(user_lat, user_lon, obj.latitude, obj.longitude)
        if distance < min_distance:
            min_distance = distance
            closest_object = obj

    return closest_object
