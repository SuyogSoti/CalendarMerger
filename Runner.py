# cronjob to make it repeat every 123.615 seconds or 2:04 minutes

from __future__ import print_function
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import strict_rfc3339 as strict
import time
import datetime
import json

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
    home_dir = os.path.expanduser('~')
    myPath = os.path.join(home_dir, '.suyg-calender-merger')
    if not os.path.exists(myPath):
        os.makedirs(myPath)
    if not os.path.exists(os.path.join(myPath, "last-data-primary.txt")):
        os.system("touch "+os.path.join(myPath, "last-data-primary.txt"))
        open(os.path.join(myPath, "last-data-primary.txt"), 'w').close()
    if not os.path.exists(os.path.join(myPath, "last-data-secondary.txt")):
        os.system("touch "+os.path.join(myPath, "last-data-secondary.txt"))
        open(os.path.join(myPath, "last-data-secondary.txt"), 'w').close()
    PrimaryFile = open(os.path.join(myPath, "last-data-primary.txt"), 'r+')
    SecondaryFile = open(os.path.join(myPath, "last-data-secondary.txt"), 'r+')

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
    print(now)
    print('Getting the upcoming', number_of_events, 'events')

    primaryEventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=number_of_events, singleEvents=True,
        orderBy='startTime').execute()

    secondaryEventsResult = service.events().list(
        calendarId=secondarCalendarID, timeMin=now, maxResults=number_of_events, singleEvents=True,
        orderBy='startTime').execute()

    primaryCalendarEvents = primaryEventsResult.get('items', [])
    secondaryCalendarEvents = secondaryEventsResult.get('items', [])

    print("DELETING ALL DELETED EVENTS")
    listOfOld = []
    count = 1
    for line in PrimaryFile:
        try:
            oldData = json.loads(line)
            var = oldData['start']['dateTime']
            var = strict.rfc3339_to_timestamp(var)
        except Exception as e:
            print(e)
        if checkICal(oldData, primaryCalendarEvents) == None and var > time.time():
            i = checkICal(oldData, secondaryCalendarEvents)
            if i == None:
                pass
            else:
                try:
                    listOfOld.append(i)
                    print(i['start']['dateTime'], i['summary'])
                    print("\033[91m" + "something was deleted! in the secondary calendar")
                    service.events().delete(calendarId=secondarCalendarID, eventId=i['id']).execute()
                    replace_line(os.path.join(myPath, "last-data-primary.txt"), count, "{}\n")
                except Exception as e:
                    print(e)
        count = count + 1

    count = 1
    for line in SecondaryFile:
        try:
            oldData = json.loads(line)
            var = oldData['start']['dateTime']
            var = strict.rfc3339_to_timestamp(var)
        except Exception as e:
            print(e)
        if (var > time.time() and checkICal(oldData, secondaryCalendarEvents) == None and checkICal(oldData, listOfOld) is None):
            i = checkICal(oldData, primaryCalendarEvents)
            if i == None:
                pass
            else:
                try:
                    listOfOld.append(i)
                    print(i['start']['dateTime'], i['summary'])
                    print("\033[91m" + "something was deleted! in the primary calendar")
                    service.events().delete(calendarId="primary", eventId=i['id']).execute()
                    replace_line(os.path.join(myPath, "last-data-secondary.txt"), count, "{}\n")
                except Exception as e:
                    print(e)
        count = count + 1


    count = 1
    print("SYNCING ALL EVENTS")
    for event in primaryCalendarEvents:
        start = event['start']['dateTime']#.get('dateTime', event['start'].get('date'))
        print(count, start, event['summary'])
        if checkICal(event, secondaryCalendarEvents) is None and checkICal(event, listOfOld) is None:
            try:
                service.events().insert(calendarId=secondarCalendarID, body=generateEvent(event)).execute()
            except Exception as e:
                print("\033[91m" + "error of inserting into Secondary Calendar:", e)
                os.system('ntfy -t "Suyog\'s Calendar Program" send "There is a bug in the program! :( Please contact Suyog about this..."')
        count += 1
        PrimaryFile.write(json.dumps(event) + "\n")
    PrimaryFile.close()

    count = 1
    for e in secondaryCalendarEvents:
        start = e['start'].get('dateTime', e['start'].get('date'))
        print("Part 2:", count, start, e['summary'])
        if checkICal(e, primaryCalendarEvents) is None and checkICal(e, listOfOld) is None:
            try:
                service.events().insert(calendarId='primary', body=generateEvent(e)).execute()
            except Exception as e:
                print("\033[91m" + "error of inserting into Primary Calendar:", e)
                os.system('ntfy -t "Suyog\'s Calendar Program" send "There is a bug in the program! :( Please contact Suyog about this..."')
        count  += 1
        SecondaryFile.write(json.dumps(e) + "\n")
    SecondaryFile.close()



def checkICal(ical, calendar):
    # print(ical)
    for i in calendar:
        # print ("Ical: ", ical['iCalUID'], "i: ", i['iCalUID'])
        try:
            if (ical['summary'] == i['summary']
            and ical['start'].get('dateTime', ical['start'].get('date')) == i['start'].get('dateTime', i['start'].get('date'))
            and ical['end'].get('dateTime', ical['start'].get('date')) == i['end'].get('dateTime', i['start'].get('date'))):
                return i
        except Exception as e:
            print(e)

def generateEvent(event):
    return {
        'summary': event['summary'],
        'location': "Somewhere",
        'description': "I am just busy!",
        'start': {
            'dateTime': event['start'].get('dateTime', event['start'].get('date')),
        },
        'end': {
            'dateTime': event['end'].get('dateTime', event['start'].get('date')),
        },
        'reminders': event['reminders']
    }
def replace_line(file_name, line_num, text):
    lines = open(file_name, 'r').readlines()
    lines[line_num] = text
    out = open(file_name, 'w')
    out.writelines(lines)
    out.close()

if __name__ == '__main__':
    main()
    main()
