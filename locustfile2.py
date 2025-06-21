from locust import HttpUser, task, between, SequentialTaskSet, constant
import gevent
import random
import time
import logging # Import the logging module
import threading
from gevent.lock import Semaphore
from locust.exception import StopUser
# Get a logger instance
# It's good practice to get a logger for your specific module/class
logger = logging.getLogger(__name__)

# You can also configure logging level if needed (optional, often done globally)
# logging.basicConfig(level=logging.INFO) # For example, to see INFO messages and above
# --- Global Counter and Lock ---
# This semaphore will protect access to the user_id_counter
user_id_counter_lock = Semaphore()
# This counter will hold the next available sequential user ID
next_user_id = 0
# Function to get the next sequential user ID safely
def get_next_sequential_user_id():
    global next_user_id
    with user_id_counter_lock: # Acquire the lock
        next_user_id += 1
        return next_user_id
    # The lock is automatically released when exiting the 'with' block
class UserBehavior(SequentialTaskSet):

    @task
    def fetch_slides_data(self):
        with self.client.get("/api/v3/publish/slides/", params={
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
            }, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected status code (slides): {response.status_code}")
        logger.info(f"User {id(self.user)}/{self.user.environment.runner.user_count} - Completed fetch_slides_data task.")
    @task
    def fetch_events_data(self):
        with self.client.get("/api/v3/publish/events/", params={
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
            }, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected status code (events): {response.status_code}")
        logger.info(f"User {id(self.user)}/{self.user.environment.runner.user_count} - Completed fetch_events_data task.")
        # gevent.sleep(random.uniform(1, 2))
        gevent.sleep(1)

    @task
    def fetch_event_details_concurrently(self):
        # Log message when this task starts
        # You can use different levels: debug, info, warning, error, critical
        logger.info(f"User {id(self.user)}/{self.user.environment.runner.user_count} - /Running/ fetch_event_details_concurrently task.")
        try:
            greenlets = [
                gevent.spawn(self.client.get, "/api/v3/publish/event/", params={
                    "id": "97a394a7-6630-465c-b76c-5a82cc607621",
                    "platform": "fairplay",
                    "sub_platform": "2",
                    "sub_version_name": "8.8.4",
                    "type": "1"
                }),
                gevent.spawn(self.client.get, "/api/v3/publish/event/related-to/", params={
                    "id": "97a394a7-6630-465c-b76c-5a82cc607621",
                    "page_num": "1",
                    "page_size": "21",
                    "sub_platform": "2",
                    "sub_version_name": "8.8.4",
                    "type": "1"
                })
            ]
            gevent.joinall(greenlets)
            for g in greenlets:
                if g.exception:
                    logger.info(f"Error in concurrent greenlet: {g.exception}")
                    # You might want to fail the task here if an internal greenlet failed
                    # self.environment.events.request.fire(request_type="GET", name="concurrent_event_fail", response_time=0, exception=g.exception)

        except Exception as e:
            logger.error(f"User {id(self.user)}{self.user.environment.runner.user_count} - An error occurred in fetch_event_details_concurrently: {e}", exc_info=True)
        finally:
            logger.info(f"User {id(self.user)}/{self.user.environment.runner.user_count} - All concurrent requests /completed/, stopping user.")
            # The quit call should still happen, even if there's an error
            # self.user.environment.runner.quit()
            raise StopUser()


class ScenarioTest1(HttpUser): # Or FastHttpUser
    wait_time = between(1, 3)
    tasks = [UserBehavior]
    # This method runs once for each HttpUser instance when it's spawned
    # def on_start(self):
    #     # Assign a sequential ID to this user instance
    #     self.sequential_id = get_next_sequential_user_id()
    #     logger.info(f"HttpUser {self.__class__.__name__} (Sequential ID: {self.sequential_id}) started.")
