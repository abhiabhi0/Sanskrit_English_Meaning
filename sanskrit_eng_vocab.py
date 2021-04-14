import pandas as pd
from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
from selenium.common.exceptions import NoSuchElementException
import time 

chrome_options = Options()
chrome_options.add_argument("no-sandbox")
chrome_options.add_argument("headless")
chrome_options.add_argument("start-maximized")
chrome_options.add_argument("window-size=1900,1080")
chrome_options.add_argument("--user-data-dir=chrome-data")

SANSKRIT_COL = 0
MEANING_COL  = 3

def clean_text(text):
    return " ".join(text.get_text().split()).strip()

def scrape_row(row):
    column = row.find_all('td')

    sanskrit = clean_text(column[SANSKRIT_COL])
    english = clean_text(column[MEANING_COL])

    return sanskrit, english

def eng_meaning(word, driver, exception_status):
	"""
	returns english meaning of the sanskrit word passed
	"""
	print("Processing -", word)
	meanings = []

	try:
		#find text box where we enter the word
		text_box = driver.find_element_by_id("tran_input")		

		#enter word in the text box
		text_box.clear()
		text_box.send_keys(word)

		#clicking translate button
		buttons = driver.find_elements_by_tag_name("button")
		buttons[-1].click()

		html_page = driver.page_source
		#parse html page
		soup = BeautifulSoup(html_page, 'html.parser')
		#find table which holds meaning
		table = soup.body.find('table', attrs={'class':'table0 bgcolor0'})

		table_body = table.find('tbody')

		#find rows of table which holds meaning
		rows = table_body.find_all('tr')

		for row in rows:
			sanskrit, english = scrape_row(row)
			meanings.append([sanskrit, english])


	except(AttributeError) as e:
		print(e)
		print("no meanings found for", word)

	except(Exception) as e:
		exception_status = True
		print(e)
	
	finally:
		if len(meanings) != 0:
			print("meanings found for", word)
		return meanings, exception_status

def remove_puntuactions(lst):
	"""
	Remove puntuactions word from the list
	"""
	puntuactions = ['|', ',', '"', '\'', ':', ';', '-', '!', ' ', '?', '||']
	for item in puntuactions:
		if item in lst:
			lst.remove(item)
	return lst

def remove_duplicates(file_name):
	"""
	Remove duplicate word from the file
	"""
	unique_words = []
	
	with open(file_name, 'r') as file:
		for line in file:
			[unique_words.append(word) for word in line.split() if word not in unique_words]

	unique_words = remove_puntuactions(unique_words)
	return unique_words


def eng_translation(file_name_r, file_name_w, driver, url):
	"""
	Read sanskrit text file  and find english meaning of each word
	"""
	try:

		words_meanings = []

		words = remove_duplicates(file_name_r)
		est_time = len(words)*132
		est_time = est_time / 60
		print("Estimated time (in minutes):", est_time)
		for word in words:	
			exception_status = False	
			meanings, exception_status = eng_meaning(word, driver, exception_status)
			if exception_status:
				driver.get(url)
			
			if meanings:
				words_meanings.extend(meanings)
				words_meanings.extend([['/////'], ['/////'], ['/////'], ['/////']])
	
		meanings_df = pd.DataFrame(words_meanings)

		meanings_df.to_csv(file_name_w, index=False, header=False)
		
	except(KeyboardInterrupt) as e:
		print(e)
		meanings_df = pd.DataFrame(words_meanings)
		meanings_df.to_csv(file_name_w, index=False, header=False)
		print("File saved")

def main():
	file_name_r = "data1.txt"
	file_name_w = input("Enter output file name (add '.csv' after the name of file) - ")
	url = 'https://www.learnsanskrit.cc/index.php?mode=3&direct=au&script=hk&tran_input='
	driver = webdriver.Chrome(options=chrome_options, executable_path="/usr/bin/chromedriver")
	driver.get(url)
	eng_translation(file_name_r, file_name_w, driver, url)
	driver.quit()

if __name__ == "__main__":
    main()
