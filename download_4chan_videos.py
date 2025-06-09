import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import re
import string


def sanitize_title(title):
    """
    Sanitize the thread title so it's safe to use as a folder name.
    This removes characters that are invalid for file/folder names.
    """
    valid_chars = string.ascii_letters + string.digits + " _-"
    sanitized_title = ''.join(c if c in valid_chars else "_" for c in title)
    return sanitized_title


def download_video(video_url, output_dir):
    try:
        video_name = video_url.split("/")[-1]
        output_path = os.path.join(output_dir, video_name)

        # Check if the video file already exists
        if os.path.exists(output_path):
            print(f"Video {video_name} already exists, skipping download.")
            return
        
        print(f"Downloading video from: {video_url}")
        response = requests.get(video_url, stream=True)
        
        # Download the video only if it doesn't exist
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        
        print(f"Successfully downloaded: {video_name}")
    except Exception as e:
        print(f"Failed to download video from {video_url}: {str(e)}")


def get_video_urls(thread_url, driver):
    driver.get(thread_url)
    time.sleep(random.uniform(2, 4))  # Random sleep to mimic human behavior
    
    # Get the page source and parse it using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Base URL for relative links
    base_url = "https://i.4cdn.org/"
    
    # Find all video links (both mp4 and webm)
    video_urls = set()  # Use a set to avoid duplicate URLs
    for video_tag in soup.find_all('a', {'href': True}):
        video_url = video_tag['href']
        # Check if the URL ends with either .mp4 or .webm
        if video_url.endswith(".mp4") or video_url.endswith(".webm"):
            # If the URL is relative, prepend the base URL
            if video_url.startswith("//"):
                video_url = "https:" + video_url
            video_urls.add(video_url)  # Add to the set to avoid duplicates
    
    return list(video_urls)


def get_thread_title(thread_url, driver):
    driver.get(thread_url)
    time.sleep(random.uniform(2, 4))  # Random sleep to mimic human behavior
    
    # Get the page source and parse it using BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Find the title of the thread, which is typically in the <title> tag
    title_tag = soup.find('title')
    if title_tag:
        # Extract the part between the first and second '-'
        title = title_tag.get_text()
        parts = title.split(" - ")
        
        # The second part is usually the actual thread title
        if len(parts) > 1:
            thread_title = parts[1]
        else:
            thread_title = title  # Fallback if the format is unexpected
        
        return sanitize_title(thread_title)  # Return sanitized title for folder name
    
    return "Untitled"  # Fallback if title isn't found


def main():
    # Setup the webdriver options (non-headless mode)
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    # Initialize the webdriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Read URLs from the file
    input_file = "thread_urls.txt"  # Updated the filename here
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} does not exist.")
        return
    
    with open(input_file, 'r') as file:
        thread_urls = file.readlines()

    # Remove any extra spaces or newlines
    thread_urls = [url.strip() for url in thread_urls if url.strip()]
    
    # Output base directory to save videos
    base_output_dir = "downloads"
    os.makedirs(base_output_dir, exist_ok=True)

    # Process each thread
    for idx, thread_url in enumerate(thread_urls, 1):
        print(f"\nProcessing thread {idx}/{len(thread_urls)}: {thread_url}")
        
        # Get the title of the thread and sanitize it for a valid folder name
        thread_title = get_thread_title(thread_url, driver)
        
        # Ensure the thread title is used as the folder name inside the 'downloads' directory
        thread_output_dir = os.path.join(base_output_dir, thread_title)
        os.makedirs(thread_output_dir, exist_ok=True)
        
        video_urls = get_video_urls(thread_url, driver)
        
        if video_urls:
            print(f"Found {len(video_urls)} video(s) to download.")
            for video_url in video_urls:
                download_video(video_url, thread_output_dir)
                # Random interval between downloads
                time.sleep(random.uniform(2, 5))  # Random sleep between 5-10 seconds
        else:
            print(f"No videos found in thread {thread_url}.")
        
        # Random interval between threads to avoid rate limiting
        time.sleep(random.uniform(5, 22))  # Random sleep between 10-20 seconds

    print("\nAll threads processed.")
    driver.quit()


if __name__ == "__main__":
    main()

