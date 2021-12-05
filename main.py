from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import csv
import re

base_url = 'https://zakupki.gov.ru'
url_full = 'https://zakupki.gov.ru/epz/complaint/search/search_eis.html?searchString=&morphology=on' \
           '&search-filter=%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F' \
           '&savedSearchSettingsIdHidden=&fz94=on&fz223=on&considered=on&decisionOnTheComplaintTypeResult_1=on' \
           '&decisionOnTheComplaintTypeResult=1&receiptDateStart=&receiptDateEnd=&updateDateFrom=&updateDateTo=' \
           '&sortBy=UPDATE_DATE&pageNumber=1&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=true'



# def receive_query_status(query_params, name_status):
#     """
#     :param query_params: input query parameters
#     :param name_status: published-размещена, regarded-рассматривается, considered-рассмотрена, returned-отказано в
#     рассмотрении, cancelled-отозвана
#     :return: output query parameters, depending on the name of desision
#     """
#     statuses = {'considered', 'returned', 'cancelled', 'published', 'regarded'}
#     for element in statuses:
#         if element in query_params.keys():
#             del query_params[element]
#     query_params[name_status] = 'on'
#     return query_params
#
#
# def receive_query_decision(query_params, name_decision, name_status):
#     """
#     :param query_params: input query parameters
#     :param name_decision: justified-обоснована, partially_justified-обоснована частично, not_justified-не обоснована,
#     not_competence-не относится к компетенции тек органах
#     :return: output query parameters, depending on the name of decision
#     """
#     decisions = {'justified': 0, 'partially_justified': 1, 'not_justified': 2, 'not_competence': 3}
#     for element in decisions.values():
#         if 'decisionOnTheComplaintTypeResult_{}'.format(element) in query_params.keys():
#             del query_params['decisionOnTheComplaintTypeResult_{}'.format(element)]
#     if name_status == 'considered':
#         query_params['decisionOnTheComplaintTypeResult_{}'.format(decisions[name_decision])] = 'on'
#         query_params['decisionOnTheComplaintTypeResult'] = str(decisions[name_decision])
#     query_params['decisionOnTheComplaintTypeResult'] = ''
#     return query_params


def receive_query_params(query_params, name_decision, name_status=None):
    """
    :param query_params: input query parameters
    :param name_decision: published-размещена, regarded-рассматривается, considered-рассмотрена, returned-отказано в
    рассмотрении, cancelled-отозвана
    :param name_status: justified-обоснована, partially_justified-обоснована частично, not_justified-не обоснована,
    not_competence-не относится к компетенции тек органах, default value None
    :return: output query parameters, depending of the status and decision names
    """
    decisions = ['considered', 'returned', 'cancelled', 'published', 'regarded']
    statuses = {'justified': 0, 'partially_justified': 1, 'not_justified': 2, 'not_competence': 3}

    query_params['decisionOnTheComplaintTypeResult'] = ''

    for element in decisions:
        if element in query_params.keys():
            del query_params[element]

    query_params[name_decision] = 'on'
    query_params['decisionOnTheComplaintTypeResult'] = ''

    for element in statuses.values():
        if 'decisionOnTheComplaintTypeResult_{}'.format(element) in query_params.keys():
            del query_params['decisionOnTheComplaintTypeResult_{}'.format(element)]

    if name_status is not None and name_decision == 'considered':
        query_params['decisionOnTheComplaintTypeResult_{}'.format(statuses[name_status])] = 'on'
        query_params['decisionOnTheComplaintTypeResult'] = statuses[name_status]

    return query_params


def url_parse(url, name_decision, name_status=None):
    """
    :param url: url for parse
    :param name_decision: published-размещена, regarded-рассматривается, considered-рассмотрена, returned-отказано в
    рассмотрении, cancelled-отозвана
    :param name_status: justified-обоснована, partially_justified-обоснована частично, not_justified-не обоснована,
    not_competence-не относится к компетенции тек органах, default value None
    :return: list of urls for parsing, depending on the name of decision and status name
    """
    url_parse_result = urlparse(url)
    query_params_old = parse_qs(url_parse_result.query)
    query_params = receive_query_params(query_params_old, name_decision, name_status)
    url_list = []
    for page in range(1, 21):
        query_params['pageNumber'] = [page]
        query_params_new_encode = urlencode(query_params, doseq=True)
        url_unparse_result = urlunparse((str(url_parse_result.scheme), str(url_parse_result.netloc), str(url_parse_result.path),
                                        str(url_parse_result.params), query_params_new_encode, str(url_parse_result.fragment)))
        url_list.append(url_unparse_result)
    return url_list


def save_file(dict_with_results, path):
    """
    :param dict_with_results: dictionary with parsing results
    :param path: path for save file
    :return: file with parsing results
    """
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['Закон', 'Номер жалобы', 'Ссылка на жалобу', 'Статус', 'Решение', 'Предписание', 'Орган контроля',
                         'Заказчик', 'Заказчик ссылка', 'Лицо, подавшее жалобу', 'Поступление жалобы', 'Рассмотрение жалобы',
                         'Дата обновления', 'Извещение', 'Описание закупки', 'Идентификационный код закупки (ИКЗ)',
                         'Решение документ'])
        for item in dict_with_results:
            writer.writerow([item['Закон'], item['Номер жалобы'], item['Ссылка на жалобу'], item['Статус'], item['Решение'],
                             item['Предписание'], item['Орган контроля'], item['Заказчик'], item['Заказчик ссылка'],
                             item['Лицо, подавшее жалобу'], item['Поступление жалобы'], item['Рассмотрение жалобы'],
                             item['Дата обновления'], item['Извещение ссылка'], item['Описание закупки'],
                             item['Идентификационный код закупки (ИКЗ)'], item['Решение документ']])


def check_subject_control(element, tag='div', class_name="cardMainInfo__title"):
    check_result = False
    check_value = element.find(tag, class_name).get_text(strip=True),
    if check_value == "Субъект контроля":
        check_result = True
    return check_result


def get_href(element, atr_name, tag='a'):
    list_hrefs = []
    href = ''
    for element in element.find_all(tag):
        list_hrefs.append(element.get('href'))
    if atr_name == 'Ссылка на жалобу':
        hrefs = [re.findall(r'^/epz/complaint/card/complaint-\w+.\w+\?\w+=\d+', i) for i in list_hrefs if i is not None]
    if atr_name == 'Заказчик ссылка':
        hrefs = [re.findall(r'^/epz/organization/view/info.\w+\?\w+=\d+', i) for i in list_hrefs if i is not None]
    if atr_name == 'Извещение ссылка':
        hrefs = [re.findall(r'^/epz/order/notice/view/common-\w+.\w+\?\w+=\d+', i) for i in list_hrefs if i is not None]
    if atr_name == 'Решение документ':
        hrefs = [re.findall(r'^https://zakupki.gov.ru/controls/documentIcrDownload\?[\w|\s]+=\d+', i) for i in list_hrefs if i is not None]
    for i in hrefs:
        if len(i) > 0:
            href = i[0]
    return href


def get_decision(element, tag='span', class_name="registry-entry__body-title distancedText mr-4"):
    check_decision = element.find(tag, class_name)
    if check_decision:
        decision = check_decision.get_text(strip=True)
    else:
        decision = ""
    return decision


def get_prescription(element, tag='span', class_name="registry-entry__body-title distancedText mr-4"):
    check_prescription_1 = element.find(tag, class_name)
    check_prescription_2 = check_prescription_1.find_next(tag, class_name)
    if check_prescription_2:
        prescription = check_prescription_2.get_text(strip=True)
    elif check_prescription_1:
        text_prescription = check_prescription_1.get_text(strip=True)
        prescription = ''
        if text_prescription == 'Предписание не выдано' or text_prescription == 'Предписание выдано':
            prescription = check_prescription_1
    else:
        prescription = ""
    return prescription


def get_side(element, value, tag='div', class_name="registry-entry__body-title"):
    side = ''
    matches = element.find_all(tag, class_name)
    for match in matches:
        if match.get_text(strip=True) == value:
            if value == 'Субъект жалобы':
                side = match.find_next_siblings()[1].get_text(strip=True)
                return side
            side = match.find_next_siblings()[0].get_text(strip=True)
            return side
    return side


def get_date(element, value, tag='div', class_name="registry-entry__body-title"):
    date = ''
    matches = element.find_all(tag, class_name)
    for match in matches:
        if match.get_text(strip=True) == value:
            date = match.find_next_siblings()[0].get_text(strip=True)
            return date
        else:
            pass
    return date


def get_purchase(element, value, tag='div', class_name="d-flex lots-wrap-content__body__title"):
    purchase = ''
    matches = element.find_all(tag, class_name)
    for match in matches:
        if match.get_text(strip=True) == value:
            if value == 'Извещение' and (len(match.find_next_siblings()) > 1):
                purchase = match.find_next_siblings()[1].get_text(strip=True)
                return purchase
            purchase = match.find_next_siblings()[0].get_text(strip=True)
            return purchase
        else:
            pass
    return purchase


def get_content(soup, tag='div', class_name="search-registry-entry-block box-shadow-search-input"):
    items = soup.find_all(tag, class_name)
    complients = []

    for item in items:
        claim_href = get_href(item, atr_name='Ссылка на жалобу')
        control_body = get_side(item, value='Орган контроля')
        customer = get_side(item, value='Субъект жалобы')
        customer_href = get_href(item, atr_name='Заказчик ссылка')
        complainer = get_side(item, value='Лицо, подавшее жалобу')
        date_of_receipt = get_date(item, value='Поступление жалобы')
        date_of_review = get_date(item, value='Рассмотрение жалобы')
        date_of_update = get_date(item, value='Обновлено')
        notification_href = get_href(item, atr_name='Извещение ссылка')
        decision_doc = get_href(item, atr_name='Решение документ')
        decision = get_decision(item)
        prescription = get_prescription(item)
        purchase_description = get_purchase(item, value='Извещение')
        purchase_number = get_purchase(item, value='Идентификационный код закупки (ИКЗ)')
        complients.append(
            {'Закон': item.find('div', class_="cardMainInfo__title distancedText").get_text(strip=True),
             'Номер жалобы': item.find('span', class_="registry-entry__header-mid__number").get_text(strip=True),
             'Ссылка на жалобу': base_url + claim_href,
             'Статус': item.find('span', class_="registry-entry__header-mid__title").get_text(strip=True),
             'Решение': decision,
             'Предписание': prescription,
             'Орган контроля': control_body,
             'Заказчик': customer,
             'Заказчик ссылка': base_url + customer_href,
             'Лицо, подавшее жалобу': complainer,
             'Поступление жалобы': date_of_receipt,
             'Рассмотрение жалобы': date_of_review,
             'Дата обновления': date_of_update,
             'Извещение ссылка': base_url + notification_href,
             'Описание закупки': purchase_description,
             'Идентификационный код закупки (ИКЗ)': purchase_number,
             'Решение документ': decision_doc
             }
        )
    return complients


def main():
    url_list = url_parse(url=url_full, name_decision='considered', name_status='justified')
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)
    driver.maximize_window()
    driver.implicitly_wait(5)
    try:
        complients = []
        page = 1
        for url in url_list:
            print('Парсинг страницы {} из 20'.format(page))
            driver.get(url)
            driver.implicitly_wait(10)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            complients.extend(get_content(soup))
            print('Получен контент {} страницы из 20'.format(page))
            driver.implicitly_wait(10)
            page += 1
        save_file(complients, '/Users/alenakapustan/Git/web_scraping_selenium/complients.csv')
        print('Получено {} записей'.format(len(complients)))
    finally:
        driver.close()
        driver.quit()


if __name__ == "__main__":
    main()
