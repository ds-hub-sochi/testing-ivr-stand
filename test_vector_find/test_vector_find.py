import requests
import re
import os
from dotenv import load_dotenv


# Загрузка переменных окружения из файла .env
load_dotenv()
host_url = os.getenv('host_url')


# Функция для очистки строки от спецсимволов
def clean_string(text):
    pattern = r'[^\wа-яА-ЯёЁ]'
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text


# Функция для чтения запросов из файла и их форматирования
def read_queries(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    themes = text.split('\n\n')  # Разделяем текст на темы
    themes = [x.split('\n') for x in themes]  # Разделяем каждую тему на строки
    for i in range(len(themes)):
        theme = themes[i]
        for j in range(len(theme)):
            query = theme[j]
            query = [s.strip() for s in query.split('#')]  # Разделяем строку на вопрос и ответ по символу #
            question = query[0]
            answer = ' '.join([str(s) for s in query[1:]])
            themes[i][j] = {'question': question, 'answer': answer}  # Создаем словарь с вопросом и ответом
    return themes


# Функция для отправки запроса на поиск
def send_request_search(query):
    url = f"{host_url}/items/search?title={query}"
    response = requests.get(url)
    if response.status_code == 200:
        response = response.json()['content']
        answer = [{"title": x['title'], "categoryId": x['categoryId']} for x in response]  # Формируем ответ
        return answer
    else:
        return None


# Функция для получения информации о категории по её ID
def send_request_category(categoryId):
    url = f"{host_url}/categories/{categoryId}"
    response = requests.get(url)
    if response.status_code == 200:
        response = response.json()
        answer = [response['title']]
        if response['parentCategoryId'] != 0:
            answer += send_request_category(response['parentCategoryId'])  # Рекурсивный вызов для получения родительских категорий
        return answer[::-1]  # Возвращаем список категорий в обратном порядке
    else:
        return None


# Функция для нахождения индекса услуги в результатах поиска
def find_service_index(answer, data_for_search):
    answer = clean_string(answer)
    for i in range(len(data_for_search)):
        compare = ' '.join([x for x in data_for_search[i]['categories']]) + ' ' + data_for_search[i]['title']
        compare = clean_string(compare)
        if answer == compare:
            return i + 1
    return 0


# Основная функция программы
def main(file_path):
    themes = read_queries(file_path)  # Чтение и форматирование запросов из файла
    dict_indexes = {0:0,1:0,2:0,3:0,4:0}  # Словарь для хранения статистики
    for theme in themes:
        for i in range(len(theme)):
            query = theme[i]
            data_for_search = send_request_search(query['question'])  # Поиск по запросу
            for i in range(len(data_for_search)):
                data_for_search[i]['categories'] = send_request_category(data_for_search[i]['categoryId'])  # Получение категорий для найденных результатов
            index = find_service_index(query['answer'], data_for_search)  # Нахождение индекса ответа в результатах поиска
            dict_indexes[index] += 1
            if index == 3 or index == 4 or index == 0:  # Вывод информации только для индексов 0, 3 и 4
                print(f"{index} - ({query['answer']}) {query['question']}")
    print(dict_indexes)  # Вывод статистики
    print('ВСЁ')


# Запуск основной функции
if __name__ == "__main__":
    file_path = "queries.txt"
    main(file_path)
