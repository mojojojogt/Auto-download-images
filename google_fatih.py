import os
import csv
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import threading  # Import the threading module

# Define the lock for thread synchronization
csv_lock = threading.Lock()


def create_directories(parent_dir, *folder_names):
    current_dir = parent_dir
    for folder_name in folder_names:
        current_dir = os.path.join(current_dir, folder_name)
        if not os.path.exists(current_dir):
            os.makedirs(current_dir)
            print("Created directory:", current_dir)
    return current_dir


def create_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return chrome_options


def download_images(query, row, image_limit, download_path):
    # Create a headless Chrome WebDriver
    chrome_options = create_chrome_options()
    driver = webdriver.Chrome(chrome_options)
    image_count = 0
    error_count = 0

    try:
        driver.get(f"https://www.google.com/search?q={query}&tbm=isch")
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
        reject = driver.find_elements(By.XPATH, "//span[contains(text(), 'Reject all')]")
        if len(reject) > 0:
            reject[0].click()

        # Scroll down to load more images
        for _ in range(3):  # Adjust the number of scrolls as needed
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for images to load

        # Find and extract image URLs
        image_urls = []
        images = driver.find_elements(By.XPATH, "//img[@class='rg_i Q4LuWd']")

        for image in images:
            try:
                image_count = image_count + 1
                if image_count >= image_limit:
                    break

                image.click()
                WebDriverWait(driver, 10).until(
                    lambda d: d.find_element(By.XPATH, "//img[@class='r48jcc pT0Scc iPVvYb']")
                )
                big_image = driver.find_element(By.XPATH, "//img[@class='r48jcc pT0Scc iPVvYb']")
                image_url = big_image.get_attribute("src")

                download_image(image_url, query, row, image_count, download_path)
            except Exception as e:
                error_count += 1
                print("Error for single image:", str(e))

    except Exception as e:
        if error_count > image_limit/2:
            print("Error:", str(e))
            write_to_csv_error(row)

    finally:
        driver.quit()


def download_image(image_url, query, row, image_count, download_path):
    try:
        print(f"Downloading image {image_count} from URL: {image_url}")
        image_response = requests.get(image_url)
        image_bytes = image_response.content

        cleaned_query = clean_filename(query)
        file_path = os.path.join(download_path, f"{cleaned_query}_{image_count}.jpg")

        with open(file_path, "wb") as image_file:
            image_file.write(image_bytes)

        write_to_final_csv(row, file_path)

    except Exception as e:
        print("Error while downloading image:", str(e))


def clean_filename(filename):
    return "".join(c for c in filename if c.isalnum() or c.isspace())


def write_to_csv_error(row):
    filename = f"error_{timestamp}.csv"
    csv_row = ",".join(row)

    with csv_lock:
        with open(filename, "a") as csv_file:
            csv_file.write(csv_row + "\n")


def write_to_final_csv(row, image_path):
    filename = f"final_{timestamp}.csv"
    csv_row = ",".join(row + [image_path])

    with csv_lock:
        with open(filename, "a") as csv_file:
            csv_file.write(csv_row + "\n")


def process_csv_row(row):
    gender, master_category, sub_category, article_type, usage, color, query = row[:7]
    download_path = create_directories(download_directory, gender, master_category, sub_category, article_type, usage,
                                       color)
    download_images(query, row, image_limit, download_path)
    print("Directories created, and images downloaded:", download_path)


def main():
    global download_directory
    global image_limit
    global timestamp

    csv_file_path = "katalog.csv"
    download_directory = "image"
    timestamp = time.strftime("%Y%m%d%H%M%S")  # Generate a timestamp
    image_limit = 10
    browser_count = 1

    os.environ["webdriver.chrome.driver"] = "chromedriver.exe"

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
