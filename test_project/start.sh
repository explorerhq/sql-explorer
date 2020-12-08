pip install -r requirements.txt
pip install -r optional-requirements.txt
python manage.py migrate
python manage.py shell <<ORM
from django.contrib.auth.models import User
u = User(username='admin')
u.set_password('admin')
u.is_superuser = True
u.is_staff = True
u.save()
from explorer.models import Query
q = Query(sql='select * from explorer_query;', title='Sample Query')
q.save()
ORM
python manage.py runserver
