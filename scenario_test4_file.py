from locust import HttpUser, TaskSet, task, between, SequentialTaskSet, LoadTestShape, events
import random
import logging
import gevent
import os
logger = logging.getLogger(__name__)
from locust.runners import MasterRunner, WorkerRunner, LocalRunner
import threading
from locust.event import EventHook

# Import our shared state manager
from shared_state_manager import write_flag, read_flag, initialize_flag, FLAG_FILE

# Global variable to hold the shared state, primarily for local (non-distributed) testing
# In distributed mode, workers will read from the file.
# The master process will also have its own state, but workers will rely on the file.
shared_test_active_flag = False

@events.init.add_listener
def _locust_init(environment, **kwargs):
    """
    Initializes the shared flag file when Locust starts.
    This listener runs on both master and worker processes.
    We only want the master to be responsible for initializing the flag if it doesn't exist.
    """
    logger.info(f"[{os.getpid()}] _locust_init environment.runner: {environment.runner}")
    if isinstance(environment.runner, MasterRunner) or isinstance(environment.runner, LocalRunner): # Check if it's the master process
        logger.info(f"[{os.getpid()}] Master process initializing shared flag file.")
        initialize_flag(False) # Set initial state to False

    # Clean up the file when Locust stops (optional, but good for clean runs)
    @events.quitting.add_listener
    def _locust_quitting(environment, **kwargs):
        logger.info(f"[{os.getpid()}] _locust_quitting environment.runner: {environment.runner}")
        if isinstance(environment.runner, MasterRunner) or isinstance(environment.runner, LocalRunner):
            logger.info(f"[{os.getpid()}] Master process cleaning up shared flag file.")
            if os.path.exists(FLAG_FILE):
                os.remove(FLAG_FILE)

# Shared variable on the worker
shared_data = {"is_rewatch": False }

# Define the custom message event
custom_message_event = EventHook()


# Define a listener function
def on_my_custom_message(environment, msg, **kwargs):
    logger.info(f"Received custom message: {msg}, environment: {environment}, kwargs: {kwargs}")
    shared_data["is_rewatch"] = msg["is_rewatch"]
    logger.info(f"Received update is_rewatch: {shared_data['is_rewatch']}")
    # You can access the environment instance here to interact with Locust
    # For example, you could access the runner instance to get the user count
    # user_count = environment.runner.user_count

# Register the listener
custom_message_event.add_listener(on_my_custom_message)
# @events.custom_message.add_listener
def on_custom_message(environment, msg, **kwargs):
    if msg["name"] == "my_data":
        shared_data["is_rewatch"] = msg["data"]["is_rewatch"]
        logger.info(f"Received update from master: {shared_data['is_rewatch']}")

# Kịch bản user duyệt nội dung, xem content xem xong trong khoảng thời gian thì tín hiệu die, tất cả user thực hiện ấn retry
class OttContinuousWatchBehavior(TaskSet): # This TaskSet will handle the continuous watching loop

    # Store the selected content ID for subsequent tasks
    selected_content_id = "97a394a7-6630-465c-b76c-5a82cc607621" 

    @task
    def watch_and_click_next(self):
        """
        This task simulates watching the current video and then selecting another.
        It implicitly loops due to how TaskSets work with @task.
        """
        # is_rewatch = getattr(self.user.environment, "is_rewatch", False)
        #is_rewatch = shared_data["is_rewatch"]
        is_rewatch = read_flag()
        logger.info(f"User {self.user.environment.runner.user_count} with is_rewatch: {is_rewatch}")
        if not is_rewatch:
            logger.info(f"User {self.user.environment.runner.user_count} is watching video: {self.selected_content_id}.")
        else:
            # Call detail API for the new video
            logger.info(f"User {self.user.environment.runner.user_count} selecting -strike- video ID: {self.selected_content_id}.")
            with self.client.get("/api/v3/publish/event/",params={
                    "id": self.selected_content_id,
                    "platform": "fairplay",
                    "sub_platform": "2",
                    "sub_version_name": "8.8.4",
                    "type": "1"
                }, catch_response=True, name="/api/v3/publish/event/") as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Detail API failed for {self.selected_content_id} with status code {response.status_code}")
            logger.info(f"User {self.user.environment.runner.user_count} getting -strike- related videos for content ID: {self.selected_content_id}.")
            # Call related videos API for the new video
            with self.client.get("/api/v3/publish/event/related-to/",params={
                    "id": self.selected_content_id,
                    "page_num": "1",
                    "page_size": "21",
                    "sub_platform": "2",
                    "sub_version_name": "8.8.4",
                    "type": "1"
                }, catch_response=True, name="/api/v3/publish/event/related-to/") as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Related Videos API failed for {self.selected_content_id} with status code {response.status_code}")

        # After these calls, the `watch_and_click_next` task will repeat.

class OttUserFlow(SequentialTaskSet): # This TaskSet defines the initial sequence

    selected_content_id = "97a394a7-6630-465c-b76c-5a82cc607621" 
    def on_start(self):
        """ Called once when a new user starts. """
        logger.info(f"User {self.user.environment.runner.user_count} starting new session.")
        # self.client.headers = {"User-Agent": "LocustOTTTestClient/1.0"}

    @task
    def browse_once(self):
        """ Task 1: User opens App and browses content - happens only once per user. """
        logger.info(f"Task 1: User {self.user.environment.runner.user_count} performing get home content at once.")
        with self.client.get("/api/v3/publish/events/",params= {
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
            }, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
        wait_time_1 = random.randint(10, 45)

        # Simulate think time after Browse (1-2 seconds)
        logger.info(f"Task 1: User {self.user.environment.runner.user_count} is waiting {wait_time_1}s for choosing content .")
        gevent.sleep(wait_time_1)

    @task
    def select_first_video_and_start_watching_loop(self):
        """ 
        Task 2: User selects a video, gets detail/related, and then enters
        the continuous watching loop.
        """
        logger.info(f"Task 2: User {self.user.environment.runner.user_count} selecting -first- video ID: {self.selected_content_id}.")
        # Call detail API for the first video
        logger.info(f"User clicking on -first- content ID: {self.selected_content_id} to get detail.")
        with self.client.get("/api/v3/publish/event/",params={
                "id": self.selected_content_id,
                "platform": "fairplay",
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "1"
            }, catch_response=True, name="/api/v3/publish/event/") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Detail API failed for {self.selected_content_id} with status code {response.status_code}")

        logger.info(f"User getting -first- related videos for content ID: {self.selected_content_id}.")
        with self.client.get("/api/v3/publish/event/related-to/",params={
                "id": self.selected_content_id,
                "page_num": "1",
                "page_size": "21",
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "1"
            }, catch_response=True, name="/api/v3/publish/event/related-to/") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Related Videos API failed for {self.selected_content_id} with status code {response.status_code}")
        self.schedule_task(OttContinuousWatchBehavior,True)
        # self.interrupt(False)
        


class WebsiteUser(HttpUser):
    host = "https://tv-api.api.vinasports.com.vn" # IMPORTANT: Change this to your actual application URL.
    
    # Since we are managing waits with self.interrupt(), we set this to None.
    wait_time = between(1, 3)
    tasks = [OttUserFlow] # Start with the main sequential flow
    
    # Optional: If you want to log details of when tasks are called/interrupted
    # events.quitting.add_listener(lambda: print("Locust test is stopping."))
class StagesShape(LoadTestShape):
    """
    A simply load test shape class that has different user and spawn_rate at
    different stages.

    Keyword arguments:

        stages -- A list of dicts, each representing a stage with the following keys:
            duration -- When this many seconds pass the test is advanced to the next stage
            users -- Total user count
            spawn_rate -- Number of users to start/stop per second
            stop -- A boolean that can stop that test at a specific stage

        stop_at_end -- Can be set to stop once all stages have run.
    """

    stages = [
        {"duration": 30, "users": 10, "spawn_rate": 1 , "is_rewatch": False},
        {"duration": 60, "users": 100, "spawn_rate": 100, "is_rewatch": True},
        {"duration": 180, "users": 0, "spawn_rate": 1, "is_rewatch": False}
    ]

    def tick(self):
        global shared_state
        run_time = self.get_run_time()
        logger.info(f"Tick run_time: {run_time}.")
        for stage in self.stages:
            if run_time < stage["duration"]:
                is_rewatch = stage["is_rewatch"]
                if is_rewatch != getattr(self.runner.environment, "is_rewatch", False) :
                    self.runner.environment.is_rewatch = is_rewatch
                    write_flag(is_rewatch)
                    custom_message_event.fire(environment=self.runner.environment, msg={"is_rewatch": is_rewatch}, some_kwarg="some value")
                    logger.info(f"Tick change value is_rewatch with new: {self.runner.environment.is_rewatch}.")

                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None