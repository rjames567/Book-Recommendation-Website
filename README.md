# Open Book
This is a project for AQA A-level Computer Science coursework. It is a website that provides all the users in the system with unique, personalised recommendations, and reading lists to allow them to store books that they have read, want to read, and are currently reading, as well as create collections of their own.  It also provides each user with a reading diary, where they can record their thoughts and feelings about each book/part of the book they have read each day. Finally, users are able to leave revies for books, and then view these on about pages for the book.

## Setup
Having cloned this repo, to set up this repository, the following commands need to be executed in the Linux terminal/files need to be created.

### Web Server
Install the lighttpd web server.
> sudo apt install lighttpd

To start the webserver:
> sudo systemctl start lighttpd

To stop the webserver:
> sudo systemctl stop lighttpd

### Packages
Install Pip to make installing python packages simpler
> sudo apt install pip

Install python dependancies (where sudo as it needs to be accessed as root, as wsgi will run as root)
> sudo pip install mysql.connector\
> pip install mysql.connector\
> sudo pip install numpy\
> sudo pip install scikit-learn\
> sudo pip install sklearn\
> sudo pip install matplotlib

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

### Generate test data
This project uses test data from https://grouplens.org/datasets/book-genome/.

Download the ZIP file, and extract it to path/to/project/data/Original.

Note that some of the files are very large, and to reduce the size of these, the following command can be run to cut down
the file sizes using the following command. Size could be for example 200K, 1G, etc.
> truncate -s size filename.json

Change the maximum allowed packet temporarily in the database by entering the following commands.
> sudo mysql -u root -p\
> USE OpenBook;\
> SET GLOBAL max_allowed_packet=1073741824;\
> EXIT;\
> python3 path/to/project/backend/data_generation.py

The python file will take a long time to execute. On an i5-1135G7, it takes approximately 40 minutes to process and insert
the entire files into a database. It is also important to note that, as the number of files increases, the load on the
server will also increase. Running the script on a raspberry pi 4b took significantly longer, and had to be left to run
overnight - a more accurate time is unknown. When running with this quantitiy of data, it struggled handing more than one 
or two concurrent users, or many requests in a short space of time. This would cause lighttpd to lock up and not give any
responses from the FastCGI script. To fix this restart lighttpd.

Note that this will increase the maximum query size to 1GB for all database connections, which may be dangerous. This will
be reverted when the database is restarted. To do this enter the following command.
> sudo systemctl restart mariadb

### Configuration
Change the configuration file to configure the project. An example configuration is shown below
> mysql:\
> &nbsp;&nbsp;&nbsp;&nbsp;username str: wsgi\
> &nbsp;&nbsp;&nbsp;&nbsp;password str: 1qwerty7\
> &nbsp;&nbsp;&nbsp;&nbsp;schema str: OpenBook\
> &nbsp;&nbsp;&nbsp;&nbsp;host str: localhost\
> \
> passwords:\
> &nbsp;&nbsp;&nbsp;&nbsp;salt bin-str: +%E!mKZ(5%Z}k#pi(cPW!US8TU-J87\
> &nbsp;&nbsp;&nbsp;&nbsp;hashing_algorithm str: sha256\
> &nbsp;&nbsp;&nbsp;&nbsp;number_hash_passes int: 100000\
> \
> books:\
> &nbsp;&nbsp;&nbsp;&nbsp;genre_match_threshold float: 0.7\
> \
> home:\
> &nbsp;&nbsp;&nbsp;&nbsp;number_home_summaries int: 8\
> &nbsp;&nbsp;&nbsp;&nbsp;number_about_similarities int: 10\
> &nbsp;&nbsp;&nbsp;&nbsp;number_display_genres int: 8\
> \
> search:\
> &nbsp;&nbsp;&nbsp;&nbsp;number_results int: 50\
> \
> session_id_length int: 4\
> debugging bool: false


### Web server
Make the directory readable
> chmod a+r /path/to/project/

Make the fastcgi file executable
> chmod a+x /path/to/project/backend/flup.server.fcgi

### Scheduled tasks
Install cron to the server
> sudo apt-get install cron -y

Open the crontab file by running the command:
> sudo crontab -e

Modify the crontab file. Write the following commands to it. They run the scripts at 1:00 am, as it is
likely to have a low number of clients, so the impact should be minimal. However, to change this, change the timing clause of the cronjob - https://crontab.guru/ can make this easier.
> 0 1 * * * python3 /absolute/path/to/project/backend/maintenance.py

## Deleting project
To clear the crontab, run the command
> sudo crontab -r

Stop the webserver
> sudo systemctl stop lighttpd

To delete the database - Note that this is non-reversable
> DROP DATABASE OpenBook;

To delete the project files - Note that this is non-reversible
> rm -rf path/to/project

To delete the install packages
> sudo apt remove lighttpd\
> sudo pip uninstall mysql.connector\
> pip uninstall mysql.connector\
> sudo pip uninstall sklearn\
> sudo pip uninstall scikit-learn\
> sudo pip uninstall numpy\
> sudo apt remove mariadb-server
