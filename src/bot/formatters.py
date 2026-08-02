import re
from src.models.exercise import ExerciseType

def parse_duration_string(text: str) -> float | None:
    """
    Parses duration string like '1ч 30мин 15с', '1м30с', '45с' or raw number (treated as seconds).
    Returns total seconds as float.
    """
    text = text.strip().lower()
    # Check if any duration units are present
    hours_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ч|h|час|часов|часа)', text)
    mins_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:мин|min|м|m)', text)
    secs_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:с|s|сек|sec|секунд|секунды)', text)

    
    if hours_match or mins_match or secs_match:
        total_seconds = 0.0
        if hours_match:
            total_seconds += float(hours_match.group(1)) * 3600
        if mins_match:
            total_seconds += float(mins_match.group(1)) * 60
        if secs_match:
            total_seconds += float(secs_match.group(1))
        return total_seconds
        
    # If raw number without units
    try:
        val = float(text.replace(',', '.'))
        return val
    except ValueError:
        return None

def parse_set_input(text: str, exercise_type: ExerciseType) -> dict:
    """
    Parses a string input based on ExerciseType.
    Returns a dict with parsed fields (reps, weight, distance, duration) or empty dict if invalid.
    Base units in DB: distance in meters, duration in seconds.
    If units not specified: distance = meters, duration = seconds ('500 45' -> 500m, 45s).
    """
    text = text.replace(',', '.').strip()
    
    if exercise_type == ExerciseType.strength:
        # Delimiters: x, х (cyrillic), -, space, *
        # Strip words like кг, kg, раз, reps
        cleaned = re.sub(r'(?i)(кг|kg|раз|reps|повторений|повт)', '', text)
        split_pattern = r'\s*[xXхХ\-\* ]+\s*'
        parts = [p for p in re.split(split_pattern, cleaned.strip()) if p]
        if len(parts) >= 2:
            try:
                return {"reps": int(parts[0]), "weight": float(parts[1])}
            except ValueError:
                pass

    elif exercise_type == ExerciseType.cardio:
        # Check if letters exist
        has_letters = bool(re.search(r'[a-zA-Zа-яА-Я]', text))
        if not has_letters:
            # Raw numbers: '500 45' -> 500 meters, 45 seconds
            parts = [p for p in re.split(r'[\s\-xXхХ\*]+', text.strip()) if p]
            if len(parts) >= 2:
                try:
                    return {"distance": float(parts[0]), "duration": float(parts[1])}
                except ValueError:
                    pass
        else:
            # Parse distance with regex
            dist_val = None
            dist_match = re.search(r'(\d+(?:\.\d+)?)\s*(км|km|м|m)', text, re.IGNORECASE)
            if dist_match:
                val = float(dist_match.group(1))
                unit = dist_match.group(2).lower()
                if unit in ('км', 'km'):
                    dist_val = val * 1000.0
                else:
                    dist_val = val
            
            # Remove the distance part from text to parse duration
            rem_text = text
            if dist_match:
                rem_text = text[:dist_match.start()] + ' ' + text[dist_match.end():]
                
            dur_val = parse_duration_string(rem_text)
            if dist_val is not None and dur_val is not None:
                return {"distance": dist_val, "duration": dur_val}

    elif exercise_type == ExerciseType.bodyweight:
        cleaned = re.sub(r'(?i)(раз|reps|повторений|повт)', '', text)
        parts = cleaned.strip().split()
        if len(parts) >= 1:
            try:
                return {"reps": int(parts[0])}
            except ValueError:
                pass

    elif exercise_type == ExerciseType.timed:
        dur_val = parse_duration_string(text)
        if dur_val is not None:
            return {"duration": dur_val}
            
    return {}

def format_duration(duration_sec: float) -> str:
    if duration_sec < 60:
        return f"{duration_sec:g} сек"
    elif duration_sec < 3600:
        mins = int(duration_sec // 60)
        secs = int(duration_sec % 60)
        if secs > 0:
            return f"{mins} мин {secs} сек"
        return f"{mins} мин"
    else:
        hours = int(duration_sec // 3600)
        rem = duration_sec % 3600
        mins = int(rem // 60)
        secs = int(rem % 60)
        parts = [f"{hours} ч"]
        if mins > 0:
            parts.append(f"{mins} мин")
        if secs > 0:
            parts.append(f"{secs} сек")
        return " ".join(parts)

def format_distance(distance_m: float) -> str:
    if distance_m < 1000:
        return f"{distance_m:g} м"
    else:
        km = distance_m / 1000.0
        return f"{km:g} км"

def format_set_text(s) -> str:
    """
    Formats a Set object into a clean Russian string:
    - reps + weight: '10 повторений, 50 кг'
    - distance + duration: '500 м, 45 сек' or '2.5 км, 12 мин 30 сек'
    - reps: '10 повторений'
    - duration: '45 сек'
    """
    if getattr(s, "reps", None) and getattr(s, "weight", None):
        return f"{s.reps} повторений, {s.weight:g} кг"
    elif getattr(s, "reps", None):
        return f"{s.reps} повторений"
    elif getattr(s, "distance", None) and getattr(s, "duration", None):
        return f"{format_distance(s.distance)}, {format_duration(s.duration)}"
    elif getattr(s, "duration", None):
        return format_duration(s.duration)
    elif getattr(s, "distance", None):
        return format_distance(s.distance)
    else:
        return "Пустой подход"
