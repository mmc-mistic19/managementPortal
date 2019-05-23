#!/bin/bash

#Create virtual enviroment
virtualenv -p python3 managementPortal

#Configure AIL_BIN path to the AIL instance for redis connections
read -p "Introduce AIL installation path: " AILPath
echo "export AIL_BIN="$AILPath"/bin/" >> managementPortal/bin/activate

#Activate virtual enviroment
source managementPortal/bin/activate

#Install required modules
pip3 install -U -r requirements.txt

#Create database
python3 identityManagement.py

#Initialize database
python3 initializeDatabase.py
