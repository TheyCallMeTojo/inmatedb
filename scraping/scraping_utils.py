import random
import re
import time
from typing import NamedTuple


def random_delay(min_delay=100, max_delay=2000):
    delay = random.randint(min_delay, max_delay)
    time.sleep(delay/1000)

def text_contains_word(text, target):
    word_match = re.compile(rf"({target})([^\w]|$)")
    matches = word_match.findall(text)
    return len(matches) != 0


class TableMatch(NamedTuple):
    table_row: object
    table_idx: int

def search_table_by_text(table_element, target, row_offset=0):
    match = TableMatch(None, -1)
    
    table_rows = table_element.find_all(name="tr")
    for i, tr in enumerate(table_rows):
        for row_data in tr.find_all(name="td"):
            if text_contains_word(row_data.text, target):
                match = TableMatch(tr, i)
                break
    
    if match.table_row is None:
        return match
    
    if row_offset != 0:
        table_idx = match.table_idx + row_offset
        if 0 <= table_idx < len(table_rows):
            table_row = table_rows[table_idx]
            match = TableMatch(table_row, table_idx)
        else:
            match = TableMatch(None, -1)
    
    return match

def get_table_value(table, target):
    target_tr = search_table_by_text(table, target).table_row
    if target_tr is None:
        return None
    
    target_td = target_tr.find_all(name="td")[-1]
    return target_td.text
