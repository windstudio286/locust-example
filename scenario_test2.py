from locust import HttpUser, TaskSet, task, between, SequentialTaskSet
import random
import logging
import gevent
logger = logging.getLogger(__name__)
from locust.contrib.fasthttp import FastHttpUser
class OttUserBehavior(SequentialTaskSet): # Use SequentialTaskSet for ordered execution

    # Assume a list of content IDs for simulation.
    CONTENT_IDS = [
        "97a394a7-6630-465c-b76c-5a82cc607621", "43987b30-1a0f-4abf-9b6f-95ea74c272b7",
        "877d190e-31c1-4233-99a5-d75f69dfbc7e", "662b4897-09d8-4ebb-8b59-2f1c2ca10af4", "e89b4a42-c6b6-4a7e-bdc6-f4568d085e8b"
    ]

    
    # Store the selected content ID for subsequent tasks
    selected_content_id = None 

    def on_start(self):
        """ on_start is called when a Locust user starts running """
        logger.info("Starting a new OTT user session...")
        # self.client.headers = {"User-Agent": "LocustOTTTestClient/1.0"}

    @task
    def browse_content(self):
        """ Task 1: User opens App and browses content """
        logger.info(f"User {self.user.environment.runner.user_count} Browse content.")
        with self.client.get("/api/v3/publish/events/",params= {
                "sub_platform": "2",
                "sub_version_name": "8.8.4",
            }, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Unexpected status code: {response.status_code}")
        
        # Simulate think time after Browse (uses HttpUser's wait_time)
        wait_time_1 = random.randint(1, 5);
        logger.info(f"User will wait {wait_time_1}s for choosing content.")
        gevent.sleep(wait_time_1) # Interrupt for 1-5 seconds after browse
        logger.info(f"User chosed content!!!")

    @task
    def select_and_get_detail(self):
        """ Task 2: User clicks content, gets detail """
        self.selected_content_id = random.choice(self.CONTENT_IDS)
        logger.info(f"User clicking on content ID: {self.selected_content_id} to get detail.")
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

    @task
    def get_related_videos(self):
        """ Task 3: Get related videos for the selected content """
        if not self.selected_content_id:
            # This should ideally not happen in SequentialTaskSet if flow is correct
            print("Error: No content ID selected for related videos.")
            return

        logger.info(f"User getting related videos for content ID: {self.selected_content_id}.")
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
        
        # Simulate think time (watching video) after detail and related calls
        watch_duration = random.randint(15, 60) # 15 to 60 in seconds
        logger.info(f"User watching video for {watch_duration} seconds.")
        gevent.sleep(watch_duration) # Interrupt for watch_duration seconds
        logger.info(f"User watched the video {self.selected_content_id} for {watch_duration} seconds !!!")

    # After watching, the user will implicitly loop back to `browse_content` due to SequentialTaskSet
    # If you want to explicitly model clicking another video *immediately* after watching,
    # you could have another task or a helper function that does this repeatedly.
    # For this simulation, SequentialTaskSet will make the user go through the cycle again,
    # effectively simulating "click other video" by starting a new browse-detail-related cycle.

class WebsiteUser(HttpUser):
    host = "https://tv-api.api.vinasports.com.vn" # IMPORTANT: Change this to your actual application URL.
    # user will wait some time before starting task again
    wait_time = between(1, 3)  # Or between(0, 0) if you prefer explicit 0 wait

    tasks = [OttUserBehavior]