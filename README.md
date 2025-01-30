# Installer les paquets nécéssaires
- sudo snap install code --classic
- sudo apt install git

# Installer Flower dans un environnement virtuel
- sudo apt install python3.12-venv
- python3 -m venv flwrvenv
- source flwrvenv/bin/activate
- pip install flwr flwr-datasets ray torch torchvision

# Préparer Docker
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Préparer le répertoire contenant le code
mkdir FederatedLearning
cd FederatedLearning
code .
git init
git clone https://github.com/Yann-j3/FedLearn-Flower-Docker.git
cd FedLearn-Flower-Docker

# Créer le réseau Flower
docker network create --driver bridge flwr-network

# Démarrer le SuperLink
docker run --rm -p 9091:9091 -p 9092:9092 -p 9093:9093 --network flwr-network --name superlink --detach flwr/superlink:1.14.0 --insecure --isolation process

# Démarrer les SuperNodes
# Start two SuperNode containers
docker run --rm -p 9094:9094 --network flwr-network --name supernode-1 --detach flwr/supernode:1.14.0 --insecure --superlink superlink:9092 --node-config "partition-id=0 num-partitions=2" --clientappio-api-address 0.0.0.0:9094 --isolation process

docker run --rm -p 9095:9095 --network flwr-network --name supernode-2 --detach flwr/supernode:1.14.0 --insecure --superlink superlink:9092 --node-config "partition-id=1 num-partitions=2" --clientappio-api-address 0.0.0.0:9095 --isolation process

# Démarrer le conteneur du serveur
docker build -f serverapp.Dockerfile -t flwr_serverapp:0.0.1 .

docker run --rm --network flwr-network --name serverapp --detach flwr_serverapp:0.0.1 --insecure --serverappio-api-address superlink:9091

# Démarrer les conteneurs des clients
docker build -f clientapp.Dockerfile -t flwr_clientapp:0.0.1 .

docker run --rm --network flwr-network --name clientapp-1 --detach flwr_clientapp:0.0.1 --insecure --clientappio-api-address supernode-1:9094

docker run --rm --network flwr-network --name clientapp-2 --detach flwr_clientapp:0.0.1 --insecure --clientappio-api-address supernode-2:9095

# Vérifier
docker network inspect flwr-network

# Lancer la simulation
flwr build
flwr run
