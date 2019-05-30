import sqlite3
import os

#Database permissions to write
os.chmod('../identityManagement.db', 0o600)

#Request user name:
username = input ("Introduce user name: ")

#Request company name:
companyName = input ("Introduce company name: ")

#Connect to database and insert values
conn = sqlite3.connect('../identityManagement.db')
c = conn.cursor()
c.execute("INSERT INTO usersCompany(userID,companyID) SELECT users.id,companies.id from users,companies where username ='"+username+"' and companyName='"+companyName+"'")
conn.commit()
c.close()

#restablish database permissions
os.chmod('../identityManagement.db', 0o400)
