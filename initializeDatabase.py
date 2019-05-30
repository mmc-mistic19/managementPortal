import sqlite3
import hashlib
import secrets

conn = sqlite3.connect('identityManagement.db')
c = conn.cursor()

#Trigger
c.execute("CREATE TRIGGER userAdminCompanies AFTER INSERT ON companies BEGIN INSERT INTO usersCompany(userID,companyID) VALUES ((SELECT id FROM users WHERE username = 'admin'),new.id);END;")

#Admin user: admin/password
salt = secrets.token_hex(8)
hashedPassword = hashlib.sha512(("password"+salt).encode('utf-8')).hexdigest()
c.execute("INSERT INTO users('username','password','salt') VALUES ('admin','"+hashedPassword+"','"+salt+"');")

#test company
c.execute("INSERT INTO companies('companyName','termsLimit') VALUES ('test-Company',15);")

conn.commit()
c.close()
