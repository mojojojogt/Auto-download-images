from selenium.webdriver.chrome.options import Options
from concurrent.futures import ThreadPoolExecutor
from GoogleImageScraper import GoogleImageScraper
import os
import csv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def create_directories(parent_dir, *folder_names):
    current_dir = parent_dir
    for folder_name in folder_names:
        current_dir = os.path.join(current_dir, folder_name)
        if not os.path.exists(current_dir):
            os.makedirs(current_dir)
            print("Created directory:", current_dir)
    return current_dir


def worker_thread(row, driver):
    try:
        download_directory = "image"
        gender, master_category, sub_category, article_type, usage, color, query = row[:7]

        image_path = create_directories(download_directory, gender, master_category, sub_category, article_type, usage,
                                        color)

        image_scraper = GoogleImageScraper(
            row,
            driver,
            image_path,
            query,
            number_of_images,
            headless,
            min_resolution,
            max_resolution,
            max_missed)
        image_urls = image_scraper.find_image_urls()
        image_scraper.save_images(image_urls, keep_filenames)

        # Release resources
        del image_scraper
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    # Define file path
    csv_file_path = "katalog.csv"

    # Parameters
    number_of_images = 10  # Desired number of images
    headless = True  # True = No Chrome GUI
    min_resolution = (0, 0)  # Minimum desired image resolution
    max_resolution = (9999, 9999)  # Maximum desired image resolution
    max_missed = 5  # Max number of failed images before exit
    number_of_workers = 4  # Number of "workers" used
    keep_filenames = False  # Keep original URL image filenames

    try:
        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header row

            with ThreadPoolExecutor(max_workers=number_of_workers) as executor:
                for row in csv_reader:
                    # try going to www.google.com
                    options = Options()
                    #options.add_argument('--headless')
                    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
                    executor.submit(worker_thread, row, driver)

    except Exception as e:
        print(str(e))
