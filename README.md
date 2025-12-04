docker stop stocks-dashboard 
docker rm stocks-dashboard
docker build -t stocks-dashboard .
docker run -d   --name stocks-dashboard   -p 5000:5000   stocks-dashboard
docker run -d   --name stocks-dashboard   -p 5000:5000 -v ${PWD}:/data  stocks-dashboard

docker volume create pimetrics
docker stop stocks-dashboard
docker rm stocks-dashboard 
docker build -t stocks-dashboard .
docker run -d --name stocks-dashboard -p 5000:5000  -v pimetrics:/app/data -v /home/pi/pishare:/app/videos stocks-dashboard

docker logs --follow stocks-dashboard

docker ps --format "{{ .Names }}"


stocks-dashboard/
├── app/
│   ├── __init__.py            # App factory and scheduler setup
│   ├── config.py              # Constants like DB path
│   ├── routes.py              # Flask routes and API endpoints
│   ├── metrics.py             # Pi metrics collection and DB logic
│   ├── stocks.py              # Stock metrics logic
│   ├── ytstreamer.py          # YouTube download logic
│   └── scheduler.py           # BackgroundScheduler jobs
├── templates/                 # HTML files
├── static/                    # CSS, JS, images
├── run.py                     # Entry point
├── requirements.txt
└── tickers.txt

