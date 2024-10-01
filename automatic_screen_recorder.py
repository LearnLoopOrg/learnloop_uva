import time
import os
import json
import tkinter as tk
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pyautogui
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import subprocess
import threading


load_dotenv()

driver = None
json_file = "lectures.json"


# Configuraties voor Selenium om pop-ups te vermijden en automatisch in te loggen
def configure_driver():
    global driver
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-search-engine-choice-screen")

    prefs = {
        "credentials_enable_service": False,  # Zet de wachtwoordopslagservice uit
        "profile.password_manager_enabled": False,  # Zet de wachtwoordbeheerder uit
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Maak Chrome WebDriver aan met de juiste opties
    driver = webdriver.Chrome(options=chrome_options)
    return driver


# Functie om in te loggen
def login_to_portal(
    url, username=os.getenv("PANOPTO_USERNAME"), password=os.getenv("PANOPTO_PASSWORD")
):
    driver.get(url)

    # Stap 1: Klik op de eerste knop (de derde optie in de lijst)
    button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "#idp-picker > section.wayf__remainingIdps > ul > li:nth-child(3) > div",
            )
        )
    )
    button.click()

    # Stap 2: Vul gebruikersnaam in
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "userNameInput"))
    )
    username_field.send_keys(username)

    # Stap 3: Vul wachtwoord in
    password_field = driver.find_element(By.ID, "passwordInput")
    password_field.send_keys(password)

    # Stap 4: Klik op de inlogknop
    login_button = driver.find_element(By.ID, "submitButton")
    login_button.click()

    # Wacht tot de pagina volledig is geladen na het inloggen
    time.sleep(5)


def click_on_speed_options():
    try:
        # Stap 1: Klik op het snelheidsmenu (Snelheid)
        speed_menu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#captionSettings > div.MuiPaper-root.MuiPaper-elevation.MuiPaper-rounded.MuiPaper-elevation8.MuiPopover-paper.css-3axkta.css-mzwxm > ul > li:nth-child(1)",
                )
            )
        )
        speed_menu.click()  # Klik om het snelheidsmenu te openen
        print("Successfully clicked on speed menu")
    except Exception as e:
        print("Not able to click on speed menu: ", e)


def select_2x_speed_option():
    try:
        speed_option_2x = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='2x']"))
        )
        speed_option_2x.click()  # Klik op de 2x optie
        print("Successfully selected 2x speed option")

    except Exception as e:
        print("Not able to select speed option: ", e)


def click_on_sprocket():
    try:
        # Eerste poging om het tandwielpictogram te vinden met de eerste selector
        sprocket_icon = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#reactCaptionsSettingsButton > button > svg > path")
            )
        )
        sprocket_icon.click()  # Klik op het tandwielpictogram
    except Exception as e:
        print("First selector failed: ", e)
        try:
            # Tweede poging om het tandwielpictogram te vinden met de tweede selector
            sprocket_icon = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#reactCaptionsSettingsButton > button > svg")
                )
            )
            sprocket_icon.click()  # Klik op het tandwielpictogram
        except Exception as e:
            print("Both selectors failed: ", e)


def click_on_other_component():
    try:
        other_component = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "rootForm"))
        )
        other_component.click()
    except Exception as e:
        print("Not able to click on other component: ", e)


def double_click_right_side():
    try:
        # Bepaal de schermgrootte
        screen_width, screen_height = pyautogui.size()

        # Definieer de positie voor de dubbelklik (bijvoorbeeld 90% van de breedte en 50% van de hoogte)
        click_x = int(screen_width * 0.9)  # 90% van de breedte (rechts)
        click_y = int(screen_height * 0.5)  # 50% van de hoogte (midden van het scherm)

        # Beweeg de muis naar de positie en voer een dubbelklik uit
        pyautogui.moveTo(
            click_x, click_y, duration=1
        )  # Verplaats de muis langzaam naar de rechterkant
        pyautogui.doubleClick()  # Voer een dubbelklik uit

        print(f"Dubbelklik uitgevoerd op positie ({click_x}, {click_y})")
    except Exception as e:
        print(f"Fout bij het uitvoeren van de dubbelklik: {e}")


def load_lectures():
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            return json.load(f)
    else:
        return {"lectures": []}


def save_lectures(lectures):
    # return
    with open(json_file, "w") as f:
        json.dump(lectures, f, indent=4)


def check_for_new_lecture(url):
    driver.get(url)

    # Zoek naar de lecture rijen in de table
    lecture_rows = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "#listViewContainer .list-view-row")
        )
    )

    # Laad bestaande lectures uit het JSON-bestand
    lectures = load_lectures()
    lecture_list = lectures["lectures"]
    new_lectures = []

    # Loop door alle lectures en check voor nieuwe
    for row in lecture_rows:
        lecture_id = row.get_attribute("id")

        # Gebruik een generieke selector om de lecture name op te halen
        lecture_name = row.find_element(
            By.CSS_SELECTOR, "td.detail-cell > div.item-title.title-link > a > span"
        ).text

        # Gebruik get_attribute('href') om de link van het college op te halen
        lecture_link = row.find_element(
            By.CSS_SELECTOR, "td.detail-cell > div.item-title.title-link > a"
        ).get_attribute("href")

        # Controleer of het college al in de JSON staat
        if lecture_id not in [lecture["id"] for lecture in lecture_list]:
            print(f"Nieuw college gevonden: {lecture_name} ({lecture_id})")

            # Voeg nieuw college toe aan de lijst
            new_lecture = {
                "id": lecture_id,
                "name": lecture_name,
                "link": lecture_link,
            }
            new_lectures.append(new_lecture)
            lecture_list.append(new_lecture)

    # Als er nieuwe lectures zijn gevonden, sla ze op in het JSON-bestand
    if new_lectures:
        save_lectures(lectures)
        # Klik op de eerste nieuwe lecture om naar de video te navigeren
        driver.get(new_lectures[0]["link"])
        return new_lectures

    return False


def record_screen_and_audio(output_file, duration_in_seconds):
    try:
        # Definieer het FFmpeg commando voor scherm- en audio-opname
        ffmpeg_command = [
            "ffmpeg",
            "-y",  # Overschrijf bestaande bestanden zonder bevestiging
            "-f",
            "gdigrab",  # Gebruik gdigrab voor schermopname op Windows
            "-i",
            "desktop",  # De bron voor de video-opname is het scherm
            "-f",
            "dshow",  # Gebruik DirectShow voor audio-opname op Windows
            "-i",
            "audio=CABLE Output (VB-Audio Virtual Cable)",  # De bron voor de audio-opname (stel je opname-apparaat in)
            "-t",
            str(duration_in_seconds),  # De duur van de opname
            "-vcodec",
            "libx264",  # Gebruik H264 voor videocompressie
            "-acodec",
            "aac",  # Gebruik AAC voor audiocompressie
            output_file,  # Uitvoerbestand
        ]

        # Voer het FFmpeg commando uit
        print(f"Opname gestart: {output_file}")
        subprocess.run(ffmpeg_command, check=True)
        print(f"Opname voltooid en opgeslagen als: {output_file}")

    except subprocess.CalledProcessError as e:
        print(f"Fout bij opname: {e}")


def get_next_output_file():
    # Vind het hoogste nummer van bestaande opnames
    existing_files = [
        f
        for f in os.listdir()
        if f.startswith("lecture_recording_") and f.endswith(".mp4")
    ]
    if existing_files:
        latest_file = sorted(existing_files)[-1]
        number = int(latest_file.split("_")[-1].replace(".mp4", "")) + 1
    else:
        number = 1
    return f"lecture_recording_{number}.mp4"


def maximize_browser_window():
    try:
        driver.maximize_window()  # Maximaliseer het browservenster
        print("Browservenster gemaximaliseerd.")
        time.sleep(1)  # Wacht kort zodat het venster volledig in focus is
    except Exception as e:
        print(f"Fout bij het maximaliseren van het venster: {e}")


def press_space():
    try:
        video_element = driver.find_element(
            By.CSS_SELECTOR, "body"
        )  # Of kies een ander element, zoals de video
        video_element.send_keys(Keys.SPACE)  # Simuleer een spatiebalkdruk
        print("Spatiebalk gedrukt met Selenium.")
    except Exception as e:
        print(f"Fout bij het drukken op de spatiebalk met Selenium: {e}")


def get_remaining_time():
    try:
        # Zoek het element met de id 'timeRemaining'
        time_remaining_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "timeRemaining"))
        )

        # Haal de tekstwaarde van het element op, zoals "-1:49:59"
        time_remaining = time_remaining_element.text.strip()

        # Verwijder het voorvoegsel '-' als dat aanwezig is en split op de dubbele punt
        time_parts = time_remaining.replace("-", "").split(":")

        # Converteer de tijd naar seconden
        hours = int(time_parts[0]) * 3600
        minutes = int(time_parts[1]) * 60
        seconds = int(time_parts[2])

        total_seconds_remaining = hours + minutes + seconds

        return total_seconds_remaining
    except Exception as e:
        print(f"Fout bij het uitlezen van de resterende tijd: {e}")
        return None


def countdown_popup(check_interval):
    # Maak een nieuw tkinter-venster aan voor de popup
    popup = tk.Tk()
    popup.title("Geen nieuwe lectures gevonden")

    # Instellen dat het venster altijd bovenaan staat
    popup.attributes("-topmost", True)

    # Bereken het midden van het scherm en centreer de popup
    window_width = 600
    window_height = 100

    # Bepaal de schermgrootte
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()

    # Bereken de positie voor centreren
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)

    # Stel de afmetingen en positie van het venster in
    popup.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

    smiley = "😊"
    # Stel de countdown in
    countdown = check_interval
    label = ttk.Label(
        popup,
        text=f"Geen nieuwe lectures gevonden. Nieuwe check over {countdown} seconden. {smiley}",
    )
    label.pack(padx=20, pady=20)

    def update_label():
        nonlocal countdown
        for i in range(10):
            countdown -= 1
            label.config(
                text=f"Geen nieuwe lectures gevonden. Nieuwe check over {countdown} seconden. {smiley}"
            )
            time.sleep(1)  # Aftellen elke seconde
        popup.destroy()  # Sluit het venster na de countdown

    # Start het aftellen op een aparte thread zodat het niet de hoofdcode blokkeert
    threading.Thread(target=update_label).start()

    popup.mainloop()


def move_mouse_to_corner():
    try:
        # Bepaal de schermgrootte
        screen_width, screen_height = pyautogui.size()
        middle_left_y_position = screen_height // 2

        # Verplaats de muis naar een veilige hoek (bijvoorbeeld de linkerbovenhoek)
        pyautogui.moveTo(0, middle_left_y_position, duration=1)

        print("Muis verplaatst naar linksmidden.")
    except Exception as e:
        print(f"Fout bij het verplaatsen van de muis: {e}")


def main(url, check_interval):
    try:
        # Controleer of er een nieuw college is
        if new_lectures := check_for_new_lecture(url):
            for lecture in new_lectures:
                driver.get(lecture["link"])
                double_click_right_side()  # Of screen to go full screen

                # Klik op de snelheidsoptie voor 2x
                click_on_sprocket()
                click_on_speed_options()
                select_2x_speed_option()
                click_on_other_component()

                press_space()  # Play the video
                move_mouse_to_corner()  # Move the mouse to the corner of the screen
                output_file = get_next_output_file()

                # Bepaal de resterende tijd
                remaining_time = get_remaining_time()
                lecture_speed = 2  # x

                # Stel de opnametijd in
                time_to_record = remaining_time / lecture_speed  # seconden

                if remaining_time is not None:
                    print(f"Resterende tijd voor de opname: {remaining_time} seconden")

                    # Start de opname met de resterende tijd als duur
                    record_screen_and_audio(
                        output_file, duration_in_seconds=time_to_record
                    )
        else:
            countdown_popup(check_interval)
            print("Geen nieuwe colleges gevonden.")

    except Exception as e:
        print(f"Een fout is opgetreden: {e}")


def go_to_lecture_overview(url):
    configure_driver()
    # Log in op de portal
    login_to_portal(url)

    maximize_browser_window()


if __name__ == "__main__":
    url = "https://hva-uva.cloud.panopto.eu/Panopto/Pages/Sessions/List.aspx#folderID=%224b60e032-0636-4c6d-9e56-b1da00a353ff%22"
    go_to_lecture_overview(url)

    check_interval = 10  # aantal seconden tussen elke check

    while True:
        try:
            print("Starten van een nieuwe check...")
            main(url, check_interval)  # Geef de URL door aan main()
        except Exception as e:
            print(f"Een fout is opgetreden: {e}")

        print(f"{check_interval} seconden wachten tot volgende check...")
        time.sleep(check_interval)  # Wacht voor de volgende check
