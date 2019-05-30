import sqlite3
import hashlib
import secrets
import getpass
import os

#Database permissions to write
os.chmod('../identityManagement.db', 0o600)

#Generate random salt
salt = secrets.token_hex(8)

#Request user name:
user = input ("Introduce user name: ")

#Request user password
password = getpass.getpass("Introduce password: ")

#Calculate password hash
hashedPassword = hashlib.sha512((password+salt).encode('utf-8')).hexdigest()

#Connect to database and insert values
conn = sqlite3.connect('../identityManagement.db')
c = conn.cursor()
c.execute("INSERT INTO users(username,password,salt) VALUES ('"+user+"','"+hashedPassword+"','"+salt+"')")
conn.commit()
c.close()

#restablish database permissions
os.chmod('../identityManagement.db', 0o400)
