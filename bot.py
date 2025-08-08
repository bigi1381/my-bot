import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import instaloader
import requests

TOKEN = "7756643728:AAFooZLIXgGty62BwokpeH8r1uBULqQt-og"
CHANNEL_ID = -1002763536821
CHANNEL_USERNAME = "@beautyshop_stor"

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"سلام {user.first_name}!\nلینک پست اینستاگرام را برای من بفرستید تا آن را دانلود کنم.")

def is_member(user_id):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
        response = requests.get(url).json()
        return response.get('result', {}).get('status') in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

def handle_message(update: Update, context: CallbackContext):
    if not is_member(update.effective_user.id):
        keyboard = [[InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        update.message.reply_text(
            '⚠️ برای استفاده از ربات، لطفاً در کانال ما عضو شوید:',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    url = update.message.text.strip()
    if 'instagram.com' not in url:
        update.message.reply_text("❌ لطفاً فقط لینک معتبر اینستاگرام ارسال کنید.")
        return

    try:
        # ایجاد پوشه downloads اگر وجود ندارد
        if not os.path.exists('downloads'):
            os.makedirs('downloads')

        L = instaloader.Instaloader(
            dirname_pattern='downloads',
            save_metadata=False,
            compress_json=False
        )
        
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        update.message.reply_text("⏳ در حال دانلود محتوا... لطفاً صبر کنید.")
        
        L.download_post(post, target='downloads')

        # ارسال فایل دانلود شده
        for file in os.listdir('downloads'):
            file_path = os.path.join('downloads', file)
            if file.endswith('.mp4'):
                with open(file_path, 'rb') as f:
                    update.message.reply_video(
                        video=f,
                        caption=f"✅ دانلود شده از {post.owner_username}",
                        supports_streaming=True
                    )
            elif file.endswith('.jpg'):
                with open(file_path, 'rb') as f:
                    update.message.reply_photo(
                        photo=f,
                        caption=f"✅ دانلود شده از {post.owner_username}"
                    )
            
            # حذف فایل پس از ارسال
            os.remove(file_path)
        
        # حذف پوشه خالی
        os.rmdir('downloads')

    except instaloader.exceptions.InvalidArgumentException:
        update.message.reply_text("❌ لینک وارد شده معتبر نیست.")
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        update.message.reply_text("❌ این پست خصوصی است و قابل دانلود نیست.")
    except Exception as e:
        update.message.reply_text(f"❌ خطا در دانلود محتوا: {str(e)}")
        # تمیز کردن فایل‌های احتمالی باقیمانده
        if os.path.exists('downloads'):
            for file in os.listdir('downloads'):
                os.remove(os.path.join('downloads', file))
            os.rmdir('downloads')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    updater.idle()

if name == 'main':
    main()
