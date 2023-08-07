# Open Book
This is a project for AQA A-level Computer Science coursework. It is a website that provides all the users in the system with unique, personalised recommendations, and reading lists to allow them to store books that they have read, want to read, and are currently reading, as well as create collections of their own.  It aso provides each user with a reading diary, where they can record their thoughts and feelings about each book/part of the book they have read each day. Finally, users are able to leave revies for books, and then view these on about pages for the book.

## Setup
Having cloned this repo, to set up this repository, the following commands need to be executed in the Linux terminal/files need to be created.

### Web Server
Install the lighttpd web server.
> sudo apt install lighttpd

### Packages
Install Pip to make installing python packages simpler
> sudo apt install pip

Install mysql.connector so the backend can be used with the front end.
> pip install mysql.connector

### Database
#### Create the database server
Update all modules on the server
> sudo apt update\
> sudo apt upgrade

Install the database server, in this case MariaDB
> sudo apt install mariadb-server

Answer _y_ to all options for the most secure installation of the database. Remember any passwords that it requires for setup.
> sudo mysql_secure_installation

There will be a prompt for a password, which will be the same as what was entered previously.
> sudo mysql -u root -p

#### Create the project database
Create the database with name OpenBook. Remember the credentials used for the username, ip and password.
> CREATE DATABASE OpenBook;\
> CREATE USER "_username_"@"_database ip_" IDENTIFIED BY "_user password_";\
> GRANT ALL PRIVILEGES ON OpenBook.* TO "_username_"@"_database ip_";\
> FLUSH PRIVILEGES;\
> QUIT;

### Web server
Make the directory readable
> chmod a+r /path/to/project/

Make the fastcgi file executable
> chmod a+X /path/to/project/backend/flup.server.fcgi
