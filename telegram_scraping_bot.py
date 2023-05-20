import telebot

import requests

from bs4 import BeautifulSoup

import pandas as pd

import re

import nltk

from nltk.corpus import stopwords

from nltk.stem import PorterStemmer

from sklearn.feature_extraction.text import CountVectorizer

import logging

import PyPDF2

from docx import Document

import os

# Configure the logging

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Telegram bot

bot = telebot.TeleBot("6158451123:AAFWNdYyUnGEbnsxWTZWUAQfrcWmbgGkr_o")

# Welcome message

@bot.message_handler(commands=['start'])

def send_welcome(message):

    bot.reply_to(message, "Welcome to the Telegram Scraping Bot! Please enter the information you want to scrape.")

# Handling user input

@bot.message_handler(func=lambda message: True)

def handle_user_input(message):

    user_input = message.text

    

    # Join the desired groups/chats

    group_names = user_input.split(',')

    join_groups(group_names)

    

    # Download the desired files

    download_files(group_names)

    

    # Add user input to the end of 'user_input.txt'

    with open('user_input.txt', 'a') as f:

        f.write(user_input + '\n')

    

    # Scrape and process the downloaded files

    process_files(group_names)

    

    # Confirmation message

    bot.reply_to(message, "Data scraping and processing completed successfully!")

    

def join_groups(group_names):

    # Logic to join the desired groups/chats

    for group_name in group_names:

        try:

            bot.join_chat(group_name)

            logging.info(f"Joined {group_name} successfully!")  # Log successful join

        except Exception as e:

            logging.error(f"Unable to join {group_name}: {e}")  # Log join failure

def download_files(group_names):

    # Logic to download files from Telegram

    for group_name in group_names:

        try:

            # Retrieve the messages from the group

            messages = bot.get_chat_messages(group_name)

            

            # Iterate over the messages and download PDF files

            for message in messages:

                if message.content_type == 'document' and message.document.mime_type == 'application/pdf':

                    file_id = message.document.file_id

                    file_info = bot.get_file(file_id)

                    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

                    

                    # Download the PDF file

                    response = requests.get(file_url)

                    with open(f"downloaded_files/{file_id}.pdf", 'wb') as f:

                        f.write(response.content)

                    

                    logging.info(f"Downloaded file {file_id}.pdf successfully!")  # Log successful download

                elif message.content_type == 'document' and message.document.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':

                    file_id = message.document.file_id

                    file_info = bot.get_file(file_id)

                    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"

                    

                    # Download the Word document

                    response = requests.get(file_url)

                    with open(f"downloaded_files/{file_id}.docx", 'wb') as f:

                        f.write(response.content)

                    

                    logging.info(f"Downloaded file {file_id}.docx successfully!")  # Log successful download

        except Exception as e:

            logging.error(f"File download failed: {e}")  # Log download failure

def extract_data_from_pdf(file_path):

    with open(file_path, 'rb') as file:

        pdf_reader = PyPDF2.PdfFileReader(file)

        num_pages = pdf_reader.numPages

        extracted_text = ''

        for page_num in range(num_pages):

            page = pdf_reader.getPage(page_num)

            extracted_text += page.extract_text()

        return extracted_text

def extract_data_from_docx(file_path):

    document = Document(file_path)

    extracted_text = ''

    for para in document.paragraphs:

        extracted_text += para.text

    return extracted_text

def process_files(group_names):

    # Logic to process the downloaded files

    for group_name in group_names:

        try:

            # Retrieve the downloaded PDF and Word files

            file_list = [f"downloaded_files/{file_id}.pdf" for file_id in os.listdir("downloaded_files") if file_id.endswith(".pdf")]

            file_list.extend([f"downloaded_files/{file_id}.docx" for file_id in os.listdir("downloaded_files") if file_id.endswith(".docx")])

            

            # Extract data from PDF and Word files

            extracted_data = []

            for file_path in file_list:

                if file_path.endswith(".pdf"):

                    extracted_data.append(extract_data_from_pdf(file_path))

                elif file_path.endswith(".docx"):

                    extracted_data.append(extract_data_from_docx(file_path))

            

            # Preprocess the extracted data

            processed_data = preprocess_data(extracted_data)

            

            # Save processed data to JSON

            processed_data.to_json('processed_data.json', orient='records')

            

            logging.info("Data processing completed successfully!")  # Log successful data processing

        except Exception as e:

            logging.error(f"Data processing failed: {e}")  # Log data processing failure

def preprocess_data(data):

    # Logic to preprocess the extracted data

    df = pd.DataFrame({'text': data})

    

    # Perform data cleaning and preprocessing

    df['clean_text'] = df['text'].apply(lambda x: re.sub(r'\s+', ' ', x))  # Remove extra whitespaces

    df['clean_text'] = df['clean_text'].apply(lambda x: re.sub(r'\W+', ' ', x))  # Remove special characters

    df['clean_text'] = df['clean_text'].apply(lambda x: x.lower())  # Convert to lowercase

    

    # Perform tokenization, stop word removal, and stemming

    stop_words = set(stopwords.words('english'))

    stemmer = PorterStemmer()

    df['clean_text'] = df['clean_text'].apply(lambda x: nltk.word_tokenize(x))

    df['clean_text'] = df['clean_text'].apply(lambda x: [word for word in x if word not in stop_words])

    df['clean_text'] = df['clean_text'].apply(lambda x: [stemmer.stem(word) for word in x])

    

    return df

# Run the bot

bot.polling()
