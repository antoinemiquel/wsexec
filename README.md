
# WSEXEC
## web-server REST (flask) permettant le lancement de scripts par ssh (paramiko)

## Requêtes

    | HTTP      | Method                                                | URI Action                                    |
    ---------------------------------------------------------------------------------------------------------------------
    | GET       | http://[hostname]/wsexec/tasks                        | Récupération de la liste des taches           |
    | GET       | http://[hostname]/wsexec/tasks/[task_id]              | Récupération d'une tache                      |
    | POST      | http://[hostname]/wsexec/tasks                        | Créer une nouvelle tache                      |
    | PUT       | http://[hostname]/wsexec/tasks                        | Mettre à jour une tache                       |
    ---------------------------------------------------------------------------------------------------------------------
    | GET       | http://[hostname]/wsexec/instances                    | Récupérer la liste des instances déclarées    |
    | GET       | http://[hostname]/wsexec/instances/[instance_id]      | Récupérer une instance déclarée               |
    | POST      | http://[hostname]/wsexec/instances                    | Créer une nouvelle instance                   |
    | PUT       | http://[hostname]/wsexec/instances                    | Mettre à jour une instance                    |
    | DELETE    | http://[hostname]/wsexec/instances/[instance_id]      | Enlever une instance des déclarations         |

## Structure de données

### task
	id          identifiant                                 Type numérique
	name        nom                                         Type texte
	tag         description                                 Type texte
	start       timestamp de début                          Type timestamp
	end         timestamp de fin                            Type timestamp
	instance    id de la machine où exécuter la tache       Type texte
	script      commande à exécuter                         Type texte
	user        utilisateur d'exécution                     Type texte
	stdout      sortie standard d'exécution                 Type texte
	stderr      sortie erreur d'exécution                   Type texte
	rc          code retour d'exécution                     Type text
	state       etat [INIT|CURRENT|DONE|ABORT]              Type texte

### instance
	id          identifiant                                 Type numérique
	ip          adresse IP                                  Type texte
	tag         description                                 Type texte
	state       etat [ACTIVE,DEACTIVATE]                    Type texte 

## Exemple de données

    tasks = [
        {
            'id': 1,
            'name': 'save_mongo',
            'tag': 'dump mongo',
            'start': 1436506743,
            'end': 1436506790,
            'instance': 501,
            'script': '/home/debian/mongo_save.sh',
            'user': 'debian',
            'stdout': 'NOK',
            'stderr': '',
            'rc': '1',
            'state': 'DONE'
        }]

    instances = [
        {
            'id': 200,
            'ip': '127.0.0.1',
            'tag': 'localhost',
            'state': 'ACTIVE'
        }]

## Pré-requis

	- la connexion ssh avec clefs doit être fonctionnelle vers les instances à joindre

## Installation
### Code et environnement
    cd ~
    mkdir wsexec
    git clone https://github.com/antoinemiquel/wsexec.git ~/wsexec
    virtualenv wsexec
    cd wsexec
    source bin/activate
    pip install flask Flask-HTTPAuth requests paramiko redis
    
### Gunicorn et nginx
    cd ~/wsexec
    source bin/activate
    pip install gunicorn
    source ~/wsexec/sources/EXPORTME.txt
    gunicorn --workers 3 --bind localhost:8000 wsgi &
    sudo apt-get install nginx
    sudo vi /etc/nginx/sites-available/wsexec    
            server {
                listen 80;
                server_name 0.0.0.0;
            
                location / {
                    include proxy_params;
                    proxy_pass http://localhost:8000;
                }
            }
    
    sudo ln -s /etc/nginx/sites-available/wsexec /etc/nginx/sites-enabled
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo service nginx restart
    
## A faire
    - sécuriser la connexion : authentification https

## Commandes curl

### tasks
    curl -u user:pass -i http://localhost:5000/wsexec/tasks
    curl -u user:pass -i http://localhost:5000/wsexec/tasks/2
    curl -u user:pass -i http://localhost:5000/wsexec/tasks/3
    
    curl -u user:pass -i -H "Content-Type: application/json" -X POST -d '{"name":"sleep 30", "tag":"essai", "instance":200, "script":"sleep 30", "user":"antoine"}' http://localhost:5000/wsexec/tasks
    curl -u user:pass -i -H "Content-Type: application/json" -X POST -d '{"name":"ls", "tag":"essai", "instance":200, "script":"ls -als", "user":"antoine"}' http://localhost:5000/wsexec/tasks
    
    curl -u user:pass -i -H "Content-Type: application/json" -X PUT -d '{"rc":5}' http://localhost:5000/wsexec/tasks/2
    curl -u user:pass -i -H "Content-Type: application/json" -X PUT -d '{"stdout":"ok"}' http://localhost:5000/wsexec/tasks/2

### instances
    curl -u user:pass -i http://localhost:5000/wsexec/instances
    curl -u user:pass -i http://localhost:5000/wsexec/instances/1
    
    curl -u user:pass -i -H "Content-Type: application/json" -X POST -d '{"ip":"127.0.0.1", "tag":"localhost", "state":"ACTIVE"}' http://localhost:5000/wsexec/instances
    
    curl -u user:pass -i -H "Content-Type: application/json" -X PUT -d '{"ip":"127.0.0.2", "tag":"localhost2", "state":"DEACTIVE"}' http://localhost:5000/wsexec/instances/1
    curl -u user:pass -i -H "Content-Type: application/json" -X PUT -d '{"ip":"127.0.0.1", "tag":"localhost", "state":"ACTIVE"}' http://localhost:5000/wsexec/instances/1
    
    curl -u user:pass -i -H "Content-Type: application/json" -X DELETE http://localhost:5000/wsexec/instances/1
