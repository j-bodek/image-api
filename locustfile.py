from locust import HttpUser, task


class TestUser(HttpUser):
    def on_start(self):
        r = self.client.post(
            "/api/token/",
            {
                "username": "admin",
                "password": "admin",
            },
        )
        self.token = r.json().get("access")

    @task
    def hello_world(self):
        file = open("test/image.jpeg", "rb")
        self.client.post(
            "/api/image/upload/",
            {"name": "testfile"},
            files={"file": file},
            headers={"Authorization": f"Bearer {self.token}"},
        )
