pip install --upgrade google-api-python-client
pip install strict-rfc3339
pip install nfty
touch ~/.suyg-calender-merger/last-data-primary.txt
touch ~/.suyg-calender-merger/last-data-secondary.txt
#cronttab -e
# */2 * * * * python Runner.py
