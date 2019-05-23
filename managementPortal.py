from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for, jsonify
import os
from sqlalchemy.orm import sessionmaker
from identityManagement import *
engine = create_engine('sqlite:///identityManagement.db', echo=True)
import redis
import configparser
import datetime
import calendar
import re
import hashlib, uuid

app = Flask(__name__)

# CONFIG #
configfile = os.path.join(os.environ['AIL_BIN'], 'packages/config.cfg')
if not os.path.exists(configfile):
    raise Exception('Unable to find the configuration file. \
                    Did you set environment variables? \
                    Or activate the virtualenv.')

cfg = configparser.ConfigParser()
cfg.read(configfile)

# REDIS #
r_serv_term = redis.StrictRedis(
        host=cfg.get("ARDB_TermFreq", "host"),
        port=cfg.getint("ARDB_TermFreq", "port"),
        db=cfg.getint("ARDB_TermFreq", "db"),
        decode_responses=True)

r_serv_db = redis.StrictRedis(
    host=cfg.get("ARDB_DB", "host"),
    port=cfg.getint("ARDB_DB", "port"),
    db=cfg.getint("ARDB_DB", "db"),
    decode_responses=True)


bootstrap_label = ['primary', 'success', 'danger', 'warning', 'info']

# VARIABLES #
#tracked
TrackedTermsSet_Name = "TrackedSetTermSet"
TrackedTermsDate_Name = "TrackedTermDate"
#black
BlackListTermsDate_Name = "BlackListTermDate"
BlackListTermsSet_Name = "BlackListSetTermSet"
#regex
TrackedRegexSet_Name = "TrackedRegexSet"
TrackedRegexDate_Name = "TrackedRegexDate"
#set
TrackedSetSet_Name = "TrackedSetSet"
TrackedSetDate_Name = "TrackedSetDate"

# notifications enabled/disabled
# same value as in `bin/NotificationHelper.py`
TrackedTermsNotificationEnabled_Name = "TrackedNotifications"

# associated notification email addresses for a specific term`
# same value as in `bin/NotificationHelper.py`
# Keys will be e.g. TrackedNotificationEmails_<TERMNAME>
TrackedTermsNotificationEmailsPrefix_Name = "TrackedNotificationEmails_"
TrackedTermsNotificationTagsPrefix_Name = "TrackedNotificationTags_"
TrackedTermsCompanyPrefix_Name = "company_"

userCompanies = []
companyLimit = []
companiesTrackedTerms = {}

# FUNCTIONS #
def Term_getValueOverRange(word, startDate, num_day, per_paste=""):
    passed_days = 0
    oneDay = 60*60*24
    to_return = []
    curr_to_return = 0
    for timestamp in range(startDate, startDate - max(num_day)*oneDay, -oneDay):
        value = r_serv_term.hget(per_paste+str(timestamp), word)
        curr_to_return += int(value) if value is not None else 0
        for i in num_day:
            if passed_days == i-1:
                to_return.append(curr_to_return)
        passed_days += 1
    return to_return

def save_tag_to_auto_push(list_tag):
    for tag in set(list_tag):
        #limit tag length
        if len(tag) > 49:
            tag = tag[0:48]
        r_serv_db.sadd('list_export_tags', tag)


# ROUTES #
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return redirect(url_for('mgmtPortal_page'))

@app.route('/login', methods=['POST'])
def do_admin_login():
    global userName
    Session = sessionmaker(bind=engine)
    s = Session()

    POST_USERNAME = str(request.form['username'])
    POST_PASSWORD = str(request.form['password'])
    
    query = s.query(User).filter(User.username.in_([POST_USERNAME]))
    result = query.first()
    if result:
        #Get user's salt to validate password
        saltQuery = s.query(User).filter(User.username.in_([POST_USERNAME])).first()
        salt = saltQuery.salt
        hashed_password = hashlib.sha512((POST_PASSWORD + salt).encode('utf-8')).hexdigest()

        if (result.password == hashed_password):
            session['logged_in'] = True
            userName = result.username
    
            #Get user's companies
            for userCompany in s.query(UsersCompany).filter_by(userID=result.id):
                company = s.query(Company).filter_by(id=userCompany.companyID).first()
                userCompanies.append(company.companyName)
                companyLimit.append(company.termsLimit)
        else: #Wrong password
            flash('Wrong user or password')#Same message to prevent attacks
    else:
        flash('Wrong user or password')#Same message to prevent attacks
    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    userCompanies.clear()
    companyLimit.clear()
    companiesTrackedTerms.clear()
    return home()

@app.route("/mgmtPortal/", methods=['GET'])
def mgmtPortal_page():
    if not session.get('logged_in'):
        return render_template('login.html')
    per_paste_text = "per_paste_"
    per_paste = 1

    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())

    # Map tracking if notifications are enabled for a specific term
    notificationEnabledDict = {}

    # Maps a specific term to the associated email addresses
    notificationEMailTermMapping = {}
    notificationTagsTermMapping = {}

    # Maps a specific term to the associated company
    companyTermMapping = {}

    #Regex
    trackReg_list = []
    trackReg_list_values = []
    trackReg_list_num_of_paste = []
    for tracked_regex in r_serv_term.smembers(TrackedRegexSet_Name):
        #Show only terms of the user's companies
        userInCompany = False
        for company in userCompanies:
            termCompanies = r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + tracked_regex)
            if termCompanies:
                for termCompany in termCompanies:
                    if (company == termCompany):
                        userInCompany = true
        if (not userInCompany):
            continue

        notificationEMailTermMapping[tracked_regex] = r_serv_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + tracked_regex)
        notificationTagsTermMapping[tracked_regex] = r_serv_term.smembers(TrackedTermsNotificationTagsPrefix_Name + tracked_regex)
        companyTermMapping[tracked_regex] = r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + tracked_regex)

        if tracked_regex not in notificationEnabledDict:
            notificationEnabledDict[tracked_regex] = False

        trackReg_list.append(tracked_regex)
        value_range = Term_getValueOverRange(tracked_regex, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedRegexDate_Name, tracked_regex)

        set_paste_name = "regex_" + tracked_regex
        trackReg_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        trackReg_list_values.append(value_range)

        if tracked_regex in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
            notificationEnabledDict[tracked_regex] = True

    #Set
    trackSet_list = []
    trackSet_list_values = []
    trackSet_list_num_of_paste = []
    for tracked_set in r_serv_term.smembers(TrackedSetSet_Name):
        #Show only terms of the user's companies
        userInCompany = False
        for company in userCompanies:
            termCompanies = r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + tracked_set)
            if termCompanies:
                for termCompany in termCompanies:
                    if (company == termCompany):
                        userInCompany = true
        if (not userInCompany):
            continue

        tracked_set = tracked_set

        notificationEMailTermMapping[tracked_set] = r_serv_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + tracked_set)
        notificationTagsTermMapping[tracked_set] = r_serv_term.smembers(TrackedTermsNotificationTagsPrefix_Name + tracked_set)
        companyTermMapping[tracked_set] = r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + tracked_set)

        if tracked_set not in notificationEnabledDict:
            notificationEnabledDict[tracked_set] = False

        trackSet_list.append(tracked_set)
        value_range = Term_getValueOverRange(tracked_set, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedSetDate_Name, tracked_set)

        set_paste_name = "set_" + tracked_set
        trackSet_list_num_of_paste.append(r_serv_term.scard(set_paste_name))
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        trackSet_list_values.append(value_range)

        if tracked_set in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
            notificationEnabledDict[tracked_set] = True

    #Tracked terms
    track_list = []
    track_list_values = []
    track_list_num_of_paste = []
    for tracked_term in r_serv_term.smembers(TrackedTermsSet_Name):
        #Show only terms of the user's companies
        userInCompany = False
        for company in userCompanies:
            termCompanies = r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + tracked_term)
            if termCompanies:
                for termCompany in termCompanies:
                    if (company == termCompany):
                        userInCompany = true
        if (not userInCompany):
            continue

        notificationEMailTermMapping[tracked_term] = r_serv_term.smembers(TrackedTermsNotificationEmailsPrefix_Name + tracked_term)
        notificationTagsTermMapping[tracked_term] = r_serv_term.smembers(TrackedTermsNotificationTagsPrefix_Name + tracked_term)
        companyTermMapping[tracked_term] = r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + tracked_term)

        if tracked_term not in notificationEnabledDict:
            notificationEnabledDict[tracked_term] = False

        track_list.append(tracked_term)
        value_range = Term_getValueOverRange(tracked_term, today_timestamp, [1, 7, 31], per_paste=per_paste_text)

        term_date = r_serv_term.hget(TrackedTermsDate_Name, tracked_term)

        set_paste_name = "tracked_" + tracked_term

        track_list_num_of_paste.append( r_serv_term.scard(set_paste_name) )

        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        value_range.append(term_date)
        track_list_values.append(value_range)

        if tracked_term in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
            notificationEnabledDict[tracked_term] = True

    #blacklist terms
    black_list = []
    for blacked_term in r_serv_term.smembers(BlackListTermsSet_Name):
        term_date = r_serv_term.hget(BlackListTermsDate_Name, blacked_term)
        term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
        black_list.append([blacked_term, term_date])

    #Counting terms tracked by each company
    for term in companyTermMapping:
        for idx,userCompany in enumerate(userCompanies):
            for companyOfTerm in companyTermMapping[term]:
                if ( companyOfTerm == userCompany):
                    if not userCompany in companiesTrackedTerms:
                        companiesTrackedTerms[userCompany] = 1
                    else:
                        companiesTrackedTerms[userCompany] += 1

    #Initialize companiesTrackedTerms for companies without terms
    for userCompany in userCompanies:
        if not userCompany in companiesTrackedTerms:
            companiesTrackedTerms[userCompany] = 0

    return render_template("mgmtPortal.html",
            black_list=black_list, track_list=track_list, trackReg_list=trackReg_list, trackSet_list=trackSet_list,
            track_list_values=track_list_values, track_list_num_of_paste=track_list_num_of_paste,
            trackReg_list_values=trackReg_list_values, trackReg_list_num_of_paste=trackReg_list_num_of_paste,
            trackSet_list_values=trackSet_list_values, trackSet_list_num_of_paste=trackSet_list_num_of_paste,
            per_paste=per_paste, notificationEnabledDict=notificationEnabledDict, bootstrap_label=bootstrap_label, 
            notificationEMailTermMapping=notificationEMailTermMapping, notificationTagsTermMapping=notificationTagsTermMapping, companyTermMapping=companyTermMapping, userName=userName, userCompanies=userCompanies)

@app.route("/mgmtPortal_query_paste/")
def mgmtPortal_query_paste():
    term =  request.args.get('term')
    paste_info = []

    # check if regex or not
    if term.startswith('/') and term.endswith('/'):
        set_paste_name = "regex_" + term
        track_list_path = r_serv_term.smembers(set_paste_name)
    elif term.startswith('\\') and term.endswith('\\'):
        set_paste_name = "set_" + term
        track_list_path = r_serv_term.smembers(set_paste_name)
    else:
        set_paste_name = "tracked_" + term
        track_list_path = r_serv_term.smembers(set_paste_name)

    for path in track_list_path:
        paste = Paste.Paste(path)
        p_date = str(paste._get_p_date())
        p_date = p_date[0:4]+'/'+p_date[4:6]+'/'+p_date[6:8]
        p_source = paste.p_source
        p_encoding = paste._get_p_encoding()
        p_size = paste.p_size
        p_mime = paste.p_mime
        p_lineinfo = paste.get_lines_info()
        p_content = paste.get_p_content()
        if p_content != 0:
            p_content = p_content[0:400]
        paste_info.append({"path": path, "date": p_date, "source": p_source, "encoding": p_encoding, "size": p_size, "mime": p_mime, "lineinfo": p_lineinfo, "content": p_content})

    return jsonify(paste_info)


@app.route("/mgmtPortal_query/")
def mgmtPortal_query():
    TrackedTermsDate_Name = "TrackedTermDate"
    term =  request.args.get('term')
    section = request.args.get('section')

    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())
    value_range = Term_getValueOverRange(term, today_timestamp, [1, 7, 31])

    if section == "followTerm":
        term_date = r_serv_term.hget(TrackedTermsDate_Name, term)

    term_date = datetime.datetime.utcfromtimestamp(int(term_date)) if term_date is not None else "No date recorded"
    value_range.append(str(term_date))
    return jsonify(value_range)


@app.route("/mgmtPortal_action/", methods=['GET'])
def mgmtPortal_action():
    today = datetime.datetime.now()
    today = today.replace(microsecond=0)
    today_timestamp = calendar.timegm(today.timetuple())


    section = request.args.get('section')
    action = request.args.get('action')
    term =  request.args.get('term')
    notificationEmailsParam = request.args.get('emailAddresses')
    input_tags = request.args.get('tags')
    company = request.args.get('company')

    if action is None or term is None or notificationEmailsParam is None:
        return "None"
    else:
        if section == "followTerm":
            if action == "add":

                #company field is mandatory
                if not company:
                    return "None"

                #User has to belong to the company to be able to add a term
                userInCompany = False
                for companyOfUser in userCompanies:
                    if (company == companyOfUser):
                        userInCompany = true
                if (not userInCompany):
                    return "None" 

                #Check for tracked terms company limit
                for idx,userCompany in enumerate(userCompanies):
                    if (company == userCompany):
                        if (companiesTrackedTerms[company] >= companyLimit[idx]):
                            flash('Tracked terms limit.')
                            return "None"

                # Make a list of all passed email addresses
                notificationEmails = notificationEmailsParam.split()

                validNotificationEmails = []
                # check for valid email addresses
                for email in notificationEmails:
                    # Really basic validation:
                    # has exactly one @ sign, and at least one . in the part after the @
                    if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        validNotificationEmails.append(email)

                # create tags list
                list_tags = input_tags.split()

                # check if regex/set or simple term
                #regex
                if term.startswith('/') and term.endswith('/'):
                    r_serv_term.sadd(TrackedRegexSet_Name, term)
                    r_serv_term.hset(TrackedRegexDate_Name, term, today_timestamp)
                    # add all valid emails to the set
                    for email in validNotificationEmails:
                        r_serv_term.sadd(TrackedTermsNotificationEmailsPrefix_Name + term, email)
                    # enable notifications by default
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, term)
                    # add tags list
                    for tag in list_tags:
                        r_serv_term.sadd(TrackedTermsNotificationTagsPrefix_Name + term, tag)
                    save_tag_to_auto_push(list_tags)
                    # add company
                    r_serv_term.sadd(TrackedTermsCompanyPrefix_Name + term, company)


                #set
                elif term.startswith('\\') and term.endswith('\\'):
                    tab_term = term[1:-1]
                    perc_finder = re.compile("\[[0-9]{1,3}\]").search(tab_term)
                    if perc_finder is not None:
                        match_percent = perc_finder.group(0)[1:-1]
                        set_to_add = term
                    else:
                        match_percent = DEFAULT_MATCH_PERCENT
                        set_to_add = "\\" + tab_term[:-1] + ", [{}]]\\".format(match_percent)
                    r_serv_term.sadd(TrackedSetSet_Name, set_to_add)
                    r_serv_term.hset(TrackedSetDate_Name, set_to_add, today_timestamp)
                    # add all valid emails to the set
                    for email in validNotificationEmails:
                        r_serv_term.sadd(TrackedTermsNotificationEmailsPrefix_Name + set_to_add, email)
                    # enable notifications by default
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, set_to_add)
                    # add tags list
                    for tag in list_tags:
                        r_serv_term.sadd(TrackedTermsNotificationTagsPrefix_Name + set_to_add, tag)
                    save_tag_to_auto_push(list_tags)
                    # add company
                    r_serv_term.sadd(TrackedTermsCompanyPrefix_Name + term, company)

                #simple term
                else:
                    r_serv_term.sadd(TrackedTermsSet_Name, term.lower())
                    r_serv_term.hset(TrackedTermsDate_Name, term.lower(), today_timestamp)
                    # add all valid emails to the set
                    for email in validNotificationEmails:
                        r_serv_term.sadd(TrackedTermsNotificationEmailsPrefix_Name + term.lower(), email)
                    # enable notifications by default
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, term.lower())
                    # add tags list
                    for tag in list_tags:
                        r_serv_term.sadd(TrackedTermsNotificationTagsPrefix_Name + term.lower(), tag)
                    save_tag_to_auto_push(list_tags)
                    # add company
                    r_serv_term.sadd(TrackedTermsCompanyPrefix_Name + term, company)

            elif action == "toggleEMailNotification":
                # get the current state
                if term in r_serv_term.smembers(TrackedTermsNotificationEnabled_Name):
                    # remove it
                    r_serv_term.srem(TrackedTermsNotificationEnabled_Name, term.lower())
                else:
                    # add it
                    r_serv_term.sadd(TrackedTermsNotificationEnabled_Name, term.lower())

            #del action
            else:
                #delete the company
                for company in userCompanies:
                    r_serv_term.srem(TrackedTermsCompanyPrefix_Name + term, company)

                #delete term from DB only if no company is tracking it
                if not r_serv_term.smembers(TrackedTermsCompanyPrefix_Name + term):
                    if term.startswith('/') and term.endswith('/'):
                        r_serv_term.srem(TrackedRegexSet_Name, term)
                        r_serv_term.hdel(TrackedRegexDate_Name, term)
                    elif term.startswith('\\') and term.endswith('\\'):
                        r_serv_term.srem(TrackedSetSet_Name, term)
                        r_serv_term.hdel(TrackedSetDate_Name, term)
                    else:
                        r_serv_term.srem(TrackedTermsSet_Name, term.lower())
                        r_serv_term.hdel(TrackedTermsDate_Name, term.lower())

                    # delete the associated notification emails too
                    r_serv_term.delete(TrackedTermsNotificationEmailsPrefix_Name + term)
                    # delete the associated tags set
                    r_serv_term.delete(TrackedTermsNotificationTagsPrefix_Name + term)

        else:
            return "None"

        to_return = {}
        to_return["section"] = section
        to_return["action"] = action
        to_return["term"] = term
        return jsonify(to_return)

@app.route("/mgmtPortal/delete_terms_tags", methods=['POST'])
def delete_terms_tags():
    term = request.form.get('term')
    tags_to_delete = request.form.getlist('tags_to_delete')
    print(term,tags_to_delete)

    if term is not None and tags_to_delete is not None:
        for tag in tags_to_delete:
            r_serv_term.srem(TrackedTermsNotificationTagsPrefix_Name + term, tag)
        return redirect(url_for('mgmtPortal_page'))
    else:
        return 'None args', 400

@app.route("/mgmtPortal/delete_terms_email", methods=['GET'])
def delete_terms_email():
    term =  request.args.get('term')
    email =  request.args.get('email')

    if term is not None and email is not None:
        r_serv_term.srem(TrackedTermsNotificationEmailsPrefix_Name + term, email)
        return redirect(url_for('mgmtPortal_page'))
    else:
        return 'None args', 400


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
