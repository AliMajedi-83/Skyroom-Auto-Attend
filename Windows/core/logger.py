import logging
import os

# ساخت پوشه logs اگر وجود نداشت
if not os.path.exists("logs"):
    os.makedirs("logs")

# تنظیمات اصلی سیستم لاگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [%(levelname)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/app.log", encoding='utf-8'),  # ذخیره دائم در فایل
        logging.StreamHandler()  # نمایش زنده در ترمینال (مثل پرینت)
    ]
)

# یک آبجکت عمومی که بقیه فایل‌ها از آن استفاده می‌کنند
app_logger = logging.getLogger("SkyroomBot")
