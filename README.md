## Getting started
This version is designed to run with Python 3.

1. Clone the repository:

	```
	git clone https://github.com/st-tu-dresden/INLOOP.git
	cd tud_praktomat_neu
	```

2. PIL requires the following dependencies *on your system*:
	```
	sudo apt-get install python-dev
	sudo apt-get install python3.4-dev
	```

3. Set up a new virtualenv and install the required packages:
	```
	virtualenv venv
	source venv/bin/activate
	pip install -r dev-requirements.txt
	```

4. Set up the database and super user:
	```
	./manage.py migrate
	./manage.py createsuperuser
	```

5. Run the application:
	```
	./manage.py runserver
	```

## Developers
Also read the [HACKING](https://github.com/st-tu-dresden/tud_praktomat_neu/blob/master/HACKING.md) documentation for useful development tips and conventions.
