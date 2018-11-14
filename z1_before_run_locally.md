<!-- 1. install virtual machine and run it -->
virtualenv venv
source venv/Scripts/activate

<!-- 2. install all required packages in venv -->
(venv) $ pip install -r requirements.txt

<!-- 3. link to database specified for develop  -->
contact me for DATABASE_URL

<!-- start with debug mode -->
python healthnote.py  

<!-- start with production mode, can send email -->
flask run

<!-- Before upload, delete all __pycache__ files with: -->
find . -type d -name __pycache__ -exec rm -r {} \+