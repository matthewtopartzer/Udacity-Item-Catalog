
//// Requirements

Download links, follow the install instructions for each software.

[VirtualBox](https://www.virtualbox.org/wiki/Downloads)
[Vagrant](https://www.vagrantup.com/downloads)
[Python](http://www.python.org/)
[Flask](http://flask.pocoo.org/) 
[SQLAlchemy](http://www.sqlalchemy.org/)


//// Usage

With this project, you will have to go to the Google Developers Console, and create your own unique ID.


Run the application, via: $ python runserver.py

Then point your browser to: "localhost:5000"

//// Installation

1) Start the virtual machine

$ cd udacity-item catalog/vagrant
$ vagrant up

2) Connect to the virtual machine.
```
$ vagrant ssh
$ cd /vagrant/catalog

(Use "vagrant halt" to turn it off.)

3) Create the database.

$ python database_setup.py


4) Populate the database.

$ python populate_database.py

Use this link in the Google Dev Console to test the project. . .
(https://developers.google.com/identity/sign-in/web/devconsole-project)


