import sqlite3

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
