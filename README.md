Test locust file
```
locust -f locustfile3.py \
  --host=https://tv-api.api.vinasports.com.vn \
  --headless \
  --users 200 \
  --spawn-rate 20 \
  --run-time 5m \
  --csv=/Users/trancong/locust/results/vinasports \
  --html=/Users/trancong/locust/results/report.html \
  --logfile=/Users/trancong/locust/results/locust.log \
  --loglevel=INFO
```
Chạy UI 
```
locust -f scenario_test4_file.py \
  --host=https://tv-api.api.vinasports.com.vn \
  --web-port 8000 \
  --process -1
```
