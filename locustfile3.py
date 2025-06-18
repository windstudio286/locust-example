from locust import HttpUser, task, between, constant, LoadTestShape
import random
import logging
import datetime
logger = logging.getLogger(__name__)


class VinaSportsUser(HttpUser):
    @property
    def wait_time(self):
        is_burst = getattr(self.environment, "burst_mode", False)

        # Log occasionally to avoid spamming logs
        if random.random() < 0.01:
            logger.info(f"[User] Burst Mode: {is_burst}")

        # Return a callable that returns wait time in seconds
        return (lambda: 0) if is_burst else (lambda: random.uniform(1, 3))

    @task
    def get_publish_events(self):
        is_burst = getattr(self.environment, "burst_mode", False)

        # Choose page size
        page_size = random.choice([10, 21, 50, 100, 200]) if is_burst else 21
        logger.info(f"page_size: {page_size}")
        logger.info(f"is_burst: {is_burst}")
        self.client.get("/api/v3/publish/event/related-to/", params={
            "id": "97a394a7-6630-465c-b76c-5a82cc607621",
            "page_num": "1",
            "page_size": str(page_size),
            "sub_platform": "2",
            "sub_version_name": "8.8.4",
            "type": "1"
        })


class ThreePhaseLoadShape(LoadTestShape):
    ramp_up_time = 120  # 2 minutes
    pause_time = 60     # 1 minute
    max_users = 200
    spawn_rate = 20

    def tick(self):
        run_time = self.get_run_time()
        # Handle total run-time
        total_run_time_raw = getattr(self.runner.environment.parsed_options, "run_time", None)
        if isinstance(total_run_time_raw, datetime.timedelta):
            total_run_time = total_run_time_raw.total_seconds()
        elif isinstance(total_run_time_raw, (int, float)):
            total_run_time = total_run_time_raw
        else:
            total_run_time = 310  # fallback default: 5 min
        # Define phase durations
        ramp_up_time = self.ramp_up_time
        pause_time = self.pause_time
        burst_time = max(0, total_run_time - ramp_up_time - pause_time)
        logger.info(f"ramp_up_time: {ramp_up_time}")
        logger.info(f"pause_time: {pause_time}")
        logger.info(f"burst_time: {burst_time}")
        logger.info(f"total_run_time: {total_run_time}")
        if run_time < self.ramp_up_time:
            # Phase 1: ramp up
            user_count = int((run_time / self.ramp_up_time) * self.max_users)
            self.runner.environment.burst_mode = False
            return user_count, self.spawn_rate

        elif run_time < self.ramp_up_time + self.pause_time:
            # Phase 2: pause
            self.runner.environment.burst_mode = False
            return self.max_users, 1

        elif run_time < self.ramp_up_time + self.pause_time + burst_time:
            # Phase 3: burst mode
            self.runner.environment.burst_mode = True
            return self.max_users, self.max_users  # All users act as fast as possible
        else:
            return None  # stop test
