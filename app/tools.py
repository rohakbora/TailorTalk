from app.calender_utils import get_free_slots, book_event, list_upcoming_events
from datetime import datetime, timedelta
import re
from typing import List, Dict
from dateutil.parser import parse as parse_datetime
import logging
from datetime import datetime, time


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def tool_check_availability(start_date: str, end_date: str) -> str:
    """Check available slots between start_date and end_date (full day range assumed)."""
    try:
        logger.info(f"Checking availability: {start_date} to {end_date}")
        
        # Handle different date formats
        if 'T' in start_date:
            start = datetime.fromisoformat(start_date.replace('Z', ''))
        else:
            start = datetime.fromisoformat(start_date + "T00:00:00")
            
        if 'T' in end_date:
            end = datetime.fromisoformat(end_date.replace('Z', ''))
        else:
            end = datetime.fromisoformat(end_date + "T23:59:59")

        busy_slots = get_free_slots(start, end)

        if isinstance(busy_slots, str):
            return busy_slots

        if not busy_slots:
            return f"✅ You're fully available between {start_date} and {end_date}."

        busy_text = "🗓️ Here are your busy slots:\n" + "\n".join(
            [f"• {slot['start']} to {slot['end']}" for slot in busy_slots]
        )
        
        return busy_text
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return f"Error checking availability: {str(e)}"

def tool_book_slot(start_time: str, duration: str = "1h", title: str = "", description: str = "") -> str:
    """Book a calendar meeting using structured parameters."""
    try:
        logger.info(f"Booking slot: {start_time} for {duration}")
        
        # Parse start time - handle different formats
        if 'T' in start_time:
            start = datetime.fromisoformat(start_time.replace('Z', ''))
        else:
            # Try to parse as "YYYY-MM-DD HH:MM" format
            try:
                start = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            except ValueError:
                # Fallback to dateutil parser
                start = parse_datetime(start_time)

        # Parse duration
        hours = 1
        if duration.lower().endswith("h"):
            hours = float(duration[:-1])
        elif duration.lower().endswith("m"):
            hours = float(duration[:-1]) / 60
        elif duration.lower().endswith("min"):
            hours = float(duration[:-3]) / 60
        else:
            # Try to parse as just a number (assume hours)
            try:
                hours = float(duration)
            except ValueError:
                hours = 1

        end = start + timedelta(hours=hours)

        # Defaults if missing
        title = title or "TailorTalk Meeting"
        description = description or ""

        # Book the event
        result = book_event(title, start, end, description)
        return result

    except Exception as e:
        logger.error(f"Error booking slot: {str(e)}")
        return f"Error booking slot: {str(e)}"

def tool_list_events(start_date: str = None, end_date: str = None) -> list:
    """List upcoming events, optionally filtered by date range, returning structured data."""
    try:
        logger.info(f"Listing events: {start_date} to {end_date}")
        
        start = None
        end = None

        if start_date:
            if 'T' in start_date:
                start = datetime.fromisoformat(start_date.replace('Z', ''))
            else:
                dt = parse_datetime(start_date)
                if dt.time() == time(0, 0, 0):
                    dt = dt.replace(hour=0, minute=0, second=0)
                start = dt

        if end_date:
            if 'T' in end_date:
                end = datetime.fromisoformat(end_date.replace('Z', ''))
            else:
                dt = parse_datetime(end_date)
                if dt.time() == time(0, 0, 0):
                    dt = dt.replace(hour=23, minute=59, second=59)
                end = dt

        events = list_upcoming_events(start=start, end=end)
        print(events)
        if isinstance(events, str):
            return [{
                "summary": "Error",
                "date": "",
                "time": "",
                "description": events,
                "link": ""
            }]

        # Handle if no events
        if not events:
            return [{
                "summary": "No upcoming events",
                "date": "",
                "time": "",
                "description": (
                    "No upcoming events found in the given range."
                    if start_date or end_date
                    else "No upcoming events found."
                ),
                "link": ""
            }]

        # structured_events = []
        # for event in events:
        #     summary = event.get('summary', 'No Title')
        #     description = event.get('description', '')
        #     link = event.get('htmlLink', '')

        #     start_obj = event.get('start', {})
        #     end_obj = event.get('end', {})

        #     date_str = ''
        #     time_str = ''

        #     if 'dateTime' in start_obj:
        #         try:
        #             start_dt = datetime.fromisoformat(start_obj['dateTime'].replace('Z', '+00:00'))
        #             end_dt = datetime.fromisoformat(end_obj['dateTime'].replace('Z', '+00:00')) if 'dateTime' in end_obj else None

        #             date_str = start_dt.strftime('%Y-%m-%d')
        #             if end_dt:
        #                 time_str = f"{start_dt.strftime('%H:%M')} – {end_dt.strftime('%H:%M')}"
        #             else:
        #                 time_str = start_dt.strftime('%H:%M')
        #         except Exception as parse_err:
        #             logger.warning(f"Could not parse dateTime: {start_obj.get('dateTime')} due to {parse_err}")
        #             date_str = 'Unknown'
        #             time_str = ''
        #     elif 'date' in start_obj:
        #         date_str = start_obj['date']
        #         time_str = '(all day)'
        #     else:
        #         date_str = 'Unknown'
        #         time_str = ''


        #     structured_events.append({
        #         "summary": summary,
        #         "date": date_str,
        #         "time": time_str,
        #         "description": description,
        #         "link": link
        #     })

        # print(structured_events, "\n")
        return events

    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        return [{
            "summary": "Error",
            "date": "",
            "time": "",
            "description": f"Error listing events: {str(e)}",
            "link": ""
        }]


# Helper function to parse natural language time expressions
def parse_natural_time(time_expr: str, reference_time: datetime = None) -> datetime:
    """Parse natural language time expressions like 'tomorrow', 'next Monday', etc."""
    if reference_time is None:
        reference_time = datetime.now()
    
    time_expr = time_expr.lower().strip()
    
    # Today
    if time_expr in ['today', 'now']:
        return reference_time.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Tomorrow
    if time_expr == 'tomorrow':
        return (reference_time + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Yesterday
    if time_expr == 'yesterday':
        return (reference_time - timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # This week, next week patterns
    if 'week' in time_expr:
        days_ahead = 7 if 'next' in time_expr else 0
        return (reference_time + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # Weekday names
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }
    
    for day_name, day_num in weekdays.items():
        if day_name in time_expr:
            days_ahead = day_num - reference_time.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            if 'next' in time_expr:
                days_ahead += 7
            return (reference_time + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
    
    # If nothing matches, try dateutil parser
    try:
        return parse_datetime(time_expr)
    except:
        return reference_time