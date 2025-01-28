from pymongo import MongoClient

class DBHandler:
    def __init__(self, mongodb_url, db_name, collection_name):
        self.client = MongoClient(mongodb_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def is_duplicate(self, file_unique_id):
        """Check if the video file is already indexed."""
        return self.collection.find_one({"file_unique_id": file_unique_id}) is not None

    def add_video(self, video_data):
        """Add a new video entry to the database."""
        self.collection.insert_one(video_data)

    def get_all_videos(self):
        """Retrieve all video entries from the database."""
        return list(self.collection.find({}, {"_id": 0}))

    def count_videos(self):
        """Count the total number of video entries in the database."""
        return self.collection.count_documents({})
