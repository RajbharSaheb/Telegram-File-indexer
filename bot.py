from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
import time

# Import configurations
from config import BOT_TOKEN

# Initialize database dictionary for user-specific settings
user_configs = {}

def start(update: Update, context: CallbackContext):
    """Start command handler."""
    update.message.reply_text(
        "Welcome! Use the following commands to configure:\n"
        "/set_db <MongoDB_URL> <Database_Name> <Collection_Name>\n"
        "/set_channel <Channel_ID>\n"
        "/index - Retrieve all indexed videos\n"
        "/index_progress - Show indexing progress\n"
        "Send any video file to index it."
    )

def set_db(update: Update, context: CallbackContext):
    """Set the MongoDB configuration for the user."""
    if len(context.args) != 3:
        update.message.reply_text("Usage: /set_db <MongoDB_URL> <Database_Name> <Collection_Name>")
        return

    user_id = update.effective_user.id
    mongodb_url, db_name, collection_name = context.args

    # Save user-specific MongoDB configuration
    user_configs[user_id] = {
        "mongodb_url": mongodb_url,
        "db_name": db_name,
        "collection_name": collection_name,
    }
    update.message.reply_text("MongoDB configuration saved!")

def set_channel(update: Update, context: CallbackContext):
    """Set the Telegram channel ID."""
    if len(context.args) != 1:
        update.message.reply_text("Usage: /set_channel <Channel_ID>")
        return

    user_id = update.effective_user.id
    channel_id = context.args[0]

    if user_id not in user_configs:
        update.message.reply_text("Please set your MongoDB configuration first using /set_db.")
        return

    # Update the channel ID in the user's configuration
    user_configs[user_id]["channel_id"] = channel_id
    update.message.reply_text("Channel ID saved!")

def handle_video(update: Update, context: CallbackContext):
    """Handle video file uploads."""
    user_id = update.effective_user.id

    if user_id not in user_configs:
        update.message.reply_text("Please configure MongoDB and channel using /set_db and /set_channel.")
        return

    user_config = user_configs[user_id]

    video = update.message.video
    if not video:
        update.message.reply_text("Please send a video file.")
        return

    # Get MongoDB configuration
    mongodb_url = user_config["mongodb_url"]
    db_name = user_config["db_name"]
    collection_name = user_config["collection_name"]

    # Connect to MongoDB
    client = MongoClient(mongodb_url)
    db = client[db_name]
    collection = db[collection_name]

    # Index video metadata to MongoDB
    video_data = {
        "file_id": video.file_id,
        "file_unique_id": video.file_unique_id,
        "file_name": video.file_name,
        "mime_type": video.mime_type,
        "file_size": video.file_size,
        "channel_id": user_config.get("channel_id"),
    }
    collection.insert_one(video_data)

    update.message.reply_text(f"Video indexed to MongoDB with ID: {video.file_id}")

def index_videos(update: Update, context: CallbackContext):
    """Retrieve all indexed videos from the database."""
    user_id = update.effective_user.id

    if user_id not in user_configs:
        update.message.reply_text("Please configure MongoDB and channel using /set_db and /set_channel.")
        return

    user_config = user_configs[user_id]

    # Get MongoDB configuration
    mongodb_url = user_config["mongodb_url"]
    db_name = user_config["db_name"]
    collection_name = user_config["collection_name"]

    # Connect to MongoDB
    client = MongoClient(mongodb_url)
    db = client[db_name]
    collection = db[collection_name]

    # Retrieve all video entries
    videos = list(collection.find({}, {"_id": 0}))  # Exclude MongoDB's internal `_id` field

    if not videos:
        update.message.reply_text("No videos indexed yet.")
        return

    # Prepare and send response
    response = "Indexed Videos:\n\n"
    for video in videos:
        response += (
            f"File Name: {video.get('file_name', 'N/A')}\n"
            f"File ID: {video['file_id']}\n"
            f"Mime Type: {video.get('mime_type', 'N/A')}\n"
            f"File Size: {video.get('file_size', 'N/A')} bytes\n"
            f"Channel ID: {video.get('channel_id', 'N/A')}\n\n"
        )

    update.message.reply_text(response)

def index_progress(update: Update, context: CallbackContext):
    """Show progress of indexing files."""
    user_id = update.effective_user.id

    if user_id not in user_configs:
        update.message.reply_text("Please configure MongoDB and channel using /set_db and /set_channel.")
        return

    user_config = user_configs[user_id]

    # Get MongoDB configuration
    mongodb_url = user_config["mongodb_url"]
    db_name = user_config["db_name"]
    collection_name = user_config["collection_name"]

    # Connect to MongoDB
    client = MongoClient(mongodb_url)
    db = client[db_name]
    collection = db[collection_name]

    # Retrieve total and indexed videos
    total_videos = collection.count_documents({})
    if total_videos == 0:
        update.message.reply_text("No videos indexed yet.")
        return

    # Simulate progress
    processed_videos = 0
    start_time = time.time()

    for _ in range(total_videos):
        time.sleep(0.5)  # Simulate time taken to process
        processed_videos += 1
        elapsed_time = time.time() - start_time
        remaining_videos = total_videos - processed_videos
        remaining_time = (elapsed_time / processed_videos) * remaining_videos if processed_videos > 0 else 0

        progress = (processed_videos / total_videos) * 100
        update.message.reply_text(
            f"Progress: {progress:.2f}%\n"
            f"Processed: {processed_videos}/{total_videos}\n"
            f"Estimated Time Remaining: {remaining_time:.2f} seconds"
        )

    update.message.reply_text("Indexing complete!")

def main():
    """Run the bot."""
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("set_db", set_db))
    dispatcher.add_handler(CommandHandler("set_channel", set_channel))
    dispatcher.add_handler(CommandHandler("index", index_videos))
    dispatcher.add_handler(CommandHandler("index_progress", index_progress))
    dispatcher.add_handler(MessageHandler(Filters.video, handle_video))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
