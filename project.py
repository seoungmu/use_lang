from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import psycopg2


# 크롤링할 날짜 설정
date_index = pd.date_range(start='20230914', end='20230930')
# 날짜를 리스트화
date_list = date_index.strftime("%Y-%m-%d").tolist()

print(date_list)

for i in range(len(date_list)):
    nday = date_list[i]
    lang = []
    for page in range(1, 101):

        print(f"{nday}날 {page}페이지")
        # 페이지 설정
        url = f'https://github.com/search?q=created%3A{nday}&type=Repositories&ref=advsearch&l=&l=&p={page}'

        driver = webdriver.Chrome()
        driver.get(url)

        # 게시글들의 XPath를 가져와 저장
        post_list = driver.find_elements(By.XPATH,
                                         '/html/body/div[1]/div[4]/main/react-app/div/div/div[1]/div/div/main/div[2]/div/div[1]/div[4]/div/div/div')

        for j in post_list:
            # 게시글 제목을 저장
            npost_title = WebDriverWait(j, 10).until(
                EC.presence_of_element_located((By.XPATH, './div/div[1]/h3/div/div[2]/a/span'))).text
            # 게시글의 a태그를 저장
            npost = WebDriverWait(j, 10).until(
                EC.presence_of_element_located((By.XPATH, './div/div[1]/h3/div/div[2]/a')))

            link = npost.get_attribute('href')

            # 새 탭에서 페이지 열기
            driver.execute_script(f"window.open('{link}', '_blank');")

            driver.switch_to.window(driver.window_handles[1])

            time.sleep(1)

            try:
                post_lang = driver.find_elements(By.CSS_SELECTOR, '.d-inline')
                post_langs = []

                for postlang in post_lang[2:]:
                    rpl_postlang = postlang.text.replace('\n', ':')
                    post_langs.append(rpl_postlang)
                lang.append([nday, npost_title, post_langs])
            except:
                lang.append([npost_title])
            finally:
                driver.close()  # 새 탭 닫기
                driver.switch_to.window(driver.window_handles[0])

    df = pd.DataFrame(lang, columns=['date', 'title', 'language'])
    # csv파일 저장
    df.to_csv(f'{nday}_git_lang.csv', index=False)

    git_lang = df.dropna(axis = 0)
    # db연결
    db = psycopg2.connect(host='localhost', dbname='project1', user='root', password='5432', port=5432)

    cursor = db.cursor()
    # DataFrame을 db에 저장
    for index, row in git_lang.iterrows():
        create_dt = row['date']
        title = row['title']
        lang = row['language']

        insert_query = "INSERT INTO project_git.git_lang (create_dt, title, lang) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (create_dt, title, lang))

    # 변경사항 저장
    db.commit()
    # 연결 종료
    db.close()