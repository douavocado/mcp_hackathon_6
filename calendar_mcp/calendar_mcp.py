
from __future__ import print_function
import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build



import argparse
from pathlib import Path
from typing import List, Dict
import time 
import grpc
import calendar_pb2
import calendar_pb2_grpc
import os
from mcp.server.fastmcp import FastMCP

# channel = grpc.insecure_channel('localhost:5471')
# stub = calendar_pb2_grpc.CalendarServiceStub(channel)

def get_credentials():
    """Get Google Calendar API credentials."""
    creds = None

    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']    

    # Step 1: Load saved token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Step 2: If no (valid) credentials, start OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=5471)
            except Exception as e:
                print("Authentication failed:", e)
                return

        # Step 3: Save the credentials
        # with open('token.json', 'w') as token:
        #     token.write(creds.to_json())

    # Step 4: Use credentials to build Google Calendar service
    service = build('calendar', 'v3', credentials=creds)

    # Step 5: Test it – list next 10 events
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # UTC time
    return service


# Initialize the MCP server
mcp = FastMCP("CalendarMCP")


service = get_credentials()

parser = argparse.ArgumentParser(description="Calendar MCP Server")
# parser.add_argument("--storage-path", required=True, help="Path to store calendar events")
args, unknown = parser.parse_known_args()


@mcp.tool()
def get_calendar_events(max_results: int = 10) -> List[str]:
    """Get calendar events."""
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    results = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    return results.get('items', [])

@mcp.tool()
def search_calendar(query: str, max_results: int = 3) -> List[str]:
    """Search calendar and return events matching the query."""

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # UTC time    
    results = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime').execute()

    events = results.get('items', [])        
    filtered_events = [event for event in events if query.lower() in event['summary'].lower()]


    return [result for result in filtered_events]

@mcp.tool()
def search_calendar_and_write_to_file(file_path: str) -> str:
    """Write information to a file."""
    results = get_calendar_events()
    md_content = "# Calendar Events\n\n| Time | Description |\n| --- | --- |\n"
    for event in results:
        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'Unknown'))
        description = event.get('summary', 'No Title')
        md_content += f"| {start} | {description} |\n"
    results = md_content

    with open(file_path, 'w') as f:
        f.write(results)
    return f"Information written to {file_path}"


@mcp.tool()
def get_events_in_time(time_start: str, time_end: str) -> List[str]:
    """Get events in a specific time range."""
    results = service.events().list(
        calendarId='primary', timeMin=time_start,
        maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = results.get('items', [])    
    filtered_events = [event for event in events if event['start']['dateTime'] >= time_start and event['end']['dateTime'] <= time_end]
    return [result for result in filtered_events]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="calendar MCP Server")
    parser.add_argument("transport", choices=["stdio", "sse"], help="Transport mode")
    # parser.add_argument("--storage-path", required=True, help="Path to store papers")
    args = parser.parse_args()



    for i in range(1):
        print(search_calendar("Rowing", 5))
        print(get_events_in_time("2025-05-13T15:00:00+01:00", "2025-05-13T20:00:00+01:00"))
        # print(get_events_in_time("2025-05-13T15:00:00+01:00", "2025-05-13T20:00:00+01:00"))

        
    # mcp.run(transport=args.transport)
