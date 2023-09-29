import concurrent.futures
from GoogleImageScraper import GoogleImageScraper, image_scraper
import os
import csv
import time

from concurrent.futures import ThreadPoolExecutor


def create_directories(parent_dir, *folder_names):
    current_dir = parent_dir
    for folder_name in folder_names:
        current_dir = os.path.join(current_dir, folder_name)
        if not os.path.exists(current_dir):
            os.makedirs(current_dir)
            print("Created directory:", current_dir)
    return current_dir

def process_csv_row(row):

    webdriver_path = "chromedriver.exe"
    number_of_images = image_limit                # Desired number of images
    headless = False                     # True = No Chrome GUI
    min_resolution = (0, 0)             # Minimum desired image resolution
    max_resolution = (9999, 9999)       # Maximum desired image resolution
    max_missed = 10                     # Max number of failed images before exit
    keep_filenames = False              # Keep original URL image filenames

    gender, master_category, sub_category, article_type, usage, color, query = row[:7]
    download_path = create_directories(download_directory, gender, master_category, sub_category, article_type, usage,
                                       color)

    scraper = image_scraper()
    images = scraper.download(query=query, limit=image_limit)
    print(images)

def main():
    global download_directory
    global image_limit
    global timestamp
    global error_limit

    csv_file_path = "katalog.csv"
    download_directory = "image"
    timestamp = time.strftime("%Y%m%d%H%M%S")  # Generate a timestamp
    image_limit = 20
    error_limit = 5
    browser_count = 1

    try:
        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header row

            with ThreadPoolExecutor(max_workers=browser_count) as executor:
                for row in csv_reader:
                    executor.submit(process_csv_row, row)

    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()
