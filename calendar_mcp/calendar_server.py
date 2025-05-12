from concurrent import futures
import grpc
import calendar_pb2
import calendar_pb2_grpc
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token.json'  # Already authenticated user

def get_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    return build('calendar', 'v3', credentials=creds)

class CalendarService(calendar_pb2_grpc.CalendarServiceServicer):
    def CreateEvent(self, request, context):
        service = get_service()

        event = {
            'summary': request.summary,
            'start': {'dateTime': request.start_time, 'timeZone': 'UTC'},
            'end': {'dateTime': request.end_time, 'timeZone': 'UTC'},
        }

        created = service.events().insert(calendarId='primary', body=event).execute()
        return calendar_pb2.CreateEventResponse(event_id=created['id'], html_link=created['htmlLink'])

    def ListEvents(self, request, context):
        service = get_service()

        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId='primary', timeMin=now,
                                              maxResults=request.max_results or 5,
                                              singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        proto_events = []

        for e in events:
            start = e['start'].get('dateTime', e['start'].get('date'))
            end = e['end'].get('dateTime', e['end'].get('date'))
            proto_events.append(calendar_pb2.Event(summary=e.get('summary', ''),
                                                   start_time=start,
                                                   end_time=end))
        return calendar_pb2.ListEventsResponse(events=proto_events)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    calendar_pb2_grpc.add_CalendarServiceServicer_to_server(CalendarService(), server)
    server.add_insecure_port('[::]:5471')
    server.start()
    print("MCP Calendar Server is running on port 5471...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
