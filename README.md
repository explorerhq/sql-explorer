django-health-check
==================

This project checks a number of backends, if they are able to connect and do a simple action, e.g. check out the django ORM backend:


```python

class DjangoDatabaseBackend(BaseHealthCheckBackend):

    def check_status(self):
        try:
            obj = TestModel.objects.create(title="test")
            obj.title = "newtest"
            obj.save()
            obj.delete()
            return True
        except IntegrityError:
            raise ServiceReturnedUnexpectedResult("Integrity Error")
        except DatabaseError:
            raise ServiceUnavailable("Database error")


```

The project is made using some of the same codes, that the django admin site uses - so when you have sucessfully written a new plugin, you register it to the pool, e.g. 

```python
plugin_dir.register(DjangoDatabaseBackend)
```


Install
=======

Add this to urls.py

```python
url(r'^ht/', include('health_check.urls'))
```

Add required apps:

```python
    'health_check',
    'health_check_celery',
    'health_check_db',
    'health_check_cache',
    'health_check_storage',
```
(remember to add dependencies, e.g. djcelery - however you should have that already, if you have celery running)

Set up monitoring
=================

E.g. add to pingdom - django-health-check will return HTTP 200 if everything is OK and HTTP 500 if *anything* is not working.

Profit
======

![Screenshot of django-health-check](http://c.kristian.io/image/3C2s1Z3X071S/Screen%20Shot%202013-03-18%20at%2018.40.52.png)

Our mascot
==========
![django-health-check is the most interresting project in the world](http://c.kristian.io/image/1J3x031Q0S3B/36347774.jpg)


Dependencies
============

Python 2.7+ (Yes, thats right, we have **Python 3 support**)

Django 1.2+

