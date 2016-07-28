sudo pip install strict-rfc3339
sudo pip install nfty
touch ~/.suyg-calender-merger/last-data-primary.txt
touch ~/.suyg-calender-merger/last-data-secondary.txt
#cronttab -e
# */2 * * * * python Runner.py
