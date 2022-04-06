# BloodRooster
Custom visualizations of Bloodhound data using flask, vis.js and sqlite

# Introduction
Have you ever thought to yourself, "Bloodhound is a pretty awesome tool, but why the fuck does it use Neo4j?"? Did you then have the thought, "Bloodhound works really well until it doesn't." BloodRooster is the result of trying to make an alternative network graph interface for Bloodhound data. It started as a modification of Jackdaw (an awesome take on the Active Directory data visulization toolbox). Jackdaw however has features that exceed requirements, and has dependencies that would require learning a bunch of new frameworks.

To summarize BloodRooster:
- imports Bloodhound ingestor data (v3 and v4) into a sqlite database
- uses Flask and Sqlalchemy for the core web application
- uses vis.js for network graph
- is memory conservative
- reasonably fast (after import)

## Install and Run
	python3 -m pip install -r requirements.txt
	python3 main.py -s sqlite:////path/to/tmp/test.db dbinit
	python3 main.py -s sqlite:////path/to/test.db import -z /path/to/bloodhound.zip
	export SQLALCHEMY_DATABASE_URI=sqlite:////path/to/test.db
	python3 webserver.py
	http://127.0.0.1:5000/
