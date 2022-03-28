# BloodRooster
Custom visualizations of bloodhound data using vis.js and sqlite


	 python3 main.py -s sqlite:////path/to/tmp/test.db dbinit
	 python3 main.py -s sqlite:////path/to/test.db import -z /path/to/bloodhound.zip
	 export SQLALCHEMY_DATABASE_URI=sqlite:////path/to/test.db
	 python3 webserver.py

from browser
http://127.0.0.1/graph
	hit submit 
	
SRC and DST dont do anything yet....submit just does path to DA
