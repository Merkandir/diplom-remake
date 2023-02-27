from func import *
from db import *


def main():
    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text.lower().strip()
                if request == "поехали":
                    conn = psycopg2.connect(database="vkdb", user="postgres", password="123")

                    user_info = get_user_info(event.user_id)

                    if user_info is not False:
                        if len(user_info) != 6 or len(user_info['bdate'].split('.')) != 3:
                            write_msg(event.user_id, "Недостаточно информации, пожалуйста, заполните пробелы &#128373;")
                            user_info = get_additional_information(user_info)
                            if user_info is False:
                                continue
                        else:
                            user_age = bdate_to_age(user_info['bdate'])
                            if user_age < 18:
                                write_msg(event.user_id,
                                          "Сервис недоступен для пользователей моложе 18 лет! &#128286;")
                                continue
                            else:
                                user_info['age'] = user_age
                                if 'bdate' in user_info:
                                    user_info.pop('bdate')
                    else:
                        write_msg(event.user_id, "Что-то пошло не так...")
                        break

                    user_db_id = get_user_db_id(conn, user_info['id'])

                    if user_db_id is False:
                        user_db_id = insert_user(conn, user_info)

                    users_list = get_users_list(user_info)
                    status = True
                    last_user = users_list[-1]

                    if users_list is not False:
                        write_msg(event.user_id, "Отлично, начинаем искать!")
                        for user in users_list:
                            if user == last_user and check_result_user(conn, user.get('id'), user_db_id) is False:
                                write_msg(event.user_id, "Больше никого нет, попробуйте ближайшие города!")
                            else:
                                check = check_result_user(conn, user.get('id'), user_db_id)
                                if check:
                                    if status:
                                        photos_info = get_photos(user)
                                        if photos_info is not False:
                                            if photos_info.get('count') < 3:
                                                continue
                                            else:
                                                photos_link = get_most_popular_photo(photos_info)
                                                write_photo_msg(event.user_id,
                                                                f"""Вам подходит {user.get('first_name')} """
                                                                f"""{user.get('last_name')} &#128150;\n"""
                                                                f"""Профиль: https://vk.com/id{user.get('id')}\n"""
                                                                f"""Самые популярные фоторафии:""", user,
                                                                photos_link)

                                                insert_result_user(conn, user_db_id, user)

                                                write_msg(event.user_id, """Ищем дальше? 
                                                                            Чтобы продолжить, введите "дальше",
                                                                            чтобы закончить, введите "закончить". """)
                                                for event in long_poll.listen():
                                                    if event.type == VkEventType.MESSAGE_NEW:
                                                        if event.to_me:
                                                            request = event.text.lower().strip()
                                                            if request == 'дальше':
                                                                write_msg(event.user_id, "Ок, ищем дальше!")
                                                                break
                                                            elif request == 'закончить':
                                                                write_msg(event.user_id, "Пока((")
                                                                status = False
                                                                break
                                                            else:
                                                                write_msg(event.user_id, """Чтобы продолжить, введите \
                                                                "дальше",\nчтобы закончить, введите "закончить" """)
                                        else:
                                            continue
                                    else:
                                        break
                                else:
                                    continue
                    else:
                        write_msg(event.user_id, "Что-то пошло не так...")
                        break
                    conn.close()

                else:
                    write_msg(event.user_id, f"""Вас приветствует бот VKinder &#9995;\n
                                                 Введите "поехали", чтобы начать.""")


if __name__ == '__main__':
    conn = psycopg2.connect(database="vkdb", user="postgres", password="123")
    delete_tables(conn)
    create_tables(conn)
    conn.close()

    main()
