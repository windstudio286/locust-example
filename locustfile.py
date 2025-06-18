from locust import HttpUser, task, between
from locust import LoadTestShape

class VinaSportsUser(HttpUser):
    wait_time = between(1, 2)
    page_size= 21  # Initial page number
    @task
    def get_publish_events(self):
        self.client.get("/api/v3/publish/event/related-to/", params={
                "id": "97a394a7-6630-465c-b76c-5a82cc607621",
                "page_num": "1",
                "page_size": str(self.page_size),
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "1"
        })
        self.page_size += 1

class StepLoadShape(LoadTestShape):
    step_time = 30        # Increase users every 30 seconds
    step_users = 20       # Add 50 users each step
    spawn_rate = 5       # Spawn 20 users per second
    max_users = 100       # Max 200 users

    def tick(self):
        run_time = self.get_run_time()
        current_step = run_time // self.step_time
        users = (current_step + 1) * self.step_users

        if users > self.max_users:
            return None

        return (users, self.spawn_rate)

