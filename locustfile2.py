from locust import HttpUser, task, between, LoadTestShape
import gevent

# Define your test user behavior
class VinaSportsUser(HttpUser):
    wait_time = between(1, 2)  # You can adjust this based on needs

    @task
    def visit_both_links(self):
        # Make two requests in parallel (same time simulation)
        greenlets = [
            gevent.spawn(self.client.get, "/api/v3/publish/event/", params={
                "id": "54a04587-0350-4905-990b-49968cef16d9",
                "platform": "fairplay",
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "2"
            }),
            gevent.spawn(self.client.get, "/api/v3/publish/event/related-to/", params={
                "id": "54a04587-0350-4905-990b-49968cef16d9",
                "page_num": "1",
                "page_size": "21",
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "2"
            })
        ]
        gevent.joinall(greenlets)


# Define load shape: ramp from 100 to 200 users, 20 users/sec, pause at 200
class CustomLoadShape(LoadTestShape):
    start_users = 100
    end_users = 200
    spawn_rate = 20
    step_time = (end_users - start_users) // spawn_rate  # seconds to ramp up (5s)

    def tick(self):
        run_time = self.get_run_time()

        if run_time < self.step_time:
            user_count = self.start_users + int(run_time * self.spawn_rate)
            return (user_count, self.spawn_rate)
        elif self.step_time <= run_time < self.step_time + 60:
            return (self.end_users, 0)  # pause for 60 seconds
        elif run_time >= self.step_time + 60:
            return (self.end_users, 0)  # continue at full 200 users
        else:
            return None