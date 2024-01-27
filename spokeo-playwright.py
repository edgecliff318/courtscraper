from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync , stealth_async


# extract info from the page of a single person
def extract_info(page, link):
    page.goto(link)
    page.wait_for_load_state()
    # get name
    name = page.query_selector('.e1ndw42t0').inner_text()
    # get age
    age = page.query_selector('.e1ndw42t1').inner_text()
    # get location
    location = page.query_selector('.e1ndw42t2').inner_text()
    # get phone number
    phone_number = page.query_selector('.e1ndw42t3').inner_text()
    # get email
    return {
        "name": name,
        "age": age,
        "location": location,
        "phone_number": phone_number
    }
    

    


#search_person("Samama", "Mahmud", token)
def search_person(page, firstName, lastName, middleName="", city=None, state=None):
    page.goto("https://www.spokeo.com/")
    q = f"{firstName} {middleName} {lastName}"
    page.fill('input[name="q"]', q)
    page.click('button:has-text("Search Now")')
    page.wait_for_load_state()
    # select all .e1ndw42t0
    link_elements = page.query_selector_all('.e1ndw42t0')
    links = [
        link_element.get_attribute('href')
        for link_element in link_elements
    ]
    return links


    
    


def run(playwright):
    print("Playwright offers a straightforward and simple approach.")
    email = "Shawn@tickettakedown.com"
    password = "?XCcFLCrhr3uQg@"
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    stealth_sync(page)
    page.goto('https://www.spokeo.com/login')
    page.wait_for_load_state("load")

    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button:has-text("LOGIN")')
    page.wait_for_load_state()
    search_person(
        page,
        "Samama",
        "Mahmud"
    )
    print(page.title())
    browser.close()

with sync_playwright() as playwright:
    run(playwright)