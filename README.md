werecars
========

Werecars game, Tornado websocket server and CopperLicht WebGL client

Games server is started with command:
python ws_server.py

*Requirements:*
* Python
* virtualenv
* virtualenvwrapper

*Installation instructions:*
#######################################################
# install virtualenvwrapper if not already installed
#######################################################
pip install virtualenvwrapper

#########################
# create virtualenv
#########################
mkvirtualenv werecars --no-site-packages

#########################
# install tornatno server
#########################
workon werecars
cdvirtualenv
pip install -e git+git://github.com/facebook/tornado.git#egg=tornado

#########################
# create virtualenv project
#########################
mkproject werecars

#########################
# clone git repo of the game from github
#########################
cdproject
git clone https://github.com/matejp/werecars.git .
