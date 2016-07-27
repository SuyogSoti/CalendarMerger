# cronjob to make it repeat every 800 seconds or 15 minutes


from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'CalendarMerger'


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   CLIENT_SECRET_FILE)

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():

    # print("Added the events from the eventText!")
    # eventText = "lunch with andy tomorrow at 10 am"
    # test = service.events().quickAdd(calendarId='primary', text=eventText, sendNotifications=True).execute()
    # print ("The event added: '", eventText, "'.")


    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    number_of_events = 200

    secondarCalendarID = ""
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            if calendar_list_entry['summary'] == 'test':
                secondarCalendarID = calendar_list_entry['id']
            page_token = calendar_list.get('nextPageToken')
        if not page_token:
                break

    print(secondarCalendarID)

    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print('Getting the upcoming', number_of_events, 'events')

    primaryEventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=number_of_events, singleEvents=True,
        orderBy='startTime').execute()

    secondaryEventsResult = service.events().list(
        calendarId=secondarCalendarID, timeMin=now, maxResults=number_of_events, singleEvents=True,
        orderBy='startTime').execute()

    primaryCalendarEvents = primaryEventsResult.get('items', [])
    secondaryCalendarEvents = secondaryEventsResult.get('items', [])


    count = 1
    for event in primaryCalendarEvents:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(count, start, event['summary'])
        if not checkICal(event, secondaryCalendarEvents):
            service.events().insert(calendarId=secondarCalendarID, body=generateEvent(event)).execute()
            # pass
        count  += 1

    count = 1
    for e in secondaryCalendarEvents:
        start = e['start'].get('dateTime', e['start'].get('date'))
        print("Part 2:", count, start, e['summary'])
        if not checkICal(e, primaryCalendarEvents):
            service.events().insert(calendarId='primary', body=generateEvent(e)).execute()
            # pass
        count  += 1




def checkICal(ical, calendar):
    for i in calendar:
        # print ("Ical: ", ical['iCalUID'], "i: ", i['iCalUID'])
        if ical['iCalUID'] == i['iCalUID']:
            return True
    return False

def generateEvent(ev):
    event  = ev
    event['id'] = ''
    return event



if __name__ == '__main__':
    main()
