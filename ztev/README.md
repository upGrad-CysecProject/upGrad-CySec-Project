This document is in reference with using the aws region us-east-1
Sign in to aws console and visit https://us-east-1.console.aws.amazon.com/cognito/users

- Create a user pool. 
  Enter a name, and click on review defaults. 
  Click on Create Pool.

- Go to the pool created.

- Go to general settings and note down your pool ID for later use.

- Go to App Integration -> Domain Name. 
  Enter a domain prefix name and check availability. Save the changes.

- Go to the user pool. Goto on app clients.

- Add an app client for server. Provide a name and click "Create app client"

- Click on show details and note down your app client id and secret for server.

- Go back to user pool and click on "App client settings".
  Add the following:
  
  Callback URL(s): https://localhost:8000/oidc_callback, https://localhost:9999/oidc_callback
  
  Sign out URL(s): https://localhost:8000/logout, https://localhost:9999/logout
  
  Allowed OAuth Flows: Authorization code grant
  
  Allowed OAuth Scopes: email, openid, profile

- Create the database
  Using AWS:
    Go to RDS:
    Click on create database.
    Choose Postgres and class free-tier.
    Choose Generate a password.
    Click on Create.
    
    Wait for db creation. Note down the generated password and endpoint id.
    psql -h <endpoint_url> -d postgres
    > Enter the password in the prompt.
    Run SQL:
      CREATE DATABASE ztev WITH OWNER = postgres ENCODING = 'UTF8';
    Update endpoint-url and password in server/config.py
  
  With Docker
  ```docker run -i --name ztev-postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=ztev -p 5432:5432 --rm postgres```

- Go to the server folder.
  ``` Requirements from system packages openssl development library ```
  ```pip install -r requirements.txt # try "pip install poetry" if it fails to install cryptograpy```
  ```pip install psycopg2==2.8.6 # if it fails try psycopg2-binary====2.8.6```
  ```cp client_secrets.json.example client_secrets.json```
  Update the <pool-id>, <domain-prefix>, <client-id> and <client-secret> in the client_secrets.json.
  To start the server execute
 ```python3 app.py```
  or 
  ```gunicorn wsgi:app```

- Go to the client folder.
  ```cp client_secrets.json.example client_secrets.json ```
  Update the <pool-id>, <domain-prefix>, <client_id> and <client_secret> in the client_secrets.json.
  

- Zip the client folder and to provide your users for secure voting.
  Your users should unzip the client folder.
  Go to the client folder and execute 
  ```python3 -m pip install -r requirements.txt```
  
  To start the voting listener:
  ```python3 app.py ```
  or
  ```gunicorn wsgi:app```


- Management: 
  Add 4 groups to the user pool
  ```
  Name          Desc    Precedence
  -----------------------------
  admin 	Admin	5	
  devops	DevOps	20	
  eng   	Development Engineering	25	
  it	        IT	10	
  ```
  
  Add 5 users to the user pool created above.
  ```
  Username, Group
  -----------------------
  upgrad+admin1@example.com, admin 
  upgrad+eng1@example.com, eng
  upgrad+eng2@example.com, eng
  upgrad+devops1@example.com, devops
  upgrad+it1@gmail.com, it
  ```

