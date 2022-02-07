from __future__ import print_function

import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import fire
from dateutil import parser
import datetime
import random
import json
from typing import List

random.seed(42)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

#EVENT_FILTER="Test 1"
EVENT_FILTER="FLG meeting"

LOG_FILE_ATTENDEES="attendees.jsonl"
LOG_FILE_EVENTS="created_events.jsonl"

group_names = [
    "Bear",
    "Crocodile",
    "Deer",
    "Elephant",
    "Fox",
    "Giraffe",
    "Gorilla",
    "Hyena",
    "Jaguar",
    "Kangaroo",
    "Lion",
    "Monkey",
    "Panda",
    "Squirrel",
    "Tiger",
    "Wolf",
    "Yak",
    "Zebra"
]

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

class EventManager:
    def __init__(self, dateMin:str=None, limit:int=1):
        #read creds
        self.creds = self._read_creds()
        self.dateMin = dateMin
        self.limit = limit

    def _read_creds(self):
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds

    def _get_events(self):
        events = None
        try:
            service = build('calendar', 'v3', credentials=self.creds)

            # Call the Calendar API
            if not self.dateMin:
                target_day = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            else:
                target_day = parser.parse(self.dateMin).isoformat() + 'Z'
            print(f"Getting the upcoming {self.limit} events, using filter {EVENT_FILTER}, starting from {target_day}")
            events_result = service.events().list(calendarId='primary', timeMin=target_day,
                                                maxResults=self.limit, singleEvents=True,
                                                orderBy='startTime',
                                                q=EVENT_FILTER).execute()
            events = events_result.get('items', [])

        except HttpError as error:
            print('An error occurred: %s' % error)
        return events

    def _print_event(self, event):
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
        if "attendees" in event:
            for attendee in event['attendees']:
                print(attendee)

    def listevents(self):
        events = self._get_events()
        if not events:
            print('No upcoming events found.')
            return
            # Prints the start and name of the next 10 events
        for event in events:
            self._print_event(event)

    def _create_groups(self, event, n):
        attendees = [attendee['email'] for attendee in event['attendees'] if attendee['responseStatus'] == 'accepted']
        random.shuffle(attendees)
        groups = []
        for group_emails in chunks(attendees, n):
            if len(group_emails) == 1 and len(groups) != 0:
                groups[-1].append(group_emails[0])
            else:
                groups.append(group_emails)

        return groups

    def _create_event_for_group(self, orig_event, name, group:List[str]):
        start = orig_event['start'].get('dateTime', orig_event['start'].get('date'))
        start_dt = parser.parse(start) + datetime.timedelta(minutes=5)
        end_dt = parser.parse(start) + datetime.timedelta(minutes=50)
        attendees = [{'email':e} for e in group]
        event = {
            "calendarId": "primary",
            "conferenceDataVersion": 1,
            'summary': f'FLG subgroup {name}',
            'description': 'Subgroup for brainstorming algo tasks',
            'start': {
                'dateTime': start_dt.isoformat(),
            },
            'end': {
                'dateTime': end_dt.isoformat(),
            },
            'attendees': attendees, 
            'reminders': {
                'useDefault': False,
                'overrides': [
                {'method': 'email', 'minutes': 10},
                {'method': 'popup', 'minutes': 5},
                ],
            },
            "conferenceData": {
                "createRequest": {
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
                "requestId": f"{name}"
                }
            },
            "sendUpdates": "all"

        }

        try:
            service = build('calendar', 'v3', credentials=self.creds)

            event = service.events().insert(calendarId='primary', conferenceDataVersion=1, body=event).execute()
            print ('Event created: %s' % (event.get('htmlLink')))
            with open(LOG_FILE_EVENTS,"a") as f:
                f.write("{}\n".format(json.dumps(event)))

        except HttpError as error:
            print('An error occurred: %s' % error)


    def create_groups(self, n:int=3):
        events = self._get_events()
        if not events:
            print('No upcoming events found.')
            return
            # Prints the start and name of the next 10 events
        for event in events:
            #self._print_event(event)
            with open(LOG_FILE_ATTENDEES, "a") as f:
                f.write("{}\n".format(json.dumps(event['attendees'])))

            groups = self._create_groups(event, n)
            print(f"Created {len(groups)} groups for event {event['summary']} {event['start']}")

            random.shuffle(group_names)
            for name, group in zip(group_names, groups):
                self._create_event_for_group(event, name, group)




if __name__ == '__main__':
    fire.Fire(EventManager)