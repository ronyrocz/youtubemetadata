import random

from locust import HttpUser, task, between
class VideoAPIStressTest(HttpUser):
    wait_time = between(1,5)

    channel_ids = [
        "UC002efe44f8d54cd9b69e94",
        "UC020c46995e934677945aa7",
        "UC02a8a0d1df5e40b483f8b5",
        "UC046d2371c2754f78993860",
        "UC08999a5233284627bf4b07",
        "UC1f43f1e5e5d645dcba66df",
        "UC201d8ab31aa04921bae29c",
        "UC2280dd4c753d437292b091",
        "UC242f0208cdbc4494af0538",
        "UC24f428340f0944d6a3fba1",
        "UC292ba79d350a47d2830a48",
        "UC29cc0e85c94a432c8feac6",
        "UC2e13c1588c4f442db2add9",
        "UC2fad5491047942d8b85622",
        "UC305a19a9b9084db79454ba",
        "UC311f220c73f6484d8be5ce",
        "UC324d3b5709a94b7c929784",
        "UC3561e149407d45629f41b4",
        "UC370b0a0f529644329a1734",
        "UC3734e8940f2a4d76a967e2",
        "UC3e8161a3e4f141d5b956c2",
        "UC3ee1dd1b832d4a2188f1d3",
        "UC3ffc5d063be34989bd2db4",
        "UC40194a7b651f4d1791c290",
        "UC452bb69d6794472a96ef38",
        "UC45702ecfd3834a87861ca8",
        "UC45b1b8282e914698814c8c",

    ]
    @task
    def get_videos(self):
        channel_id = random.choice(self.channel_ids)  # Pick a random channel ID

        self.client.get(f"/video/?channel_id={channel_id}")