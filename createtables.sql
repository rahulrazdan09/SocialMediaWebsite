CREATE DATABASE IF NOT EXISTS photoshare;
SET SQL_SAFE_UPDATES = 0;
USE photoshare;




CREATE TABLE IF NOT EXISTS Users
	(userid INTEGER NOT NULL , 
    firstname CHAR(50) NOT NULL,
	lastname CHAR(50) NOT NULL,
	email VARCHAR(100) UNIQUE,
	birthdate DATE,
	hometown CHAR(50),
	contribution INTEGER,
	gender  CHAR(1),
	password VARCHAR(50) NOT NULL,	
	PRIMARY KEY (userid));

CREATE TABLE IF NOT EXISTS Albums
	(albumid INTEGER ,
	name CHAR(50),
	creationdate DATE,
    userid INTEGER NOT NULL,
	PRIMARY KEY (albumid),
    FOREIGN KEY (userid)
		REFERENCES Users(userid));

CREATE TABLE IF NOT EXISTS Photos
	(photoid INTEGER,
	caption VARCHAR(100),
	imgdata LONGBLOB,
	likes INTEGER,
    albumid INTEGER NOT NULL,
    userid INTEGER NOT NULL,
	PRIMARY KEY (photoid),
    FOREIGN KEY (albumid)
		REFERENCES Albums(albumid),
	FOREIGN KEY (userid)
		REFERENCES Users(userid));

CREATE TABLE IF NOT EXISTS Tags
	(keyword CHAR(30),
	count INTEGER,
	PRIMARY KEY (keyword));

CREATE TABLE IF NOT EXISTS Comments
	(commentid INTEGER,
	text VARCHAR(150),
	userid INTEGER,
	date DATE,
	photoid INTEGER NOT NULL,
	PRIMARY KEY (commentid),
	FOREIGN KEY (userid)
		REFERENCES Users (userid),
	FOREIGN KEY (photoid)
		REFERENCES Photos (photoid));

CREATE TABLE IF NOT EXISTS Is_Friends
	(userid1 INTEGER,
 	userid2 INTEGER,
	PRIMARY KEY(userid1, userid2),
	FOREIGN KEY(userid1)
		REFERENCES Users(userid),
	FOREIGN KEY(userid2)
		REFERENCES Users(userid),
	CHECK (userid1 <> userid2));
CREATE TABLE IF NOT EXISTS Tagged
	(keyword CHAR(30),
	 photoid INTEGER NOT NULL,
	 PRIMARY KEY (keyword, photoid),
	 FOREIGN KEY(keyword)
		REFERENCES Tags(keyword),
	 FOREIGN KEY(photoid)
		REFERENCES Photos(photoid));
CREATE TABLE IF NOT EXISTS Liked_Photo
	(userid INTEGER,
	 photoid INTEGER,
	PRIMARY KEY (userid, photoid),
	FOREIGN KEY(userid)
		REFERENCES Users(userid),
	FOREIGN KEY(photoid)
		REFERENCES Photos(photoid));

DROP TRIGGER IF EXISTS on_del_user;
DROP TRIGGER IF EXISTS on_del_album; 
DROP TRIGGER IF EXISTS on_del_photo_comments;
DROP TRIGGER IF EXISTS on_del_user_comments; 
DROP TRIGGER IF EXISTS LIKES_ON_PHOTO;
DROP TRIGGER IF EXISTS NEW_LIKES; 
DROP TRIGGER IF EXISTS UPD_COLLAB_SCORE1;
DROP TRIGGER IF EXISTS UPD_COLLAB_SCORE2;
DROP TRIGGER IF EXISTS DELETE_TAGS_FROM_RELATION;
DROP TRIGGER IF EXISTS UPDATE_TAGS;
DROP TRIGGER IF EXISTS friendship;
DROP TRIGGER IF EXISTS likes_on_user_delete;
DROP TRIGGER IF EXISTS is_friends_same_user;
DROP TRIGGER IF EXISTS UPDATE_TAGS_INS;
DROP TRIGGER IF EXISTS subtract_likes;

CREATE TRIGGER on_del_user BEFORE DELETE on Users
FOR EACH ROW
DELETE FROM Albums
WHERE Albums.userid=old.userid;

CREATE TRIGGER on_del_album BEFORE DELETE ON albums
FOR EACH ROW
DELETE FROM Photos
WHERE Photos.albumid=old.albumid;

CREATE TRIGGER on_del_photo_comments BEFORE DELETE ON photos
FOR EACH ROW
DELETE FROM Comments
WHERE old.photoid=Comments.photoid;

CREATE TRIGGER on_del_user_comments BEFORE DELETE ON Users
FOR EACH ROW
DELETE FROM Comments
WHERE old.userid=Comments.userid;

CREATE TRIGGER LIKES_ON_PHOTO BEFORE DELETE ON Photos
FOR EACH ROW
DELETE FROM Liked_Photo
WHERE Liked_Photo.photoid=old.photoid;

CREATE TRIGGER NEW_LIKES AFTER INSERT ON Liked_Photo
FOR EACH ROW
UPDATE Photos
SET
Photos.likes=Photos.likes+1
WHERE new.photoid=Photos.photoid;

CREATE TRIGGER UPD_COLLAB_SCORE1 AFTER INSERT ON Comments
FOR EACH ROW
UPDATE Users
SET
Users.contribution=Users.contribution+1
WHERE new.userid=Users.userid;

CREATE TRIGGER UPD_COLLAB_SCORE2 AFTER INSERT ON photos
FOR EACH ROW
UPDATE users
SET
Users.contribution=Users.contribution+1
WHERE Users.userid=new.userid;

CREATE TRIGGER DELETE_TAGS_FROM_RELATION BEFORE DELETE ON Photos
FOR EACH ROW
DELETE FROM Tagged
WHERE old.photoid=Tagged.photoid;

CREATE TRIGGER UPDATE_TAGS AFTER DELETE ON Tagged
FOR EACH ROW
UPDATE Tags
SET
Tags.count=Tags.count-1
WHERE Tags.keyword=old.keyword;

DELIMITER $$
CREATE TRIGGER UPDATE_TAGS_INS BEFORE INSERT ON Tagged
FOR EACH ROW BEGIN
IF (EXISTS (SELECT keyword FROM Tags WHERE Tags.keyword=new.keyword))
THEN UPDATE Tags SET Tags.count=Tags.count+1
WHERE Tags.keyword=new.keyword;
else
INSERT INTO Tags (keyword,count) VALUES (new.keyword,1);
END IF;
END$$
DELIMITER ;

CREATE TRIGGER friendship BEFORE DELETE ON Users
FOR EACH ROW
DELETE FROM is_friends
WHERE old.userid=is_friends.userid1 OR old.userid=is_friends.userid2;

CREATE TRIGGER likes_on_user_delete BEFORE DELETE ON Users
FOR EACH ROW
DELETE FROM liked_photo
WHERE liked_photo.userid=old.userid;




SELECT *
FROM COMMENTS
