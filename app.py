    ######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
import datetime
#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'SOnali7979'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''<style> body {   margin: 0;
    font-family: Arial;
  }
  
  .topnav {
    overflow: hidden;
    background-color:rgb(30, 112, 219);
  }
  
  .topnav a {
    float: left;
    color: #f2f2f2;
    text-align: center;
    padding: 15px 16px;
    text-decoration: none;
    font-size: 15px;
  }
  
  </style>
  <div class="topnav">
    <a class="active" href="/">Home</a>
    <a href="/album">View Albums</a>
    <a href="/upload">Upload Picture</a>
    <a href="/leaderboard">Leaderboard</a>
    <a href='/friends'> Find Friends</a>
    <a href='/searchbytag'> Search by Tags</a>
    <a href='/viewtag'> View Tags</a>
    <a href='/viewallfriends'> View All Friends</a>
    <a href='/searchbycomment'>Search by Comment</a>
    <a href='/recphoto'>Recommended Photos</a>
    <a href="/logout">Logout</a>
    <a href='/delete'> Delete your account</a>
  </div>
<br><br><br><center><h1> Please Sign In</h1>
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br></center>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')


def get_all_photos():
    cursor=conn.cursor()
    
    cursor.execute("SELECT DISTINCT Photos.photoid, imgdata, caption, likes FROM Photos")
    return cursor.fetchall()

@app.route("/register", methods=['POST'])
def register_user():
    try:
        firstname=request.form.get('firstname')
        lastname=request.form.get('lastname')
        email=request.form.get('email')
        date=request.form.get('birthdate')
        password=request.form.get('password')
    except:
        print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    hometown=request.form.get('hometown')
    gender=request.form.get('gender')
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        cursor.execute("SELECT userid FROM Users ORDER BY userid desc LIMIT 1")
        if cursor.rowcount==0:
            useid=1
        else:
            useid=cursor.fetchone()[0]+1
        print(cursor.execute("INSERT INTO Users (userid,firstname, lastname, email, birthdate, hometown, gender, contribution, password) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(useid,firstname, lastname, email, date, hometown, gender, 0, password)))
        conn.commit()
		#log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("ERROR: Duplicate Email")
    return """<center><h1> ERROR: EMAIL ALREADY EXISTS <br><a href='/register'>Try again</a>\
			<br><a href='/'>Go Back to Home</a></center>"""

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT photoid, imgdata, caption, likes FROM Photos WHERE userid = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getFriendsPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT photoid, data, caption, likes FROM Photos JOIN (SELECT userid2 FROM is_friends WHERE userid1='{0}') as t1 ON Photos.userid=t1.userid2").format(uid)
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]



def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT userid  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def delete_user(uid):
    cursor=conn.cursor()
    cursor.execute("DELETE FROM Users WHERE userid='{0}'".format(uid))

def delete_album(aid):
    cursor=conn.cursor()
    cursor.execute("DELETE FROM Albums WHERE albumid='{0}'".format(aid))
    
def delete_photo(pid):
    cursor=conn.cursor()
    cursor.execute("DELETE FROM Photos WHERE photoid='{0}'".format(pid))

def addFriend(userid1, userid2):
    cursor=conn.cursor()
    cursor.execute("INSERT INTO is_friends (userid1, userid2) VALUES ('{0}','{1}')".format(userid1, userid2))
    cursor.execute("INSERT INTO is_friends (userid1, userid2) VALUES ('{0}','{1}')".format(userid2, userid1))

def addAlbum(aid, uid, albumname, creationdate):
    cursor=conn.cursor()
    cursor.execute("INSERT INTO Albums (albumid, name, creationdate, userid) VALUES ('{0}','{1}','{2}','{3}')".format(aid, albumname, creationdate, uid ))

def leaderboard():
    cursor=conn.cursor()
    cursor.execute("SELECT userid, firstname, lastname, contribution FROM users ORDER BY contribution DESC LIMIT 10")
    return cursor.fetchall()

def get_photos_from_album(album):
    cursor=conn.cursor()
    cursor.execute("SELECT Photos.photoid, Photos.imgdata, Photos.caption from Photos Where Photos.albumid='{0}'".format(album))
    return cursor.fetchall()

def get_albums_from_user(uid):
    cursor=conn.cursor()
    cursor.execute("SELECT albumid, name FROM Albums WHERE userid='{0}'".format(uid))
    return cursor.fetchall()

def view_all_photos_by_tag(tag):
    cursor=conn.cursor()
    cursor.execute("SELECT Photos.photoid, data FROM Photos JOIN TAGGED ON Photos.photoid=TAGGED.photoid WHERE Tagged.keyword='{0}'".format(tag))
    return cursor.fetchall()

def view_all_your_photos_by_tag(uid, tag):
    cursor=conn.cursor()
    cursor.execute("SELECT Photos.photoid, data FROM Photos JOIN TAGGED ON Photos.photoid=TAGGED.photoid WHERE Tagged.keyword='{0}' AND Photos.userid='{1}'".format(tag,uid))
    return cursor.fetchall()

def leaderboard_for_tags():
    cursor=conn.cursor()
    cursor.execute("""SELECT Tags.keyword, Tags.count FROM Tags JOIN (SELECT keyword, count
                   FROM tags
                   GROUP BY count
                   ORDER BY count DESC LIMIT 3) as t1
                    ON t1.count=Tags.count
                    ORDER BY Tags.count DESC""")
    return cursor.fetchall()

def unique_album_for_user(uid, albumname):
    cursor=conn.cursor()
    if cursor.execute("SELECT albumid, name FROM albums WHERE userid='{0}' AND name='{1}'".format(uid,albumname)):
        return False
    else:
        return True
def friends_of_friends(uid):
    
    cursor=conn.cursor()
    cursor.execute("""
    SELECT users.userid, users.firstname, users.lastname, users.hometown, users.gender
    FROM users JOIN (SELECT a2.userid2 as uid, COUNT(a2.userid2) as count
    FROM is_friends as a1 JOIN is_friends as a2
    ON a1.userid2=a2.userid1 
    WHERE a1.userid1<>a2.userid2 AND a1.userid1='{0}'
    GROUP BY a2.userid2
    ORDER BY COUNT(a2.userid2) DESC
    ) as t2
    ON users.userid=t2.uid 
    WHERE Users.userid NOT IN (SELECT userid2 FROM is_friends WHERE userid1='{0}')
    ORDER BY t2.count DESC""".format(uid))
    return cursor.fetchall()
    

def youmayalsolike5(uid):
    cursor=conn.cursor()
    cursor.execute("""
    SELECT Tagged.photoid, t3.imdata, t3.liked, t3.cap, COUNT(Tagged.photoid)
    FROM Tagged JOIN (SELECT Photos.photoid as pid, Photos.imgdata as imdata, Photos.likes as liked, Photos.caption as cap, COUNT(Photos.photoid) as counter
    FROM Photos JOIN (
    SELECT *
    FROM Tagged JOIN (SELECT Tagged.keyword as tagg, COUNT(Tagged.keyword) as counts
    FROM Photos JOIN Tagged
    ON Photos.photoid=Tagged.photoid
    WHERE Photos.userid='{0}'
    GROUP BY Tagged.keyword 
    ORDER BY counts DESC LIMIT 5) as t1
    ON Tagged.keyword=t1.tagg ) as t2
    ON Photos.photoid=t2.photoid
    WHERE Photos.userid<>'{0}'
    GROUP BY Photos.photoid
    ORDER BY COUNT(Photos.Photoid) DESC) as t3
    ON Tagged.photoid=t3.pid
    WHERE t3.counter=5
    GROUP BY Tagged.photoid
    ORDER BY COUNT(Tagged.photoid)""".format(uid))
    return cursor.fetchall()

def youmayalsolike4(uid):
    cursor=conn.cursor()
    cursor.execute("""
    SELECT Tagged.photoid, t3.imdata, t3.liked, t3.cap, COUNT(Tagged.photoid)
    FROM Tagged JOIN (SELECT Photos.photoid as pid, Photos.imgdata as imdata, Photos.likes as liked, Photos.caption as cap, COUNT(Photos.photoid) as counter
    FROM Photos JOIN (
    SELECT *
    FROM Tagged JOIN (SELECT Tagged.keyword as tagg, COUNT(Tagged.keyword) as counts
    FROM Photos JOIN Tagged
    ON Photos.photoid=Tagged.photoid
    WHERE Photos.userid='{0}'
    GROUP BY Tagged.keyword 
    ORDER BY counts DESC LIMIT 5) as t1
    ON Tagged.keyword=t1.tagg ) as t2
    ON Photos.photoid=t2.photoid
    WHERE Photos.userid<>'{0}'
    GROUP BY Photos.photoid
    ORDER BY COUNT(Photos.Photoid) DESC) as t3
    ON Tagged.photoid=t3.pid
    WHERE t3.counter=4
    GROUP BY Tagged.photoid
    ORDER BY COUNT(Tagged.photoid)""".format(uid))
    return cursor.fetchall()
def youmayalsolike3(uid):
    cursor=conn.cursor()
    cursor.execute("""
    SELECT Tagged.photoid, t3.imdata, t3.liked, t3.cap, COUNT(Tagged.photoid)
    FROM Tagged JOIN (SELECT Photos.photoid as pid, Photos.imgdata as imdata, Photos.likes as liked, Photos.caption as cap, COUNT(Photos.photoid) as counter
    FROM Photos JOIN (
    SELECT *
    FROM Tagged JOIN (SELECT Tagged.keyword as tagg, COUNT(Tagged.keyword) as counts
    FROM Photos JOIN Tagged
    ON Photos.photoid=Tagged.photoid
    WHERE Photos.userid='{0}'
    GROUP BY Tagged.keyword 
    ORDER BY counts DESC LIMIT 5) as t1
    ON Tagged.keyword=t1.tagg ) as t2
    ON Photos.photoid=t2.photoid
    WHERE Photos.userid<>'{0}'
    GROUP BY Photos.photoid
    ORDER BY COUNT(Photos.Photoid) DESC) as t3
    ON Tagged.photoid=t3.pid
    WHERE t3.counter=3
    GROUP BY Tagged.photoid
    ORDER BY COUNT(Tagged.photoid)""".format(uid))
    return cursor.fetchall()
def youmayalsolike2(uid):
    cursor=conn.cursor()
    cursor.execute("""
    SELECT Tagged.photoid, t3.imdata, t3.liked, t3.cap, COUNT(Tagged.photoid)
    FROM Tagged JOIN (SELECT Photos.photoid as pid, Photos.imgdata as imdata, Photos.likes as liked, Photos.caption as cap, COUNT(Photos.photoid) as counter
    FROM Photos JOIN (
    SELECT *
    FROM Tagged JOIN (SELECT Tagged.keyword as tagg, COUNT(Tagged.keyword) as counts
    FROM Photos JOIN Tagged
    ON Photos.photoid=Tagged.photoid
    WHERE Photos.userid='{0}'
    GROUP BY Tagged.keyword 
    ORDER BY counts DESC LIMIT 5) as t1
    ON Tagged.keyword=t1.tagg ) as t2
    ON Photos.photoid=t2.photoid
    WHERE Photos.userid<>'{0}'
    GROUP BY Photos.photoid
    ORDER BY COUNT(Photos.Photoid) DESC) as t3
    ON Tagged.photoid=t3.pid
    WHERE t3.counter=2
    GROUP BY Tagged.photoid
    ORDER BY COUNT(Tagged.photoid)""".format(uid))
    return cursor.fetchall()
def youmayalsolike1(uid):
    cursor=conn.cursor()
    cursor.execute("""
    SELECT Tagged.photoid, t3.imdata, t3.liked, t3.cap, COUNT(Tagged.photoid)
    FROM Tagged JOIN (SELECT Photos.photoid as pid, Photos.imgdata as imdata, Photos.likes as liked, Photos.caption as cap, COUNT(Photos.photoid) as counter
    FROM Photos JOIN (
    SELECT *
    FROM Tagged JOIN (SELECT Tagged.keyword as tagg, COUNT(Tagged.keyword) as counts
    FROM Photos JOIN Tagged
    ON Photos.photoid=Tagged.photoid
    WHERE Photos.userid='{0}'
    GROUP BY Tagged.keyword 
    ORDER BY counts DESC LIMIT 5) as t1
    ON Tagged.keyword=t1.tagg ) as t2
    ON Photos.photoid=t2.photoid
    WHERE Photos.userid<>'{0}'
    GROUP BY Photos.photoid
    ORDER BY COUNT(Photos.Photoid) DESC) as t3
    ON Tagged.photoid=t3.pid
    WHERE t3.counter=1
    GROUP BY Tagged.photoid
    ORDER BY COUNT(Tagged.photoid)""".format(uid))
    return cursor.fetchall()

def youmayalsolike(uid):
    a=youmayalsolike5(uid)+youmayalsolike4(uid)+youmayalsolike3(uid)+youmayalsolike2(uid)+youmayalsolike1(uid)
    return a

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code



@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    cursor = conn.cursor()
    if request.method == 'POST':
        cursor.execute("SELECT photoid FROM Photos ORDER BY photoid desc LIMIT 1")
        if cursor.rowcount==0:
            photoid=1
        else:
            photoid=cursor.fetchone()[0]+1
        uid = getUserIdFromEmail(flask_login.current_user.id)
        albumname=request.form.get('albumname')
        albumsid=cursor.execute("""
        SELECT albumid
        FROM Albums
        WHERE name='{0}' AND Albums.userid='{1}'""".format(albumname,uid))
        albumsid=cursor.fetchone()
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        tagss=request.form.get('tags')
        photo_data =imgfile.read()   
        test=unique_album_for_user(uid, albumname)
        if (test==False):
            cursor.execute('''INSERT INTO Photos (photoid,caption,imgdata,likes,albumid,userid) VALUES (%s, %s, %s,%s,%s,%s )''' ,(photoid, caption, photo_data, 0, albumsid, uid ))
            conn.commit()
            tagss=tagss.split()
            
            for tag in tagss:
                cursor.execute('''
                INSERT Into Tagged
                (keyword, photoid) 
                VALUES('{0}','{1}')'''.format(tag,photoid))
                conn.commit()           
        else:
            print("Put valid albumname")
            return flask.redirect(flask.url_for('upload_file'))
        return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
    else:
        return render_template('upload.html')       

@app.route('/album', methods=['GET'])
@flask_login.login_required
def albums():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('albums.html', name=flask_login.current_user.id, albums=get_albums_from_user(uid))
    

@app.route('/createalbum', methods=['POST', 'GET'])
@flask_login.login_required
def create_album():
    if request.method=='GET' :
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('createalbum.html')
    else:
        cursor=conn.cursor()
        cursor.execute("SELECT albumid FROM Albums ORDER BY albumid desc LIMIT 1")
        if cursor.rowcount==0:
            albumid=1
        else:
            albumid=cursor.fetchone()[0]+1
        uid = getUserIdFromEmail(flask_login.current_user.id)
        albumname=request.form.get('albumname')
        test=unique_album_for_user(uid, albumname)
        creationdate=datetime.datetime.now()
        if test:    
            print(cursor.execute("INSERT INTO Albums (albumid, name, creationdate, userid) VALUES (%s,%s,%s,%s)",(albumid,albumname,creationdate,uid)))
            conn.commit()
        else:
            print("Unique albumname is needed within the same individual")
            return render_template('createalbum.html')
        return render_template('albums.html', name=flask_login.current_user.id, albums=get_albums_from_user(uid))
    
@app.route('/delete', methods=['GET'])
@flask_login.login_required
def delete_account():
    cursor=conn.cursor()
    uid=getUserIdFromEmail(flask_login.current_user.id)
    cursor.execute("DELETE FROM Users WHERE userid='{0}'".format(uid))
    conn.commit()
    flask_login.logout_user()
    return render_template('hello.html', message='Successfully Deleted Account')
    
    
@app.route('/leaderboard', methods=['GET'])
def Leaderboard():
    topten=leaderboard()
    return render_template('leaderboard.html',leaders=topten)

@app.route('/friends', methods=['GET','POST'])
@flask_login.login_required
def find_friends():
    uid=getUserIdFromEmail(flask_login.current_user.id)
    friend_of_friend=friends_of_friends(uid)
    if request.method=='GET':
        return render_template('friends.html', recs=friend_of_friend)
    else:
        cursor=conn.cursor()  
        firstname=request.form.get("firstname")
        lastname=request.form.get("lastname")
        hometown=request.form.get("hometown")
        if len(hometown)==0:
            cursor.execute("SELECT userid, firstname, lastname, hometown, gender FROM Users WHERE firstname='{0}' AND lastname='{1}' AND userid<>'{2}'".format(firstname, lastname,uid))
            searchresults=cursor.fetchall()
        else:
            cursor.execute("SELECT userid, firstname, lastname, hometown, gender FROM Users WHERE firstname='{0}' AND lastname='{1}' AND hometown='{2}' AND userid<>'{3}' UNION SELECT userid, firstname, lastname, hometown, gender FROM Users WHERE firstname='{0}' AND lastname='{1}' AND hometown is NULL AND userid<>'{3}'".format(firstname, lastname,hometown,uid))
            searchresults=cursor.fetchall() 
        return render_template('friends.html', searches=searchresults, recs=friend_of_friend)

@app.route('/viewphotos', methods=['GET','POST'])
@flask_login.login_required
def viewphoto():
    aid=request.args.get('albumid')
    photo=get_photos_from_album(aid)
    if request.method=="GET":
        photo=get_photos_from_album(aid)
        return render_template('viewphoto.html', photos=photo, base64=base64)
    else:
        answer=request.form.get("switch")
        cursor.execute("DELETE FROM Albums WHERE albumid='{0}'".format(aid))
        conn.commit()
        return render_template("hello.html", message="Successfully Deleted Album")
        
#end photo uploading code

@app.route('/viewcomment', methods=['GET','POST'])
def viewcomment():
    cursor=conn.cursor()
    pid=request.args.get('photoid')
    cursor.execute("SELECT photoid, imgdata FROM Photos WHERE photoid='{0}'".format(pid))
    photo=cursor.fetchone()
    if request.method=="GET":
        cursor.execute("SELECT Comments.commentid, Comments.text, Users.firstname, Users.lastname FROM Comments LEFT JOIN Users ON Comments.userid=Users.userid WHERE Comments.photoid='{0}'".format(pid))
        comment=cursor.fetchall()
        return render_template('viewcomments.html', comments=comment, photos=photo, base64=base64)
    else:
        commenttext=request.form.get("writecomment")
        cursor.execute("SELECT commentid FROM Comments ORDER BY commentid desc LIMIT 1")
        if cursor.rowcount==0:
            commentid=1
        else:
            commentid=cursor.fetchone()[0]+1
        if (flask_login.current_user.is_authenticated):    
            uid = getUserIdFromEmail(flask_login.current_user.id)
            date=datetime.datetime.now()
            cursor.execute("SELECT userid FROM Photos WHERE Photos.photoid='{0}'".format(pid))
            owner=int(cursor.fetchone()[0])        
            if owner==uid:
                cursor.execute("SELECT Comments.commentid, Comments.text, Users.firstname, Users.lastname FROM Comments LEFT JOIN Users ON Comments.userid=Users.userid WHERE Comments.photoid='{0}'".format(pid))
                comment=cursor.fetchall()
                return render_template('viewcomments.html', comments=comment, photos=photo, base64=base64, message="User can't comment on his own photo")
            cursor.execute("INSERT INTO Comments (commentid, text, userid, date, photoid) VALUES ('{0}','{1}','{2}','{3}','{4}')".format(commentid, commenttext, uid, date, pid))
            cursor.execute("SELECT Comments.commentid, Comments.text, Users.firstname, Users.lastname FROM Comments LEFT JOIN Users ON Comments.userid=Users.userid WHERE Comments.photoid='{0}'".format(pid))
            comment=cursor.fetchall()
            conn.commit()
            return render_template('viewcomments.html', comments=comment, photos=photo, base64=base64, message="Succesfully Added Comment")
        date=datetime.datetime.now()
        cursor.execute("INSERT INTO Comments (commentid, text, date, photoid) VALUES ('{0}','{1}','{2}','{3}')".format(commentid, commenttext, date, pid))
        cursor.execute("SELECT Comments.commentid, Comments.text, Users.firstname, Users.lastname FROM Comments LEFT JOIN Users ON Comments.userid=Users.userid WHERE Comments.photoid='{0}'".format(pid))
        comment=cursor.fetchall()
        conn.commit()
        return render_template('viewcomments.html', comments=comment, photos=photo, base64=base64, message="Succesfully Added Comment")

@app.route('/searchbytag', methods=['GET','POST'])
def searchbytag():
    leader=leaderboard_for_tags()
    if request.method=="GET":
        return render_template('searchbytag.html', poptags=leader)
    else:
        cursor=conn.cursor()
        tags=request.form.get("searchtag")
        tag=tags.split()
        cursor.execute("""SELECT Photos.photoid, Photos.imgdata, Photos.likes, Photos.caption
                       FROM Photos JOIN (SELECT photoid, count(photoid) as count
                        FROM Tagged
                        WHERE keyword IN ({0})
                        GROUP BY photoid) as t1
                       ON Photos.photoid=t1.photoid
                       WHERE t1.count='{1}'""".format(str(tag)[1:-1],len(tag)))
        searchresult=cursor.fetchall()
        return render_template('searchbytag.html', searches=searchresult, base64=base64, poptags=leader)
    
@app.route('/viewtag', methods=['GET','POST'])
@flask_login.login_required
def viewtag():
    if request.method=="GET":
        return render_template('viewyourtag.html')
    else:
        option=request.form.get("switch")
        cursor=conn.cursor()
        uid=getUserIdFromEmail(flask_login.current_user.id)
        if option=="View my Tags":
            cursor.execute("SELECT DISTINCT keyword FROM Tagged JOIN Photos WHERE Tagged.photoid=Photos.photoid AND Photos.userid='{0}'".format(uid))
            search=cursor.fetchall()
            return render_template("viewyourtag.html",searches=search, option=1)
            
        else:
            cursor.execute("SELECT keyword FROM Tags")
            search=cursor.fetchall()
        return render_template("viewyourtag.html",searches=search, option=2)

@app.route('/addorremove', methods=['GET','POST'])
@flask_login.login_required
def addorremove():
    frienduid=request.args.get("userid")
    uid=getUserIdFromEmail(flask_login.current_user.id)
    cursor=conn.cursor()
    cursor.execute("SELECT userid1 FROM is_friends WHERE userid1='{0}' AND userid2='{1}'".format(uid,frienduid))
    a=cursor.fetchall()
    cursor.execute("SELECT firstname, lastname FROM users WHERE userid='{0}'".format(frienduid))
    friendname=cursor.fetchone()
    if len(a)==0:
        msg="Are you sure you want to add "+friendname[0]+" "+friendname[1]+" as a friend?"
        formmsg="Add Friend"
    else:
        msg="Are you sure you want to remove "+friendname[0]+" "+friendname[1]+" as a friend?"
        formmsg="Remove Friend"
    if request.method=="GET":
        return render_template("addorremovefriend.html", message=msg, formmessage=formmsg)
    else:
        newmsg=request.form.get("switch")
        if formmsg=="Add Friend":
            cursor.execute("INSERT INTO is_friends (userid1,userid2) VALUES ('{0}','{1}')".format(uid,frienduid))
            cursor.execute("INSERT INTO is_friends (userid1,userid2) VALUES ('{0}','{1}')".format(frienduid,uid))
            conn.commit()
        else:
            cursor.execute("DELETE FROM is_friends WHERE userid1='{0}' AND userid2='{1}'".format(uid,frienduid))
            cursor.execute("DELETE FROM is_friends WHERE userid1='{0}' AND userid2='{1}'".format(frienduid,uid))
            conn.commit()

    return  render_template('hello.html')  


@app.route('/viewallfriends', methods=['GET'])
@flask_login.login_required
def viewallfriends():
    uid=getUserIdFromEmail(flask_login.current_user.id)
    cursor=conn.cursor()
    cursor.execute("SELECT Users.userid, firstname, lastname, hometown, gender FROM is_friends JOIN Users ON is_friends.userid2=Users.userid WHERE is_friends.userid1='{0}'".format(uid))
    friends=cursor.fetchall()
    return render_template("viewallfriends.html", searches=friends)


@app.route('/likepicture', methods=['GET','POST'])
@flask_login.login_required
def likepic():
    photoid=request.args.get("photoid")
    uid=getUserIdFromEmail(flask_login.current_user.id)
    cursor=conn.cursor()
    cursor.execute("SELECT Users.userid, firstname, lastname FROM Liked_Photo JOIN Users ON Users.userid=Liked_Photo.userid WHERE photoid='{0}'".format(photoid))
    likedusers=cursor.fetchall()
    cursor.execute("SELECT userid FROM liked_photo WHERE photoid='{0}' AND userid='{1}'".format(photoid,uid))
    wasliked=cursor.fetchall()
    cursor.execute("SELECT photoid, imgdata, likes FROM Photos WHERE photoid='{0}'".format(photoid))
    photodata=cursor.fetchone()
    if len(wasliked)==0:
        msg="Like"
    else:
        msg="Unlike"
    if request.method=="GET":
        return render_template('likepicture.html',photos=photodata, likeusers=likedusers, formmessage=msg, base64=base64)
    else:
        if msg=="Like":
            cursor.execute("INSERT INTO Liked_Photo (userid, photoid) VALUES ('{0}','{1}')".format(uid,photoid))
            conn.commit()
        else:
            cursor.execute("DELETE FROM Liked_Photo WHERE userid='{0}' AND photoid='{1}'".format(uid,photoid))
            cursor.execute(" UPDATE Photos SET likes=likes-1 WHERE photoid='{0}'".format(photoid))
            conn.commit()
        return render_template("hello.html", message="Successfully "+str(msg)+"d Photo")    



@app.route('/tagsforphoto', methods=['GET'])
def viewtagphoto():
    photoid=request.args.get("photoid")
    cursor=conn.cursor()
    cursor.execute("SELECT keyword FROM Tagged WHERE photoid='{0}'".format(photoid))
    tags=cursor.fetchall()
    cursor.execute("SELECT photoid, imgdata, likes FROM Photos WHERE photoid='{0}'".format(photoid))
    photodata=cursor.fetchone()
    return render_template('viewtagphoto.html',photos=photodata, tags=tags, base64=base64)
    
@app.route('/tagforphoto', methods=['GET'])
def viewallphototag():
    keyword=request.args.get("keyword")
    option=int(request.args.get("option"))
    cursor=conn.cursor()
    if option==1:
        uid=getUserIdFromEmail(flask_login.current_user.id)
        cursor.execute("SELECT Photos.photoid as p1, imgdata, caption, likes, keyword FROM Photos JOIN Tagged ON Photos.photoid=Tagged.photoid WHERE keyword='{0}' AND userid='{1}'".format(keyword,uid))
        photos=cursor.fetchall()
        return render_template('viewallphotosfortag.html', photos=photos, base64=base64, keyword=keyword, msg="your")
    else:
        cursor.execute("SELECT Photos.photoid as p1, imgdata, caption, likes, keyword FROM Photos JOIN Tagged ON Photos.photoid=Tagged.photoid WHERE keyword='{0}'".format(keyword))
        photos=cursor.fetchall()
        return render_template('viewallphotosfortag.html', photos=photos, base64=base64, keyword=keyword, msg="all")


@app.route('/searchbycomment', methods=['GET', 'POST'])
def searchoncomment():
    if request.method=='GET':
        return render_template("searchbycomment.html")
    else:
        commenttext=request.form.get("commenttext")
        cursor=conn.cursor()
        cursor.execute("""SELECT Users.userid, firstname, lastname, hometown, gender, t1.count, t1.text, t1.count
                   FROM Users JOIN (SELECT userid, text, COUNT(userid) as count
                    FROM Comments 
                    WHERE text='{0}'
                    GROUP BY userid
                    ORDER BY COUNT(userid) DESC) as t1
                   ON Users.userid=t1.userid
                   ORDER BY t1.count DESC""".format(commenttext))
        userwithcomment=cursor.fetchall()
        return render_template("searchbycomment.html", users=userwithcomment)
    

@app.route('/recphoto', methods=['GET'])
@flask_login.login_required  
def recphoto():
    uid=getUserIdFromEmail(flask_login.current_user.id)
    recphotos=youmayalsolike(uid)
    return render_template("recpics.html", photos=recphotos, base64=base64)

    
@app.route('/deletepicture', methods=['GET','POST'])
@flask_login.login_required
def delphoto():
    pid=request.args.get("photoid")
    cursor=conn.cursor()
    cursor.execute("SELECT photoid, imgdata, caption, likes FROM Photos WHERE photoid='{0}'".format(pid))
    photos=cursor.fetchone()
    if request.method=="GET":
        return render_template("deletephoto.html",photos=photos, base64=base64)
    else:
        delphoto=request.form.get("delete")
        if delphoto=="YES":
            cursor.execute("DELETE FROM Photos WHERE photoid='{0}'".format(pid))
            conn.commit()
            return render_template("hello.html", message="Successfully Deleted Photo")
        else:
            return render_template("hello.html",message="Successfully deleted Photo")

#default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html',photos=get_all_photos(),base64=base64)


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
