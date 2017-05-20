from happy-worker import Happy-worker

happy = Happy-worker("example_db")

if __name__ == "__main__":
    dummy_job = {"hello": "world"}
    happy.submit(dummy_job, retries=3)
