********
Settings
********

``EXPLORER_SQL_BLACKLIST``
**************************
          
Disallowed words in SQL queries to prevent destructive actions. 

**Default Value:**

.. code-block:: python

   ('ALTER', 'RENAME ', 'DROP', 'TRUNCATE', 'INSERT INTO', 'UPDATE', 'REPLACE', 'DELETE', 'ALTER', 'CREATE TABLE', 'SCHEMA', 'GRANT', 'OWNER TO')



``EXPLORER_SQL_WHITELIST``
**************************
             
These phrases are allowed, even though part of the phrase appears in the blacklist.

**Default Value:**

.. code-block:: python

 ('CREATED', 'UPDATED', 'DELETED','REGEXP_REPLACE')



``EXPLORER_DEFAULT_ROWS``
*************************
                   
The number of rows to show by default in the preview pane.

**Default Value:**

.. code-block:: python                                                 
 
 1000

``EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES`` 
****************************************** 

If not None, show schema only for tables starting with these prefixes. "Wins" if in conflict with EXCLUDE       

**Default Value:**

.. code-block:: python

 None  # shows all tables

``EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES``  
******************************************

Don't show schema for tables starting with these prefixes, in the schema helper.

**Default Value:**

.. code-block:: python
                                
 ('django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.admin')


``EXPLORER_SCHEMA_INCLUDE_VIEWS``
*********************************
           
Include database views                                                                                          

**Default Value:**

.. code-block:: python

 False


``EXPLORER_ASYNC_SCHEMA``
*************************                   
Generate DB schema asynchronously. Requires Celery and EXPLORER_TASKS_ENABLED

**Default Value:**
                                   
False


``EXPLORER_DEFAULT_CONNECTION``
*******************************
             
The name of the Django database connection to use. Ideally set this to a connection with read only permissions

**Default Value:**

.. code-block:: python
  
 None  # Must be set for the app to work, as this is required


``EXPLORER_CONNECTIONS``
************************
                    
A dictionary of { 'Friendly Name': 'django_db_alias'}.

**Default Value:**

.. code-block:: python
                                                          
 {}  # At a minimum, should be set to something like { 'Default': 'readonly' } or similar. See connections.py for more documentation.


``EXPLORER_PERMISSION_VIEW`` 
****************************               
Callback to check if the user is allowed to view and execute stored queries

**Default Value:**

.. code-block:: python
                                     
 lambda r: r.user.is_staff


``EXPLORER_PERMISSION_CHANGE``
******************************   
           
Callback to check if the user is allowed to add/change/delete queries

**Default Value:**

.. code-block:: python
                                           
 lambda r: r.user.is_staff

``EXPLORER_TRANSFORMS``
***********************
                     
List of tuples like [('alias', 'Template for {0}')]. See features section of this doc for more info.

**Default Value:**            

.. code-block:: python

 []



``EXPLORER_RECENT_QUERY_COUNT``
*******************************
             
The number of recent queries to show at the top of the query listing.

**Default Value:**    
                                       
.. code-block:: python

 10


``EXPLORER_GET_USER_QUERY_VIEWS``
*********************************
           
A dict granting view permissions on specific queries of the form {userId:[queryId, ...], ...}

**Default Value:**

.. code-block:: python                   

 {}


``EXPLORER_TOKEN_AUTH_ENABLED`` 
******************************* 
           
Bool indicating whether token-authenticated requests should be enabled. See "Power Tips", above.

**Default Value:**

.. code-block:: python
                
 False


``EXPLORER_TOKEN`` 
******************
                         
Access token for query results.                                                                                 

**Default Value:**

.. code-block:: python

 "CHANGEME"


``EXPLORER_TASKS_ENABLED`` 
**************************
                 
Turn on if you want to use the snapshot_queries celery task, or email report functionality in tasks.py

**Default Value:**

.. code-block:: python
          
 False

``EXPLORER_S3_ACCESS_KEY``
**************************
                  
S3 Access Key for snapshot upload

**Default Value:**

.. code-block:: python
                                                                               
 None


``EXPLORER_S3_SECRET_KEY`` 
************************** 
                
S3 Secret Key for snapshot upload 

**Default Value:**

.. code-block:: python
                                                                              
 None


``EXPLORER_S3_BUCKET`` 
********************** 
                    
S3 Bucket for snapshot upload                                                                                  

**Default Value:**

.. code-block:: python

 None


EXPLORER_FROM_EMAIL
*******************       
              
The default 'from' address when using async report email functionality                                          

**Default Value:**

.. code-block:: python

 "django-sql-explorer@example.com"


``EXPLORER_DATA_EXPORTERS``                 
***************************

The export buttons to use. Default includes Excel, so xlsxwriter from optional-requirements.txt is needed

**Default Value:**

.. code-block:: python
       
 [('csv', 'explorer.exporters.CSVExporter'), ('excel', 'explorer.exporters.ExcelExporter'), ('json', 'explorer.exporters.JSONExporter')]

``EXPLORER_UNSAFE_RENDERING``  
*****************************     
        
Disable auto escaping for rendering values from the database. Be wary of XSS attacks if querying unknown data...  

**Default Value:**

.. code-block:: python

 False
