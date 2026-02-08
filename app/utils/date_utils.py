"""
Date parsing utilities for different data sources.
Centralizes date parsing logic to avoid duplication and ensure consistency.
"""
from datetime import datetime
from typing import Optional
import pytz
from app.utils.logger import get_logger

logger = get_logger(__name__)

ARGENTINA_TZ = pytz.timezone('America/Argentina/Buenos_Aires')


def parse_gestion_real_date(date_str: str) -> Optional[datetime]:
    """
    Parse date from Gestión Real CSV format: DD-MM-YYYY HH:MM:SS

    Args:
        date_str: Date string in DD-MM-YYYY HH:MM:SS format

    Returns:
        datetime object or None if parsing fails

    Examples:
        >>> parse_gestion_real_date("29-01-2026 23:11:30")
        datetime(2026, 1, 29, 23, 11, 30)
        >>> parse_gestion_real_date("invalid")
        None
    """
    if not date_str or not isinstance(date_str, str):
        return None

    try:
        date_str = date_str.strip()
        parts = date_str.split(' ')

        if len(parts) < 1:
            return None

        date_parts = parts[0].split('-')
        if len(date_parts) != 3:
            logger.warning(f"Invalid date format (expected DD-MM-YYYY): {date_str}")
            return None

        time_part = parts[1] if len(parts) > 1 else '00:00:00'

        day, month, year = date_parts[0], date_parts[1], date_parts[2]

        # Validate numeric components
        if not (day.isdigit() and month.isdigit() and year.isdigit()):
            logger.warning(f"Non-numeric date components: {date_str}")
            return None

        # Parse the date
        parsed_date = datetime.strptime(f'{year}-{month}-{day} {time_part}', '%Y-%m-%d %H:%M:%S')

        return parsed_date

    except (ValueError, IndexError) as e:
        logger.warning(f"Error parsing Gestión Real date '{date_str}': {e}")
        return None


def parse_splynx_date(date_str: str) -> Optional[datetime]:
    """
    Parse date from Splynx API format: YYYY-MM-DD HH:MM:SS

    Args:
        date_str: Date string in YYYY-MM-DD HH:MM:SS format

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None

    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        logger.warning(f"Error parsing Splynx date '{date_str}': {e}")
        return None


def ensure_argentina_tz(dt: datetime) -> datetime:
    """
    Ensure datetime has Argentina timezone.
    If naive, localizes to Argentina TZ.
    If aware, converts to Argentina TZ.

    Args:
        dt: datetime object (naive or aware)

    Returns:
        timezone-aware datetime in Argentina timezone
    """
    if dt.tzinfo is None:
        # Naive datetime - localize to Argentina
        return ARGENTINA_TZ.localize(dt)
    else:
        # Aware datetime - convert to Argentina
        return dt.astimezone(ARGENTINA_TZ)
