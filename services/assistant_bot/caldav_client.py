import datetime
import os
import json
import logging
import caldav

logger = logging.getLogger("caldav_client")

def get_caldav_config():
    p = "/etc/openclaw/secrets.json"
    if os.path.exists(p):
        try:
            with open(p) as f:
                data = json.load(f)
                return data.get("caldav_url"), data.get("caldav_user"), data.get("caldav_password")
        except Exception:
            pass
    return None, None, None

def add_event_to_calendar(summary: str, dt_start: datetime.datetime, duration_minutes: int = 60, description: str = "") -> bool:
    url, user, password = get_caldav_config()
    if not url or not user or not password:
        logger.warning("CalDAV credentials not fully configured in /etc/openclaw/secrets.json")
        return False

    try:
        client = caldav.DAVClient(url=url, username=user, password=password)
        my_principal = client.principal()
        calendars = my_principal.calendars()
        if not calendars:
            return False
        
        target_cal = calendars[0]
        dt_end = dt_start + datetime.timedelta(minutes=duration_minutes)
        
        target_cal.save_event(
            dtstart=dt_start,
            dtend=dt_end,
            summary=summary,
            description=description
        )
        return True
    except Exception as e:
        logger.error(f"Error adding CalDAV event: {e}")
        return False
