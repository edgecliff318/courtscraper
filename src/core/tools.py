from typing import Any
import functools
import hashlib
import datetime
import time
import re

import imaplib, email
import pandas as pd
import numpy as np
import requests

from src.core.storage import Storage


def compound_exp(r):
    """
    returns the result of compounding the set of returns in r
    """
    return np.expm1(np.log1p(r).sum())


def hash_single(arg):
    if isinstance(arg, pd.Series) or isinstance(arg, pd.DataFrame):
        return hashlib.sha256(
            pd.util.hash_pandas_object(arg, index=True).values).hexdigest()
    elif isinstance(arg, tuple) or isinstance(arg, list):
        m = hashlib.md5()
        for s in arg:
            m.update(str(s).encode())
        return m.hexdigest()
    elif isinstance(arg, str):
        m = hashlib.md5()
        m.update(arg.encode())
        return m.hexdigest()
    elif isinstance(arg, requests.sessions.Session):
        m = 1
    else:
        return hash(arg)


def hash_multiple(args, kwargs):
    hashed_args = tuple(hash_single(arg) for arg in args)
    # (0, 'bb7831021d8a3e98102cca4d329b1201a5d9dff5538a8ebb4229994ac60f6fb1')
    hashed_kwargs = tuple(hash_single(kwarg) for kwarg in kwargs.values())
    return hash_single(hashed_args + hashed_kwargs)


def cached(storage: Storage = None, memory_cache=True):
    """
    A function that creates a decorator which will use "cachefile"
    for caching the results of the decorated function "fn"
    :param storage:
    :type storage:
    :return:
    :rtype:
    """

    def decorator(fn):
        if memory_cache:
            fn_cache = {}

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            kwargs_with_fn = kwargs.copy()
            kwargs_with_fn["fn_module"] = fn.__module__
            kwargs_with_fn["fn_name"] = fn.__name__
            hash_label = hash_multiple(args, kwargs_with_fn)
            if kwargs.get("no_cache", False):
                kwargs.pop("no_cache")
                res = fn(*args, **kwargs)
                storage.save(hash_label, res)
                return res

            if memory_cache:
                #  exists in memory cache
                res = fn_cache.get(hash_label)
                if res is not None:
                    return res

            # If exists in storage cache
            if storage.exist(hash_label):
                res = storage.load(hash_label)
                if res is not None:
                    return res
            # execute the function with all arguments passed
            res = fn(*args, **kwargs)

            if memory_cache:
                # save to memory cache
                fn_cache[hash_label] = res

            # save to storage
            storage.save(hash_label, res)
            return res

        return wrapped

    return decorator



class SonsorEmail:
    """
        how to use:
            create an instance of this class and call it
            snsr = SonsorEmail()
            print(snsr())
    """
    
    def __init__(self) -> None:
        ##TODO: add the email and password to the env file
        self.user = 'fublooman@gmail.com' # Input your gmail address here
        self.password = 'pauzlxwtzkwjyqyr'
        self.imap_url = 'imap.gmail.com'
        # self.threshold_time =  (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d-%b-%Y')
        self.threshold_time =  (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime('%d-%b-%Y')
        
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        link = self.get_magic_link()
        return link
        
        
    def get_my_mail(self):
        my_mail = imaplib.IMAP4_SSL(self.imap_url) # connect to gmail
        my_mail.login(self.user, self.password) # sign in with your credentials
        my_mail.select('Inbox') # select the folder that you want to retrieve
        return my_mail
    
    def check_email_if_exist(self,data,my_mail):
        list_ids = []
        for uid in data[0].split():
            result, data = my_mail.uid('fetch', uid, '(RFC822)')
            raw_email = data[0][1].decode('utf-8')
            email_message = email.message_from_string(raw_email)
            sender = re.search(r'<(.+?)>', email_message['From']).group(1)
            if 'support@email.beenverified.com' in sender:
                list_ids.append(uid)
        return list_ids
        
    
    def wait_for_magic_link(self, data,  my_mail):
        list_ids = []
        start_time = time.time()
        while len(list_ids) == 0:
            list_ids = self.check_email_if_exist(data,my_mail)
            if len(list_ids) > 0:
                break
            ## wait for 40 seconds before checking again
            time.sleep(40)
            ## check if the time is over 5 minutes
            if time.time() - start_time > 5 * 60:
                break
            
        return list_ids
    
    def get_boy_magic_link(self, my_mail, email_id):
        status, email_data = my_mail.fetch(email_id, '(BODY[HEADER] BODY[TEXT])')
        header = email_data[0][1].decode('utf-8')  # Decode the header bytes to a string
        return header
    
    def get_link(self, email_txt):
        link_pattern = re.compile(r'https://click\.email\.beenverified\.com/\?qs=\S*')
        link_match = link_pattern.search(email_txt)
        link = link_match.group()
        return link
    
    def get_magic_link(self):
        my_mail = self.get_my_mail()
        result, data = my_mail.uid('search', None, f'(SENTON {self.threshold_time})')
        list_ids = self.wait_for_magic_link(data,my_mail)
        if len(list_ids) == 0: 
            raise Exception("No magic link found")      
        email_txt = self.get_boy_magic_link(my_mail, list_ids[0])
        link = self.get_link(email_txt)
        return link
        
        

       
    
    
                
                
