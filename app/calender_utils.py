from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from dateutil import tz
import logging
from dateutil.parser import parse

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TAILORTALK_CALENDAR_ID = os.getenv("TAILORTALK_CALENDAR_ID")  # <-- use shared calendar

def get_credentials():
    """Create credentials from environment variables"""
    try:
        token_data = {
            'token': None,
            'refresh_token': os.getenv('GOOGLE_REFRESH_TOKEN'),
            'id_token': None,
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'scopes': SCOPES
        }
        
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        # Refresh token if needed
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            
        return creds
    except Exception as e:
        logger.error(f"Error creating credentials: {str(e)}")
        raise

def get_calendar_service():
    """Get Google Calendar service"""
    try:
        creds = get_credentials()
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error creating calendar service: {str(e)}")
        raise

def get_free_slots(start_time, end_time):
    """Get free time slots from the shared calendar"""
    try:
        service = get_calendar_service()
        
        # Convert to UTC if needed
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=tz.gettz('Asia/Kolkata'))
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=tz.gettz('Asia/Kolkata'))
            
        body = {
            "timeMin": start_time.astimezone(tz.UTC).isoformat().replace('+00:00', 'Z'),
            "timeMax": end_time.astimezone(tz.UTC).isoformat().replace('+00:00', 'Z'),
            "items": [{"id": TAILORTALK_CALENDAR_ID}]
        }
        
        logger.info(f"Checking availability from {start_time} to {end_time}")
        events = service.freebusy().query(body=body).execute()
        busy_times = events["calendars"][TAILORTALK_CALENDAR_ID].get("busy", [])
        
        # Format busy times for better readability
        formatted_busy = []
        for busy_slot in busy_times:
            start_dt = datetime.fromisoformat(busy_slot['start'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(busy_slot['end'].replace('Z', '+00:00'))
            
            # Convert to local time
            local_start = start_dt.astimezone(tz.gettz('Asia/Kolkata'))
            local_end = end_dt.astimezone(tz.gettz('Asia/Kolkata'))
            
            formatted_busy.append({
                'start': local_start.strftime('%Y-%m-%d %H:%M'),
                'end': local_end.strftime('%Y-%m-%d %H:%M')
            })
            
        return formatted_busy
        
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return f"Error checking availability: {str(e)}"

def book_event(summary=None, start_time=None, end_time=None, description=None):
    """Book an event in the shared calendar unless it overlaps with existing ones"""
    try:
        service = get_calendar_service()

        # Fallbacks
        summary = summary or "TailorTalk Meeting"
        description = description or ""

        # Ensure timezone info
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=tz.gettz('Asia/Kolkata'))
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=tz.gettz('Asia/Kolkata'))

        # Check for overlap
        time_min = start_time.astimezone(tz.UTC).isoformat().replace('+00:00', 'Z')
        time_max = end_time.astimezone(tz.UTC).isoformat().replace('+00:00', 'Z')

        logger.info(f"Checking for overlaps: {time_min} to {time_max}")
        
        overlapping_events = service.events().list(
            calendarId=TAILORTALK_CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])

        if overlapping_events:
            first = overlapping_events[0]
            title = first.get('summary', 'Unnamed Event')
            start_str = first['start'].get('dateTime', first['start'].get('date', 'Unknown time'))
            return f"⚠️ Overlap detected: '{title}' already exists at {start_str}. Please choose a different time."

        # Create event
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Asia/Kolkata'
            }
        }

        logger.info(f"Creating event: {summary} at {start_time}")
        created_event = service.events().insert(
            calendarId=TAILORTALK_CALENDAR_ID,
            body=event
        ).execute()

        return f"✅ Meeting '{summary}' booked from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')} on {start_time.strftime('%Y-%m-%d')}.\n📎 Event Link: {created_event.get('htmlLink')}"
        
    except Exception as e:
        logger.error(f"Error booking event: {str(e)}")
        return f"Error booking event: {str(e)}"

from datetime import datetime
from dateutil import tz
import logging

logger = logging.getLogger(__name__)

def list_upcoming_events(start=None, end=None):
    """List upcoming events from the shared calendar, including start and end time"""
    try:
        service = get_calendar_service()
        now = datetime.now(tz.gettz('Asia/Kolkata'))

        # Use current time if no start specified
        if start is None:
            start = now
        elif start.tzinfo is None:
            start = start.replace(tzinfo=tz.gettz('Asia/Kolkata'))

        time_min = start.astimezone(tz.UTC).isoformat().replace('+00:00', 'Z')
        time_max = None

        if end:
            if end.tzinfo is None:
                end = end.replace(tzinfo=tz.gettz('Asia/Kolkata'))
            time_max = end.astimezone(tz.UTC).isoformat().replace('+00:00', 'Z')

        query = {
            'timeMin': time_min,
            'singleEvents': True,
            'orderBy': 'startTime',
            'maxResults': 20,
        }
        if time_max:
            query['timeMax'] = time_max

        logger.info(f"Listing events from {time_min} to {time_max or 'end of time'}")

        events_result = service.events().list(
            calendarId=TAILORTALK_CALENDAR_ID,
            **query
        ).execute()

        events = events_result.get('items', [])

        # Format each event with both start and end times
        formatted_events = []
        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            end_str = event['end'].get('dateTime', event['end'].get('date'))

            # Parse and format both start and end
            if 'T' in start_str:
                start_dt = parse(start_str).astimezone(tz.gettz('Asia/Kolkata'))
                end_dt = parse(end_str).astimezone(tz.gettz('Asia/Kolkata'))
                time_range = f"{start_dt.strftime('%H:%M')} – {end_dt.strftime('%H:%M')}"
                date_display = start_dt.strftime('%Y-%m-%d')
            else:
                time_range = "All-day"
                date_display = start_str

            formatted_events.append({
                'summary': event.get('summary', 'No Title'),
                'date': date_display,
                'time': time_range,
                'description': event.get('description', ''),
                'htmlLink': event.get('htmlLink', '')
            })
            # print("formatted_event: ", formatted_events)
        return formatted_events

    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        return f"Error listing events: {str(e)}"

# Add missing import for Request
try:
    from google.auth.transport.requests import Request
except ImportError:
    logger.warning("google.auth.transport.requests not available")
    pass