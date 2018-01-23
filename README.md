# Bloom Logs

RESTful API to create bloom filters used to quickly find matching log lines.

Requires Python >= 3.6

## Installation

### Install Rabbitmq

###### Add the APT repository
```bash
echo 'deb http://www.rabbitmq.com/debian/ testing main' |
     sudo tee /etc/apt/sources.list.d/rabbitmq.list
```

###### Add public key
```bash
wget -O- https://www.rabbitmq.com/rabbitmq-release-signing-key.asc |
     sudo apt-key add -
```

###### Install 
```bash
apt-get update && apt-get install rabbitmq-server
```

###### Setup a user

```bash
rabbitmqctl add_user admin {{ rabbit_password }}
rabbitmqctl set_user_tags admin administrator
rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"
```

###### Enable Rabbitmq management
```bash
rabbitmq-plugins enable rabbitmq_management
service rabbitmq-server restart
```

### Install Redis

```bash
sudo apt install redis-server
```

### Install Mongodb
```bash
apt-get install mongodb-server
```
Edit `/etc/mongodb.conf` and change `bind_ip` to a service-net ip instead of 127.0.0.1.
Update the `MONGO_HOST` from `bf.settings.py` to match this same ip.


##### For celery workers
```bash
apt-get install mongodb-clients
```

### Install Nginx
```bash
apt-get install nginx
```

Edit your default nginx config `/etc/nginx/sites-enabled/default`

Be sure to replace `{SERVER_NAME_HERE}` with your hostname.
```text
server {
    listen 80;
    server_name {SERVER_NAME_HERE};

    location /flower/ {
        rewrite ^/flower/(.*)$ /$1 break;
        proxy_pass http://127.0.0.1:5555;
        proxy_set_header Host $host;
    }

    location / {
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   Host      $http_host;
        proxy_pass         http://127.0.0.1:5000;
    }
}
```
Remember to restart nginx after you make changes.

### Install python 3.6 if not already installed
```bash
add-apt-repository ppa:jonathonf/python-3.6
apt-get update
apt-get install python3 build-essential python3-dev
```

### Install python packages
```bash
pip3 install -r requirements.txt
```

##### Start the server

```bash
python3 app.py
```

##### Start celery workers
 This starts 10 celery workers as well as a task monitor (flower) at [http://localhost/flower](http://localhost/flower)

```bash
./start_workers.sh
```

##### Start scheduler processes
_The scheduler is responsible for keeping bloom filters up to date._

```bash
python3 scheduler.py
```

## Client interaction
##### API interaction
```bash
# Preform a search
curl -X POST http://127.0.0.1/search -F 'object=Account/Container/ObjectName'
```

##### Command line interaction

```bash
# Display help
./triage.py -h

# To search:
./triage.py account/container/object

# To update mongodb with the latest log names (specify full for the initial installation):
./triage.py --update-db full

# To process any logs that are currently marked as "not processed" in mongodb:
./triage.py  --process-logs
```