from selenium.common.exceptions import NoSuchElementException
import os
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep, strftime
import random


from selenium import webdriver

driver = webdriver.Chrome()
all_runners_data = []
BATCH_SIZE = 3
CSV_FILENAME = 'runners_data.csv'


def scrape_runner(faq_category, pagenum):
    runner_data = {}
    driver.get('https://www.beachcomberhottubs.com/knowledge-base/{faq_category}/?p={pagenum}'.format(
        faq_category=faq_category, pagenum=pagenum))
    title = driver.title
    # Sleeps for a random time between 2 and 5 seconds.
    sleep_time = random.uniform(2, 5)
    sleep(sleep_time)

    html = driver.page_source
    try:
        # Find name and starting number
        name_text = driver.find_element_by_xpath('//div[@class = "name mb4"]')
        parts = name_text.text.split(' ', 1)
        runner_data['starting_number'] = parts[0].replace(
            '#', '').replace(':', '')
        runner_data['name'] = parts[1]

        print(runner_data['starting_number'])

        # Find nation
        nation_text = driver.find_element_by_xpath(
            '//span[@class = "value b dtc pl2 w-50 svelte-1llqdsx"]')
        runner_data['nation'] = nation_text.text
        print(runner_data['nation'])

        # Find Team, Gender and AgeGroup
        team_and_gender_and_age_group = driver.find_elements_by_xpath(
            '//span[@class = "value b dtc pl2 svelte-1llqdsx"]')
        runner_data['team'] = team_and_gender_and_age_group[0].text
        try:
            gender_and_age_group_text = team_and_gender_and_age_group[1].text
            parts = gender_and_age_group_text.split(' ')
            gender_map = {'Mænd': 'M', 'Kvinder': 'F'}
            runner_data['gender'] = gender_map.get(parts[0], 'Unknown')
            runner_data['age_group'] = parts[1]
        # Catching both potential IndexError and other exceptions for safety
        except (IndexError, Exception):
            runner_data['gender'] = 'Unknown'
            runner_data['age_group'] = 'Unknown'

        print(runner_data['gender'])
        print(runner_data['age_group'])
        print(runner_data['team'])

        # Find total time
        total_time_text = driver.find_element_by_xpath(
            '//div[@class = "f1 tc b"]')
        runner_data['total_time'] = total_time_text.text
        print(runner_data['total_time'])

        # Find distance, average pace, overall place, gender place, class place
        five_values = driver.find_elements_by_xpath('//div[@class = "f3 b"]')
        runner_data['distance'] = five_values[0].text
        runner_data['average_pace'] = five_values[1].text
        runner_data['overall_place'] = five_values[2].text
        runner_data['gender_place'] = five_values[3].text
        runner_data['class_place'] = five_values[4].text
        print('distance: ' + runner_data['distance'])
        print('average pace: ' + runner_data['average_pace'])
        print('overall place: ' + runner_data['overall_place'])
        print('gender place: ' + runner_data['gender_place'])
        print('class place: ' + runner_data['class_place'])

        try:
            # Find split times (Maybe store in another CSV file)
            split_times_df_list = pd.read_html(
                html, attrs={'class': 'splits bg-contrast white w-100 tc collapse f6'})
            split_times_df = split_times_df_list[0]
            split_times_df = split_times_df.drop(0)

            split_data = {}

            # Initialize empty dictionaries for each split
            split_data = {"split5k": "", "split10k": "",
                          "split15k": "", "split20k": "", "split21097k": ""}

            for index, row in split_times_df.iterrows():
                split_name = f'split{row[0].replace(" km", "k").replace(".", "")}'
                split_time = row[2]
                split_data[split_name] = split_time
            runner_data.update(split_data)
            all_runners_data.append(runner_data)

        except ValueError:
            all_runners_data.append(runner_data)
            print(
                f"No table found for runner {starting_number}. Ignoring split times.")

    except NoSuchElementException:
        print(
            f"No details found for runner {starting_number}, skipping to next runner.")


def save_to_csv(batch_data):
    # Check if file exists to decide mode
    mode = 'a' if os.path.exists(CSV_FILENAME) else 'w'
    df = pd.DataFrame(batch_data)
    df.to_csv(CSV_FILENAME, mode=mode, header=(
        not os.path.exists(CSV_FILENAME)), index=False)


def run_scraper():
    # To keep track of current batch data
    batch_data = []
    for i in range(3159, 27000):
        scrape_runner(i)
        # Assuming all_runners_data gets updated in scrape_runner
        batch_data.append(all_runners_data[-1])
        if i % BATCH_SIZE == 0:
            save_to_csv(batch_data)
            batch_data.clear()  # Clearing current batch data
    # Save any remaining data
    if batch_data:
        save_to_csv(batch_data)


run_scraper()