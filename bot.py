from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from db_handler import DBHandler
from config import BOT_TOKEN
import time

# User-specific configurations (stored in memory)
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

async def handle_video(update: Update, context: CallbackContext):
    """Handle video file uploads."""
    if not update.effective_user:
        await update.message.reply_text("User not identified. Only user messages are allowed.")
        return

    user_id = update.effective_user.id

    if user_id not in user_configs:
        await update.message.reply_text("Please configure MongoDB and channel using /set_db and /set_channel.")
        return

    user_config = user_configs[user_id]

    video = update.message.video
    if not video:
        await update.message.reply_text("Please send a video file.")
        return

    # Initialize DBHandler with user configuration
    db_handler = DBHandler(user_config["mongodb_url"], user_config["db_name"], user_config["collection_name"])

    # Check for duplicates
    if db_handler.is_duplicate(video.file_unique_id):
        await update.message.reply_text(f"Duplicate file skipped: {video.file_name or 'Unnamed Video'}")
        return

    # Index video metadata to MongoDB
    video_data = {
        "file_id": video.file_id,
        "file_unique_id": video.file_unique_id,
        "file_name": video.file_name,
        "mime_type": video.mime_type,
        "file_size": video.file_size,
        "channel_id": user_config.get("channel_id"),
    }
    db_handler.add_video(video_data)

    await update.message.reply_text(f"Video indexed to MongoDB with ID: {video.file_id}")
    
def index_videos(update: Update, context: CallbackContext):
    """Retrieve all indexed videos from the database."""
    user_id = update.effective_user.id

    if user_id not in user_configs:
        update.message.reply_text("Please configure MongoDB and channel using /set_db and /set_channel.")
        return

    user_config = user_configs[user_id]
    db_handler = DBHandler(user_config["mongodb_url"], user_config["db_name"], user_config["collection_name"])

    videos = db_handler.get_all_videos()
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

def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_db", set_db))
    application.add_handler(CommandHandler("set_channel", set_channel))
    application.add_handler(CommandHandler("index", index_videos))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
