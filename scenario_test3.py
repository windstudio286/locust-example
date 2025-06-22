from locust import HttpUser, TaskSet, task, between, SequentialTaskSet, LoadTestShape
import random
import logging
import gevent
logger = logging.getLogger(__name__)
# Kịch bản user duyệt nội dung, xem content trong khoảng thời gian rồi lại chọn xem content khác từ video liên quan
class OttContinuousWatchBehavior(TaskSet): # This TaskSet will handle the continuous watching loop

    # Assume a list of content IDs for simulation.
    CONTENT_IDS = [
        "97a394a7-6630-465c-b76c-5a82cc607621", "43987b30-1a0f-4abf-9b6f-95ea74c272b7",
        "877d190e-31c1-4233-99a5-d75f69dfbc7e", "662b4897-09d8-4ebb-8b59-2f1c2ca10af4", "e89b4a42-c6b6-4a7e-bdc6-f4568d085e8b"
    ]
    # Store the selected content ID for subsequent tasks
    current_content_id = None 

    @task
    def watch_and_click_next(self):
        """
        This task simulates watching the current video and then selecting another.
        It implicitly loops due to how TaskSets work with @task.
        """
        self.current_content_id = self.user.shared_value
        if self.current_content_id is None:
            # If this is the very first loop, pick a random content.
            # In the main flow, we ensure it's set by the initial detail call.
            self.current_content_id = random.choice(self.CONTENT_IDS)

        # Simulate user staying on detail page / watching video
        watch_duration = random.randint(15, 60) # 15 to 60 in seconds
        logger.info(f"User {self.user.environment.runner.user_count} watching video ID {self.current_content_id} for {watch_duration} seconds.")
        gevent.sleep(watch_duration) # Interrupt for watch_duration seconds

        # Now, simulate clicking on another video
        new_content_id = random.choice(self.CONTENT_IDS)
        # Ensure it's not the same video for a more realistic next click
        # In a real app, related videos would provide different IDs
        while new_content_id == self.current_content_id:
            new_content_id = random.choice(self.CONTENT_IDS)
        
        self.current_content_id = new_content_id # Update for the next loop

        logger.info(f"User {self.user.environment.runner.user_count} clicking on new content ID: {new_content_id}.")

        # Call detail API for the new video
        with self.client.get("/api/v3/publish/event/",params={
                "id": self.current_content_id,
                "platform": "fairplay",
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "1"
            }, catch_response=True, name="/api/v3/publish/event/") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Detail API failed for {self.current_content_id} with status code {response.status_code}")
        logger.info(f"User {self.user.environment.runner.user_count} getting related videos for content ID: {self.current_content_id}.")
        # Call related videos API for the new video
        with self.client.get("/api/v3/publish/event/related-to/",params={
                "id": self.current_content_id,
                "page_num": "1",
                "page_size": "21",
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
                "type": "1"
            }, catch_response=True, name="/api/v3/publish/event/related-to/") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Related Videos API failed for {self.current_content_id} with status code {response.status_code}")

        # After these calls, the `watch_and_click_next` task will repeat.

class OttUserFlow(SequentialTaskSet): # This TaskSet defines the initial sequence

    # Shared content IDs
    CONTENT_IDS = OttContinuousWatchBehavior.CONTENT_IDS
    selected_content_id = None 
    def on_start(self):
        """ Called once when a new user starts. """
        logger.info(f"User {self.user.environment.runner.user_count} starting new session.")
        # self.client.headers = {"User-Agent": "LocustOTTTestClient/1.0"}

    @task
    def browse_once(self):
        """ Task 1: User opens App and browses content - happens only once per user. """
        logger.info(f"User {self.user.environment.runner.user_count} performing get home content at once.")
        with self.client.get("/api/v3/publish/events/",params= {
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
            }, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
        
        # Simulate think time after Browse (1-2 seconds)
        gevent.sleep(random.randint(1, 2))

    @task
    def select_first_video_and_start_watching_loop(self):
        """ 
        Task 2: User selects a video, gets detail/related, and then enters
        the continuous watching loop.
        """
        # Select the very first content ID for this user's session
        selected_content_id = random.choice(self.CONTENT_IDS)
        # Store it in the continuous behavior taskset instance for later use
        self.selected_content_id = selected_content_id 
        
        logger.info(f"User {self.user.environment.runner.user_count} selecting -first- video ID: {selected_content_id}.")

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
        self.user.shared_value = selected_content_id
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
        {"duration": 60, "users": 1, "spawn_rate": 1},
        {"duration": 100, "users": 5, "spawn_rate": 2},
        {"duration": 180, "users": 10, "spawn_rate": 4},
        {"duration": 220, "users": 4, "spawn_rate": 2},
        {"duration": 230, "users": 2, "spawn_rate": 1},
        {"duration": 240, "users": 1, "spawn_rate": 1},
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                tick_data = (stage["users"], stage["spawn_rate"])
                return tick_data

        return None