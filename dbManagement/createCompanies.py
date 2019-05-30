import sqlite3
import os

#Database permissions to write
os.chmod('../identityManagement.db', 0o600)

#Request company name:
companyName = input ("Introduce company name: ")

#Request company terms limit
termsLimit = input ("Introduce company limit: ")


#Connect to database and insert values
conn = sqlite3.connect('../identityManagement.db')
c = conn.cursor()
c.execute("INSERT INTO companies(companyName,termsLimit) VALUES ('"+companyName+"','"+termsLimit+"')")
conn.commit()
c.close()

#restablish database permissions
os.chmod('../identityManagement.db', 0o400)
