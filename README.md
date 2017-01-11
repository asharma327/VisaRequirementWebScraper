# VisaRequirementWebScraper
Web Scraper and Database pusher for Visa Requirements of Indian Citizens. 

Python file that will scrape a Wikipedia table of "Visa Requirements of [country]". The current script is modified to scrape the Visa Requirements for Indian Citizens.

On line 16 of the script, change:
url = "https://en.wikipedia.org/wiki/Visa_requirements_for_Indian_citizens"
to the page and table you want to scrape

The script also contains data cleansing lines such as removing unicode and standardizing certain Visa rules.

After halfway through the script, it becomes relevant only to Indian Citizens holding US Green Cards as it updates the necessary visa rules.

In the final section, you can export the table in either a .csv format or in a PostGres database

NOTE: you must create your own PostGres database first and specify the connection details in line 180 of the script
