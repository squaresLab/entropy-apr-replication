## Make GPU dockers with torch preinstalled
docker run --name=entropy -it --runtime=nvidia -e NVIDIA_VISIBLE_DEVICES=8,9 \
--mount type=bind,src=/home/aidan/entropy-apr-replication/,dst=/home \
--mount type=bind,src=/data/huggingface/,dst=/models/huggingface \
aidan

## Initialize container
XDG_CACHE_HOME='/models'
export XDG_CACHE_HOME
echo $XDG_CACHE_HOME
conda activate torch
export PATH=$PATH:/home/defects4j/framework/bin
cd /home

## Give access to folders
chmod -R a+rw /home/TBar

## Defects4j
tar -xvzf def
cd defects4j
apt-get update
apt-get -y install cpanminus
apt-get install wget
cpanm --installdeps .
apt-get install subversion
./init.sh
export PATH=$PATH:/home/defects4j/framework/bin
defects4j info -p Chart

D4J_HOME='/home/defects4j'
DEFECTS4J_HOME='/home/defects4j'
export D4J_HOME
export DEFECTS4J_HOME
echo $D4J_HOME

## Tar
tar -xvzf

## Java
apt update
apt-get install openjdk-8-jdk
java -version
apt install ant
apt install maven

## DEAR
https://github.com/AutomatedProgramRepair-2021/dear-auto-fix.git
cd dear-auto-fix
bash DEAR/approach/sbfl/setup.sh
python3 dear-auto-fix/approach/get_fl_data.py

## TBar
### Docker for TBar
docker run --name=tbar -it \
--mount type=bind,src=/home/aidan/entropy/ebfl,dst=/home \
kuiliu/tbar

./installD4J.sh

export PATH=$PATH:/home/TBar/D4J/defects4j/framework/bin

D4J_HOME='/home/TBar/D4J/defects4j'
DEFECTS4J_HOME='/home/TBar/D4J/defects4j'
export D4J_HOME
export DEFECTS4J_HOME

./checkoutD4JBugs.sh

### Run Tbar
mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.MainPerfectFL -Dexec.args="/home/TBar/D4J/projects/ Chart_4 /home/defects4j/ false"
### compile Tbar
mvn compile -Dmaven.wagon.http.ssl.insecure=true -Dmaven.wagon.http.ssl.allowall=true -Dhttps.protocols=TLSv1.2

## remove git history
git filter-branch --tree-filter "rm -rf patches/patches_shibboleth" --prune-empty HEAD
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
echo patches/patches_shibboleth/ >> .gitignore
git add .gitignore
git commit -m 'Removing patches/patches_shibboleth from git history'
git gc
git push origin master --force

cp -a /home/aidan/entropy/ebfl/TBar/D4J/. //home/aidan/TBar/D4J/

## Docker
docker commit 41762c01b56f aidanben/aidan