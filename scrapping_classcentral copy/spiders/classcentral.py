import re
from scrapy.http import Request
import scrapy
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from tqdm import tqdm
import json

cs_subjects = [
    ("Artificial Intelligence", "/subject/ai"),
    ("Algorithms and Data Structures", "/subject/algorithms-and-data-structures"),
    ("Internet of Things", "/subject/internet-of-things"),
    ("Information Technology", "/subject/information-technology"),
    ("Computer Networking", "/subject/computer-networking"),
    ("Machine Learning", "/subject/machine-learning"),
    ("DevOps", "/subject/devops"),
    ("Deep Learning", "/subject/deep-learning"),
    ("Cryptography", "/subject/cryptography"),
    ("Quantum Computing", "/subject/quantum-computing"),
    ("Human-Computer Interaction (HCI)", "/subject/hci"),
    ("Distributed Systems", "/subject/distributed-systems"),
    ("Blockchain Development", "/subject/blockchain"),
    ("Operating Systems", "/subject/operating-systems"),
    ("Computer Graphics", "/subject/computer-graphics"),
    ("Automata Theory", "/subject/automata"),
    ("Compilers", "/subject/compilers"),
    ("SCADA", "/subject/scada"),
    ("Mainframe", "/subject/mainframe"),
    ("Digital Image Processing", "/subject/digital-image-processing"),
    ("View all Computer Science", "/subject/cs"),
    ("Cybersecurity", "/subject/cybersecurity"),
    ("Network Security", "/subject/network-security"),
    ("Ethical Hacking", "/subject/ethical-hacking"),
    ("Digital Forensics", "/subject/digital-forensics"),
    ("Reverse Engineering", "/subject/reverse-engineering"),
    ("Penetration Testing", "/subject/pentesting"),
    ("Malware Analysis", "/subject/malware-analysis"),
    ("DevSecOps", "/subject/devsecops"),
    ("OSINT (Open Source Intelligence)", "/subject/osint"),
    ("Threat Intelligence", "/subject/threat-intelligence"),
    ("Red Team", "/subject/red-team"),
    ("Blue Team", "/subject/blue-team"),
    ("View all Information Security (InfoSec)", "/subject/infosec"),
    ("Web Development", "/subject/web-development"),
    ("Mobile Development", "/subject/mobile-development"),
    ("Software Development", "/subject/software-development"),
    ("Game Development", "/subject/game-development"),
    ("Programming Languages", "/subject/programming-languages"),
    ("Cloud Computing", "/subject/cloud-computing"),
    ("Domain-Specific Languages (DSL)", "/subject/domain-specific-languages-dsl"),
    ("Aspect-oriented programming", "/subject/aspect-oriented-programming"),
    ("Object-oriented programming", "/subject/object-oriented-programming"),
    ("Visual Programming", "/subject/visual-programming"),
    ("Competitive Programming", "/subject/competitive-programming"),
    ("Database Programming", "/subject/database-programming"),
    ("Generic Programming", "/subject/generic-programming"),
    ("Programming Language Development", "/subject/programming-language-development"),
    ("Leetcode", "/subject/leetcode"),
    ("GNU Toolchain", "/subject/gnu-toolchain"),
    ("View all Programming", "/subject/programming-and-software-development"),
    ("Databases", "/subject/databases"),
    ("Information Retrieval", "/subject/information-retrieval"),
    ("Data Processing", "/subject/data-processing"),
    ("Data Wrangling", "/subject/data-wrangling"),
    ("Data Extraction", "/subject/data-extraction"),
    ("Data Manipulation", "/subject/data-manipulation"),
    ("View all Data Science", "/subject/data-science"),
]


class ClasscentralSpider(scrapy.Spider):
    name = "classcentral"
    allowed_domains = ["classcentral.com"]
    start_urls = ["https://www.classcentral.com/subjects"]

    def parse(self, response):
        # Your existing parse method to iterate over subjects
        if response.status == 200:
            self.logger.info("Scraping all subjects from: %s", response.url)
            for title, link in tqdm(cs_subjects, total=len(cs_subjects)):
                abs_subject_url = response.urljoin(link)
                yield Request(
                    abs_subject_url,
                    callback=self.parse_subject,
                    meta={"subject_title": title},
                )
        else:
            self.logger.error(
                f"Failed to fetch page: {response.url} with status {response.status}"
            )

    def parse_subject(self, response):
        subject_title = response.meta.get("subject_title", "Unknown Subject")
        self.logger.info(
            f"Scraping courses for subject: {subject_title} from {response.url}"
        )

        # Initialize Selenium WebDriver here
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        driver_path = "F:\chromedriver.exe"  # Update the path as per your system
        browser_path = "C:\Program Files\Google\Chrome\Application\chrome.exe"
        chrome_options.binary_location = browser_path
        driver = webdriver.Chrome(
            chrome_options, service=webdriver.chrome.service.Service(driver_path)
        )

        driver.get(response.url)

        ignored_exceptions = (
            NoSuchElementException,
            StaleElementReferenceException,
        )
        wait = WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions)

        # Loop until all pages are loaded
        page_count = 0
        while True:
            try:
                element = wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//span[@class="hidden small-up-inline-block"]')
                    )
                )
                driver.execute_script("arguments[0].click();", element)
                page_count += 1
                self.logger.info(
                    f"{page_count} :Loading more courses...for subject {subject_title}"
                )
                # break
            except TimeoutException:
                self.logger.info("No more pages to load for subject: %s", subject_title)
                break

        # Once all the content is loaded, get the page source
        page_source = driver.page_source
        driver.quit()
        # Create a Scrapy response from Selenium's page source
        scrapy_response = scrapy.Selector(text=page_source)

        # Now use Scrapy selectors to parse the data
        for course in scrapy_response.css(
            ".row.vert-align-top.xlarge-up-nowrap.margin-bottom-xxsmall"
        ):
            course_info = {}

            # Extract course URL
            course_url = course.css(".course-name::attr(href)").get()
            course_info["course_url"] = (
                response.urljoin(course_url) if course_url else "N/A"
            )

            # Extract course name
            course_name = course.css("h2.weight-semi::text").get()
            course_info["course_name"] = course_name.strip() if course_name else "N/A"

            # Extract instructor or institution names
            instructor_names = course.css(
                'a[data-track-click="catalog_click"] .text-3::text'
            ).getall()
            instructor_names = [
                name.strip() for name in instructor_names if name.strip()
            ]
            course_info["instructor_name"] = (
                ", ".join(instructor_names) if instructor_names else "N/A"
            )

            # Extract course provider and additional attributes
            data_track_props = course.css(".course-name::attr(data-track-props)").get()
            if data_track_props:
                try:
                    data_track_props = data_track_props.replace("&quot;", '"').replace(
                        "&#039;", "'"
                    )
                    data_props = json.loads(data_track_props)
                    course_info["course_provider"] = data_props.get(
                        "course_provider", "N/A"
                    )
                    course_info["course_level"] = data_props.get("course_level", "N/A")
                    course_info["course_certificate"] = data_props.get(
                        "course_certificate", "N/A"
                    )
                    course_info["course_subject"] = data_props.get(
                        "course_subject", "N/A"
                    )
                    course_info["course_is_university"] = data_props.get(
                        "course_is_university", "N/A"
                    )
                    course_info["course_avg_rating"] = data_props.get(
                        "course_avg_rating", "N/A"
                    )
                    course_info["course_num_rating"] = data_props.get(
                        "course_num_rating", "N/A"
                    )
                    course_info["course_institution"] = data_props.get(
                        "course_institution", "N/A"
                    )
                    course_info["course_is_classroom"] = data_props.get(
                        "course_is_classroom", "N/A"
                    )
                    course_info["course_is_free"] = data_props.get(
                        "course_is_free", "N/A"
                    )
                    course_info["course_id"] = data_props.get("course_id", "N/A")
                    course_info["course_type"] = data_props.get("course_type", "N/A")
                except json.JSONDecodeError:
                    self.logger.error(
                        "Failed to decode data-track-props for course: %s",
                        course_name,
                    )
            else:
                course_info.update(
                    {
                        "course_provider": "N/A",
                        "course_level": "N/A",
                        "course_certificate": "N/A",
                        "course_subject": "N/A",
                        "course_is_university": "N/A",
                        "course_avg_rating": "N/A",
                        "course_num_rating": "N/A",
                        "course_institution": "N/A",
                        "course_is_classroom": "N/A",
                        "course_is_free": "N/A",
                        "course_id": "N/A",
                        "course_type": "N/A",
                    }
                )

            # Extract course description and other information
            description = course.css(".text-2.margin-bottom-xsmall a::text").get()
            course_info["description"] = description.strip() if description else "N/A"

            # Extract course image URL
            image_url = course.css(".cover.block::attr(src)").get()
            course_info["image_url"] = image_url.strip() if image_url else "N/A"

            # Extract course rating
            rating_elements = course.css(".cmpt-rating-medium i.icon-star")
            rating = len(rating_elements)
            course_info["rating"] = (
                f"{rating} out of 5 stars" if rating > 0 else "No rating available"
            )

            # Yield the course information
            yield course_info


class GameTheoryCourseSpider(scrapy.Spider):
    name = "classcentral2"
    allowed_domains = ["classcentral.com"]
    start_urls = ["https://www.classcentral.com/course/game-theory-1-308"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Extract course title
        title = response.xpath(
            '//h2[@class="course-collapsable-section-heading head-3 medium-up-hidden"]/text()'
        ).get()
        title = title.strip() if title else None

        # Extract course provider information
        provider = response.xpath('//a[@title="List of Coursera MOOCs"]/text()').get()
        provider = provider.strip() if provider else None

        # Extract full course description (targeting the expanded version)
        description = response.xpath(
            '//section[@id="1579390435-contents"]//div[contains(@class, "wysiwyg text-1 line-wide")]//text()'
        ).getall()
        description = " ".join([desc.strip() for desc in description]).strip()

        # Extract instructor(s)
        instructors = response.xpath(
            '//p[contains(text(), "Taught by")]/following-sibling::p/text()'
        ).getall()
        instructors = [instructor.strip() for instructor in instructors]

        # Extract course information like duration, effort, and rating
        duration = response.xpath(
            '//li[div/i[contains(@class, "icon-clock-charcoal")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        duration = duration.strip() if duration else None

        effort = response.xpath(
            '//li[div/span[contains(text(), "Duration & workload")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        effort = effort.strip() if effort else None

        rating = response.xpath('//span[@class="review-score-text"]/text()').get()
        rating = rating.strip() if rating else None

        # Extract pricing information
        pricing = response.xpath(
            '//li[div/i[contains(@class, "icon-dollar-charcoal")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        pricing = pricing.strip() if pricing else None

        # Extract course languages
        languages = response.xpath(
            '//li[div/i[contains(@class, "icon-language-charcoal")]]/div/a[@class="text-2 color-charcoal line-tight"]/text()'
        ).getall()
        languages = [language.strip() for language in languages]

        # Extract certificate availability
        certificate = response.xpath(
            '//li[div/i[contains(@class, "icon-credential-charcoal")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        certificate = certificate.strip() if certificate else None

        # Extract course sessions
        sessions = response.xpath(
            '//li[div/i[contains(@class, "icon-calendar-charcoal")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        sessions = sessions.strip() if sessions else None

        # Extract course level
        level = response.xpath(
            '//li[div/i[contains(@class, "icon-level-charcoal")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        level = level.strip() if level else None

        # Extract subtitles available
        subtitles = response.xpath(
            '//li[div/i[contains(@class, "icon-subtitles-charcoal")]]/div/span[@class="text-2 line-tight"]/text()'
        ).get()
        subtitles = (
            [subtitle.strip() for subtitle in subtitles.split(",")]
            if subtitles
            else None
        )

        # Extract related subjects tags
        related_subjects = response.xpath(
            '//a[@class="course-subject-link text-2 link-gray-underline with-icon"]/span/text()'
        ).getall()
        related_subjects = [subject.strip() for subject in related_subjects]

        # Extract "Go to Class" button link
        go_to_class_link = response.xpath(
            '//a[@id="btnProviderCoursePage"]/@href'
        ).get()
        go_to_class_link = go_to_class_link.strip() if go_to_class_link else None

        syllabus_items = response.xpath(
            '//section[@id="1164852544"]//div[@id="1164852544-contents"]//ul//li'
        )

        syllabus_content = []
        for item in syllabus_items:
            # Get the main text of each list item
            week_title = item.xpath(".//text()").get().strip()

            # Get any sub-items (if nested lists exist)
            sub_items = item.xpath(".//ul//li//text()").getall()

            # Clean up and store the content
            syllabus_content.append(
                {
                    "week": week_title,
                    "details": [sub_item.strip() for sub_item in sub_items],
                }
            )

        if syllabus_content:
            yield {"syllabus": syllabus_content}
        else:
            self.logger.info("No syllabus found")
            self.logger.info(response.body)

        # Print or yield the extracted information
        yield {
            "title": title,
            "provider": provider,
            "description": description,
            "instructors": instructors,
            "duration": duration,
            "effort": effort,
            "rating": rating,
            "pricing": pricing,
            "languages": languages,
            "certificate": certificate,
            "sessions": sessions,
            "level": level,
            "subtitles": subtitles,
            "related_subjects": related_subjects,
            "go_to_class_link": go_to_class_link,
            "syllabus": syllabus_content,
        }


# To run this spider, save it in a file (e.g., game_theory_spider.py) and use the following command in your terminal:
# scrapy runspider game_theory_spider.py -o output.json
# This will save the extracted data to output.json
