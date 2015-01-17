## Getting started
Note: This version has only been tested with Python 2.7.

1. Clone the repository:

	```
	git clone https://github.com/st-tu-dresden/tud_praktomat_neu.git
	cd tud_praktomat_neu
	```

2. Set up a new virtualenv and install the required packages:
	```
	virtualenv venv
	source venv/bin/activate
	pip install -r dev-requirements.txt
	```

3. Set up the database and super user:
	```
	./manage.py syncdb
	./manage.py createsuperuser
	```

4. Run the application:
	```
	./manage.py runserver
	```
