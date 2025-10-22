docker stop stocks-dashboard 
docker rm stocks-dashboard
docker build -t stocks-dashboard .
docker run -d   --name stocks-dashboard   -p 5000:5000   stocks-dashboard
docker run -d   --name stocks-dashboard   -p 5000:5000 -v ${PWD}:/data  stocks-dashboard

docker volume create pimetrics
docker stop stocks-dashboard
docker rm stocks-dashboard 
docker build -t stocks-dashboard .
docker run -d --name stocks-dashboard -p 5000:5000  -v pimetrics:/app/data stocks-dashboard