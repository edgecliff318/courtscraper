import requests
import urllib3
import time

#urllib3.disable_warnings() # This is not good practice. Do we need it? https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
})

# service key for 2captcha
CAPTCHA_KEY = '3b5ee599faed56271944b615035f44f1'
BASE_URL = 'https://2captcha.com/'
def get_recaptcha_answer(site_key, pageurl):
    try:
        captcha_id = session.post('{}in.php?key={}&method=userrecaptcha&googlekey={}&pageurl={}'.format(BASE_URL, CAPTCHA_KEY, site_key, pageurl)).text.replace('OK|', '')
    except requests.ConnectionError as e:
        print("Connection failure : " + str(e))
        print("Verification with InsightFinder credentials Failed")
    print(captcha_id)


    # get captcha_answer with captcha_id and captcha_key
    try:
        recaptcha_answer = session.get('{}res.php?key={}&action=get&id={}'.format(BASE_URL, CAPTCHA_KEY, captcha_id)).text
    except requests.ConnectionError as e:
        print("Connection failure : " + str(e))
        print("Verification with InsightFinder credentials Failed")
    print(recaptcha_answer)

    # try to get captcha_answer repeatedly until it's ready
    while 'CAPCHA_NOT_READY' in recaptcha_answer:
        print (recaptcha_answer)
        seconds_to_sleep = 5
        time.sleep(seconds_to_sleep)
        try:
            recaptcha_answer = session.get('{}res.php?key={}&action=get&id={}'.format(BASE_URL, CAPTCHA_KEY, captcha_id)).text
        except requests.ConnectionError as e:
            print("Connection failure : " + str(e))
            print("Verification with InsightFinder credentials Failed")
    
    if recaptcha_answer == 'ERROR_CAPTCHA_UNSOLVABLE':
        return get_recaptcha_answer(site_key, pageurl)
    recaptcha_answer = recaptcha_answer.replace('OK|', '')
    return recaptcha_answer