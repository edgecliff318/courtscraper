echo "# Killing the APP"
sudo kill -9 $(sudo lsof -t -i:8060)
echo "# Starting the TA Client"
export GOOGLE_APPLICATION_CREDENTIALS="./configuration/fubloo-app-1f213ca274de.json"
nohup nohup python3.7 -m gunicorn --config gunicorn_config.py server:server &