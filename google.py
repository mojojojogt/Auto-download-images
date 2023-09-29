import os
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from time import sleep
import concurrent.futures


# Dosya adındaki geçersiz karakterleri temizleyen fonksiyon
def clean_filename(filename):
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename

# Dizinleri oluşturan fonksiyon
def create_directories(parent_dir, folder_names):
    current_dir = parent_dir
    for folder_name in folder_names:
        current_dir = os.path.join(current_dir, folder_name)
        os.makedirs(current_dir, exist_ok=True)
    return current_dir

# Resimleri indiren fonksiyon
def download_images(query, image_limit, download_path):

    webDriver = webdriver.Chrome()
    webDriver.get("https://www.google.com/imghp?hl=en")

    # Arama kutusunu bulun ve sorguyu gönderin
    search_box = webDriver.find_element(By.NAME, "q")
    search_box.send_keys(query + Keys.ENTER)

    count = 0
    image_count = 0
    WebDriverWait(webDriver, 3).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
    images = webDriver.find_elements(By.XPATH, "//img[@class='rg_i Q4LuWd']")

    for image in images:
            image_count += 1

            if(image_count > image_limit):
                break

            image.click()
            bigImage = WebDriverWait(webDriver, 3).until(EC.visibility_of_element_located((By.XPATH, "//img[@class='r48jcc pT0Scc iPVvYb']")))
            image_url = bigImage.get_attribute("src")
            if image_url:
                executor.submit(download_image, image_url, query, image_count, download_path)

    webDriver.quit()


def download_image(image_url, query, image_count, download_path):
    response = requests.get(image_url, allow_redirects=True, timeout=10)
    if response.status_code == 200:
        cleaned_query = clean_filename(query)
        with open(os.path.join(download_path, f"{cleaned_query}_{image_count}.jpg"), "wb") as file:
            file.write(response.content)

def write_to_csv(row):
    csv_row = ",".join(row)
    with open("error.csv", "a") as csv_file:
        csv_file.write(csv_row + "\n")


def main():
    with open('katalog.csv', 'r') as file:
        reader = csv.reader(file)
        next(reader)  # İlk satırı atla

        for row in reader:
            try:
                gender = row[0]
                mastercategory = row[1]
                subcategory = row[2]
                articletype = row[3]
                usage = row[4]
                color = row[5]
                result = row[6]  # 7. sütunu al

                # İndirilen görselleri kaydetmek için dizin yolu oluştur
                parent_dir = "C:/git/Auto-download-images/image"
                folder_names = [gender, mastercategory, subcategory, articletype, usage, color]
                download_path = create_directories(parent_dir, folder_names)

                # Görselleri indir ve kaydet
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    #download_images(result, 5, download_path)
                    executor.submit(download_images, result, 5, download_path)
                    print("Dizinler oluşturuldu ve görseller kaydedildi:", download_path)

            except Exception as e:
                print(f"error: {str(e)}")
                write_to_csv(row)


if __name__ == "__main__":
    main()