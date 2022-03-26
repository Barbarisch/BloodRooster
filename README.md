# BloodRooster
Custom visualizations of bloodhound data using vis.js and sqlite


python3 main.py -s sqlite:////home/user/Desktop/workspace/tmp/test.db dbinit
python3 main.py -s sqlite:////home/user/Desktop/workspace/tmp/test.db import -z /home/user/Desktop/workspace/stuff/internal_bloodhound/20220308093024_BloodHound.zip

export SQLALCHEMY_DATABASE_URI=sqlite:////home/user/Desktop/workspace/tmp/test.db
python3 webserver.py


from browser
http://127.0.0.1/graph
	hit submit 
	
SRC and DST dont do anything yet....submit just does path to DA
