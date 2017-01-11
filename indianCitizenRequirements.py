import wikipedia
from lxml import html
import requests
import urllib2
from bs4 import BeautifulSoup
import unicodedata
import string
import csv
import psycopg2
from psycopg2.extensions import AsIs

# Initiate object from Wikipedia using Wikipedia library
visa_page = wikipedia.page('Visa requirements for Indian citizens')

# URL for wikipedia site
url = "https://en.wikipedia.org/wiki/Visa_requirements_for_Indian_citizens"

# Instantiate page object
page = urllib2.urlopen(url).read()
soup = BeautifulSoup(page, "lxml")

# Create list of numbers from 0-999
numbers = range(0, 1000)

# Create list of bracketed objects to be removed later
chars_to_remove = []
for idx in numbers:
    chars_to_remove.append('[' + str(numbers[idx]) + ']')

# Instantiate empty list for country name, status, notes and list to be removed
name_list = []
status_list = []
notes_list = []
status_list_permit = ["oivr permit required", "access permit required", "travel permit required", "permission required", "entry permit required", "special permit required", "access permit required", "special permits required"]
status_list_permission = ["special permission required", "special authorisation required"]

# Create a list of objects that are printable
printable = set(string.printable)

# Cycle through table tags in html object
for tr in soup.find_all('tr'):
    tds = tr.find_all('td')
    if len(tds) == 3:
        # Convert from unicode object and remove all ASCII characters
        name_uni = tds[0].text.encode('utf-8')
        name = filter(lambda x: x in printable, name_uni)
        # Name Exceptions to restore that had ASCII stripped
        if name == "Cte d'Ivoire":
            name_list.append("Cote d'Ivoire")
        elif name == "So Tom and Prncipe":
            name_list.append("Sao Tome and Principe")
        elif name == "Runion":
            name_list.append("Reunion")
        else:
            name_list.append(name.strip())

        status_uni = tds[1].text.encode('utf-8')
        status = filter(lambda x: x in printable, status_uni)

        # Status Exceptions
        if status.lower() in status_list_permit:
            status_list.append("Permit required")
        elif status.lower() in status_list_permission:
            status_list.append("Special Authorization Required")
        elif "visa on arrival" in status.lower() and len(status.lower()) > 14:
            status_list.append("Visa on arrival")
        elif status.replace(".", "") == "Restricted zone" or status == "Restricted area":
            status_list.append("Restricted zone")
        else:
            status_list.append(status)

        # Notes Exceptions
        notes_uni = tds[2].text.encode('utf-8')
        notes = filter(lambda x: x in printable, notes_uni)
        notes.translate(None, ''.join(chars_to_remove))
        notes_list.append(notes)

# Remove extraneous values from all 3 lists
status_list = status_list[0: len(status_list)-41]
name_list = name_list[0: len(name_list)-41]
notes_list = notes_list[0: len(notes_list)-41]

table_dir = {'names': name_list, 'status': status_list, 'notes': notes_list}

# Remove any [xxx] blocks from status and notes where xxx represent 000 - 999 numbers
for dir in table_dir:
    for idx in range(0, len(name_list)):
        for number in chars_to_remove:
            if number in table_dir[dir][idx]:
                table_dir[dir][idx] = table_dir[dir][idx].replace(number, '').strip()

# Create Status and Notes directories
status_dir = {}
notes_dir = {}
country_flag = {}
country_non_UN = ["Abkhazia", "Macau", "Taiwan", "Gibraltar", "Belovezhskaya Pushcha National Park",
                  "Crimea", "Turkish Republic of Northern Cyprus", "UN Buffer Zone in Cyprus", "Nagorno-Karabakh Republic",
                  "Novorossiya", "South Ossetia", "Transnistria", "British Indian Ocean Territory",
                  "Eritrea outside Asmara", "Gorno-Badakhshan Autonomous Province", "Korean Demilitarised Zone",
                  "UNDOF Zone and Ghajar", "Ashmore and Cartier Islands", "Clipperton Island", "Lau Province",
                  "United States Minor Outlying Islands", "Antarctica", "South Georgia and the South Sandwich Islands"]

for country_name in name_list:
    indices = []
    note_val = []
    # Create Status directory
    status_dir[country_name] = status_list[name_list.index(country_name)]

    # Create Country Flag directory
    if country_name not in country_non_UN:
        country_flag[country_name] = "Country"
    else:
        country_flag[country_name] = "Disputed or Restricted Territories"

    # Concatenate Notes
    if name_list.count(country_name) > 1:
        indices = [i for i, x in enumerate(name_list) if x == country_name]
        for note_idx in range(0, len(indices)):
            note_val.append(notes_list[indices[note_idx]])
        if note_val[0] == "":
            notes_dir[country_name] = "".join(note_val)
        else:
            notes_dir[country_name] = " ".join(note_val)
    else:
        notes_dir[country_name] = notes_list[name_list.index(country_name)]

'''AT THIS POINT THE SCRIPT DIVERGES TO CHANGE VISA RULES BASED ON US GREEN CARD'''

# Create list of key word to check
usa_check = ["USA", "US", "United States", "U.S.A"]
visa_not_required = ["visa not required", "no visa required", "visa waived", "valid visa", "valid travel documents", "permanent"]
visa_not_required_pos = ["visa required", "except"]

# Update country status based on Visa rules
for country_name in notes_dir:
    if any(usa in notes_dir[country_name] for usa in usa_check):
        if any(visa in notes_dir[country_name].lower() for visa in visa_not_required):
            status_dir[country_name] = "Visa not required"
        elif all(visa_req in notes_dir[country_name].lower() for visa_req in visa_not_required_pos):
            status_dir[country_name] = "Visa not required"

# Manual Overrides for certain cases
status_dir["United States"] = "Home"
notes_dir["United States"] = "Permanent Resident (Green Card Holder)"
name_list.append("India")
status_list.append("Home")
notes_list.append("Indian Citizen")
country_flag["India"] = "Country"
status_dir["India"] = "Home"
notes_dir["India"] = "Indian Citizen"
status_dir["Malaysia"] = "Visa required"
notes_dir["Malaysia"] = "eVisa facilities only available for Indian Citizens residing in India"
status_dir["Gabon"] = "eVisa"
status_dir["Guam"] = "Visa not required"
status_dir["U.S. Virgin Islands"] = "Visa not required"
status_dir["Antarctica"] = "Permit required"
status_dir["Turkey"] = "eVisa"
status_dir["Taiwan"] = "eVisa"
status_dir["Cuba"] = "Visa on arrival"
status_dir["United Arab Emirates"] = "eVisa"

# Output and update a .csv file with all the data
'''OUTPUT A .CSV FILE CONTAINING DATA. UNCOMMENT BLOCK TO RUN'''

# with open('VisaRequirements.csv', 'w') as csv_file:
    # fieldnames = ['Country_Name', 'Visa_Requirements', 'Notes', 'Country_Flag']
    # writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    # writer.writeheader()
    # for country_name in name_list:
        # writer.writerow({'Country_Name': country_name, 'Visa_Requirements': status_dir[country_name], 'Notes': notes_dir[country_name],
                        #  'Country_Flag': country_flag[country_name]})

# print name_list
# print status_dir
# print notes_dir

'''CONNECT AND OUTPUT RESULTS TO A POSTGRES DATABASE HOSTED ON LOCAL SERVER'''

conn_string = "host='localhost' dbname='greencard' user='Adhaar'"

print "Connecting to database\n	->%s" % conn_string

conn = psycopg2.connect(conn_string)

print "Connected:\n"

insert_country_info = 'insert into country_info (country_id, country_name, country_status, country_flag, modified_date) Values ' \
         '(%s, %s, %s, %s, now() );'
insert_country_notes = 'insert into country_notes (country_id, country_notes) Values (%s, %s);'
cursor = conn.cursor()

sorted_country_name = sorted(status_dir.keys(), key=lambda x: x.lower())

for pk in range(0, len(sorted_country_name)):
    country_info_values = (pk+1, sorted_country_name[pk], status_dir[sorted_country_name[pk]], country_flag[sorted_country_name[pk]], )
    print country_info_values
    cursor.execute(insert_country_info, country_info_values)
    country_notes_values = (pk+1, notes_dir[sorted_country_name[pk]])
    print country_notes_values
    cursor.execute(insert_country_notes, country_notes_values)

conn.commit()
