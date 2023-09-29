# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 13:01:02 2020

@author: OHyic
"""
# import selenium drivers
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urlparse
import os
import requests
import io
from PIL import Image
import threading  # Import the threading module

csv_lock = threading.Lock()

class GoogleImageScraper:

    def write_to_final_csv(self, row, image_path):
        filename = f"final.csv"
        csv_row = ",".join(row + [image_path])

        with csv_lock:
            with open(filename, "a") as csv_file:
                csv_file.write(csv_row + "\n")

    def __init__(self, row, driver, image_path, search_key="cat", number_of_images=1, headless=True,
                 min_resolution=(0, 0), max_resolution=(1920, 1080), max_missed=10):

        if (type(number_of_images) != int):
            print("[Error] Number of images must be integer value.")
            return
        if not os.path.exists(image_path):
            print("[INFO] Image path not found. Creating a new folder.")
            os.makedirs(image_path)

        for i in range(1):
            try:
                driver.set_window_size(1400, 1050)
                driver.get("https://www.google.com")
            except Exception as e:
                print("[ERROR]")

        self.driver = driver
        self.search_key = search_key
        self.number_of_images = number_of_images
        self.image_path = image_path
        self.url = "https://www.google.com/search?q=%s&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947" % (
            search_key)
        self.headless = headless
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.max_missed = max_missed
        self.timestamp = time.strftime("%Y%m%d%H%M%S")  # Generate a timestamp
        self.row = row
    def find_image_urls(self):
        print("[INFO] Gathering image links")
        self.driver.get(self.url)
        image_urls = []
        count = 0
        missed_count = 0
        indx_1 = 0
        indx_2 = 0
        search_string = '//*[@id="islrg"]/div[1]/div[%s]/a[1]/div[1]/img'
        time.sleep(3)
        while self.number_of_images > count and missed_count < self.max_missed:
            if indx_2 > 0:
                try:
                    imgurl = self.driver.find_element(By.XPATH, search_string % (indx_1, indx_2 + 1))
                    imgurl.click()
                    indx_2 = indx_2 + 1
                    missed_count = 0
                except Exception:
                    try:
                        imgurl = self.driver.find_element(By.XPATH, search_string % (indx_1 + 1, 1))
                        imgurl.click()
                        indx_2 = 1
                        indx_1 = indx_1 + 1
                    except:
                        indx_2 = indx_2 + 1
                        missed_count = missed_count + 1
            else:
                try:
                    imgurl = self.driver.find_element(By.XPATH, search_string % (indx_1 + 1))
                    imgurl.click()
                    missed_count = 0
                    indx_1 = indx_1 + 1
                except Exception:
                    try:
                        imgurl = self.driver.find_element(By.XPATH,
                                                          '//*[@id="islrg"]/div[1]/div[%s]/div[%s]/a[1]/div[1]/img' % (
                                                              indx_1, indx_2 + 1))
                        imgurl.click()
                        missed_count = 0
                        indx_2 = indx_2 + 1
                        search_string = '//*[@id="islrg"]/div[1]/div[%s]/div[%s]/a[1]/div[1]/img'
                    except Exception:
                        indx_1 = indx_1 + 1
                        missed_count = missed_count + 1

            try:
                # select image from the popup
                time.sleep(1)
                class_names = ["n3VNCb", "iPVvYb", "r48jcc", "pT0Scc"]
                images = [self.driver.find_elements(By.CLASS_NAME, class_name) for class_name in class_names if
                          len(self.driver.find_elements(By.CLASS_NAME, class_name)) != 0][0]
                for image in images:
                    # only download images that starts with http
                    src_link = image.get_attribute("src")
                    if (("http" in src_link) and (not "encrypted" in src_link)):
                        print(
                            f"[INFO] {self.search_key} \t #{count} \t {src_link}")
                        image_urls.append(src_link)
                        count += 1
                        break
            except Exception:
                print("[INFO] Unable to get link")

            try:
                # scroll page to load next image
                if (count % 3 == 0):
                    self.driver.execute_script("window.scrollTo(0, " + str(indx_1 * 60) + ");")
                element = self.driver.find_element(By.CLASS_NAME, "mye4qd")
                element.click()
                print("[INFO] Loading next page")
                time.sleep(3)
            except Exception:
                time.sleep(1)

        self.driver.quit()
        print("[INFO] Google search ended")
        return image_urls

    def save_images(self, image_urls, keep_filenames):
        print(keep_filenames)

        print("[INFO] Saving image, please wait...")
        for indx, image_url in enumerate(image_urls):
            try:
                print("[INFO] Image url:%s" % (image_url))
                search_string = ''.join(e for e in self.search_key if e.isalnum())
                image = requests.get(image_url, timeout=5)
                if image.status_code == 200:
                    with Image.open(io.BytesIO(image.content)) as image_from_web:
                        try:
                            if (keep_filenames):
                                # extact filename without extension from URL
                                o = urlparse(image_url)
                                image_url = o.scheme + "://" + o.netloc + o.path
                                name = os.path.splitext(os.path.basename(image_url))[0]
                                # join filename and extension
                                filename = "%s.%s" % (name, image_from_web.format.lower())
                            else:
                                filename = "%s%s.%s" % (search_string, str(indx), image_from_web.format.lower())

                            image_path = os.path.join(self.image_path, filename)
                            image_path_rel = os.path.relpath(os.path.join(self.image_path, filename))
                            print(
                                f"[INFO] {self.search_key} \t {indx} \t Image saved at: {image_path}")
                            image_from_web.save(image_path)
                            self.write_to_final_csv(self.row, image_path_rel)
                        except OSError:
                            rgb_im = image_from_web.convert('RGB')
                            rgb_im.save(image_path)
                        image_resolution = image_from_web.size
                        if image_resolution != None:
                            if image_resolution[0] < self.min_resolution[0] or image_resolution[1] < \
                                    self.min_resolution[1] or image_resolution[0] > self.max_resolution[0] or \
                                    image_resolution[1] > self.max_resolution[1]:
                                image_from_web.close()
                                os.remove(image_path)

                        image_from_web.close()
            except Exception as e:
                print("[ERROR] Download failed: ", e)
                pass
        print("--------------------------------------------------")
        print(
            "[INFO] Downloads completed. Please note that some photos were not downloaded as they were not in the correct format (e.g. jpg, jpeg, png)")
