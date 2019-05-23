import sqlite3

conn = sqlite3.connect('identityManagement.db')
c = conn.cursor()

#Trigger
c.execute("CREATE TRIGGER userAdminCompanies AFTER INSERT ON companies BEGIN INSERT INTO usersCompany(userID,companyID) VALUES ((SELECT id FROM users WHERE username = 'admin'),new.id);END;")

#Admin user: admin/password
c.execute("INSERT INTO users('username','password','salt') VALUES ('admin','2e1d3097cc94e78ce53779569ba2aceb80fadc4ca86fdc0e7196ebd7ee75c3e1969fd06649be9a25a447e91305e79c0f8e1abc78944bc98f2a4a83afa1eb3c21','KESSUPjYRcDKnZK7-muD');")

#test company
c.execute("INSERT INTO companies('companyName','termsLimit') VALUES ('test-Company',15);")

conn.commit()
c.close()
