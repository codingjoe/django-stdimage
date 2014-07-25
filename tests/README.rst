Running tests
=============

Note
-----

If you encounter a setuptools issue the solution I found is installing a new setupools::

    $ wget https://bitbucket.org/pypa/setuptools/raw/0.8/ez_setup.py
    $ sudo /usr/bin/python ez_setup.py

Running tests
-------------

Navigate into the tests/ directory

::

    pip install Django==<Django Version Under Test>
    pip install -r requirements.txt
    python manage.py test
