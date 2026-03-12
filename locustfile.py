from locust import FastHttpUser, task, between

class HousingAPIUser(FastHttpUser):
    # This simulates "think time". Each simulated user will wait between 
    # 0.1 and 0.5 seconds before firing their next request.
    wait_time = between(0.1, 0.5)

    @task
    def get_listings(self):
        """
        Simulate a user browsing the main property listings page.
        We add a name parameter so Locust groups these requests nicely in the dashboard.
        """
        self.client.get("/api/listings/?limit=50", name="/api/listings/")

    # Optional: You can add more tasks here! Locust will randomly pick between them.
    # @task
    # def get_market_summary(self):
    #     self.client.get("/api/analytics/market-summary", name="/api/analytics/market-summary")