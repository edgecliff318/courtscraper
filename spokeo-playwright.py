from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync , stealth_async


# extract info from the page of a single person
def extract_info(page):
    container = page.query_selector('.e1usz6i03')
    phone_number = container.query_selector('#phone-number-content').inner_text()
    
    return phone_number
    

    


#search_person("Samama", "Mahmud", token)
def search_person(page, firstName, lastName, middleName="", city=None, state=None):
    page.goto("https://www.spokeo.com/")
    # q = f"{firstName} {middleName} {lastName}"
    firstName = "Samama"
    lastName = "Mahmud"
    middleName = "B"
    # https://www.spokeo.com/Samama-Mahmud?middle_name=B
    url = f"https://www.spokeo.com/{firstName}-{lastName}?middle_name={middleName}"
    page.goto(url)
    l = "https://www.spokeo.com/Samama-Mahmud/Wisconsin/Milwaukee/p2015111502099087352946730813837"
    
    link_elements = page.query_selector_all('.e1ndw42t0')
    links = [
        link_element.get_attribute('href')
        for link_element in link_elements
    ]
    return links


def login(page,context, email, password):
    page.goto('https://www.spokeo.com/login')
    
    page.click('input[name="password"]')
    page.fill('input[name="password"]', password)
    #clcik inside the input box
    page.click('input[name="email"]')
    page.fill('input[name="email"]', email)
    
    
    stealth_sync(page)
    page.wait_for_selector('button:has-text("LOGIN")', state="visible")

    page.click('button:has-text("LOGIN")')
    page.wait_for_load_state()
    state = context.storage_state()
    import os
    os.makedirs('playwright/.auth', exist_ok=True)
    with open('playwright/.auth/state.json', 'w') as f:
        f.write(state)
    return page
    
    


def run(playwright):
    print("Playwright offers a straightforward and simple approach.")
    email = "Shawn@tickettakedown.com"
    password = "?XCcFLCrhr3uQg@"
    browser = playwright.chromium.launch(headless=False)
    # context =  browser.new_context(storage_state='state.json')
    #check if there is a saved state
    import os
    os.makedirs('playwright/.auth', exist_ok=True)
    if os.path.exists('playwright/.auth/state.json'):
        # with open('', 'r') as f:
        #     state = f.read()
        context = browser.new_context(storage_state="playwright/.auth/state.json")
        page = context.new_page()

    else:
        context =  browser.new_context()
        page =  context.new_page()
        page = login(page, context, email, password)


    print(page.title())
    ## save state
    search_person(
        page,
        "Samama",
        "Mahmud"
    )
    print(page.title())
    browser.close()

with sync_playwright() as playwright:
    run(playwright)