echo "# Killing the APP"
sudo kill -9 $(sudo lsof -t -i:8060)
echo "# Starting the TA Client"
export GOOGLE_APPLICATION_CREDENTIALS="./configuration/deeprl-326711-2dd88867b5e4.json"
nohup nohup python3.7 -m gunicorn --config gunicorn_config.py server:server &