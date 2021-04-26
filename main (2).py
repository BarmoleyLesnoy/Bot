import aiogram  # Подключаем библиотеку aiogram

import config as cfg  # Подключаем файл config.py

from aiogram import types

import sqlite3  # Для работы с базой данных
import os.path  # Для работы с файловой системой

import googletrans
from googletrans import Translator

# Кнопки
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

transl = Translator()
bot = aiogram.Bot(token=cfg.TOKEN)
dp = aiogram.Dispatcher(bot)  # Создает диспетчера

globalVar = {}  # Статус бота. Запущен он или нет. Если нет, то бот не будет ниначто реагировать

# Начальная проверка на наличие файла базы данных и ее заполнение
path = os.path.abspath(os.path.dirname(__file__))  # Путь откуда запущена исполняема программа
sqlite_file = path + '\\' + cfg.NAMEBOT + '.db'
if os.path.exists(sqlite_file):
    # Файл есть. Просто соединяемся
    mydb = sqlite3.connect(sqlite_file)
    mycursor = mydb.cursor()
else:
    # Файла не существует. Создадим структуру БД
    print("Файла нет. Создаем")
    mydb = sqlite3.connect(sqlite_file)
    mycursor = mydb.cursor()
    mycursor.execute("CREATE TABLE Users (id TEXT NOT NULL, lang_id TEXT)")
    mycursor.execute("CREATE TABLE Languages (id TEXT NOT NULL, lang TEXT)")

# В любом случае перезаполним таблицу Languages
mycursor.execute("DELETE FROM Languages")
mydb.commit()
# print(googletrans.LANGUAGES)
for x in googletrans.LANGUAGES:
    val = (str(x), googletrans.LANGUAGES[x])
    mycursor.execute("INSERT INTO Languages (id, lang) VALUES (?, ?)", val)
mydb.commit()

print('started')


# Обработчик команды "start"
@dp.message_handler(commands=['start'])
async def process_start_command(message: aiogram.types.Message):
    mycursor = mydb.cursor()
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    globalVar[chat_id] = {'BotIsRun': True}

    # Chat = await bot.get_chat(chat_id)

    adr = (chat_id,)
    mycursor.execute("SELECT * FROM users WHERE id = ?", adr)  # Ищем в базе пользователя/чат с текущим ID
    myresult = mycursor.fetchall()
    # print(myresult)

    new_word = ""
    if myresult is None or myresult == [] or myresult == ():
        # Если пользователя нет в БД, то его надо туда добавить
        mycursor = mydb.cursor()
        val = (chat_id, "ru")
        mycursor.execute("INSERT INTO users (id, lang_id) VALUES (?, ?)", val)
        mydb.commit()

        msg_text = "Регистрация чата пройдена"
        word = await translate_STR_user(msg_text=msg_text, user_id=user_id, count_lang=1)
        new_word = new_word + word
    else:
        # Пользователь уже имеется
        msg_text = "Чат уже зарегистрирован"
        word = await translate_STR_user(msg_text=msg_text, user_id=user_id, count_lang=1)
        if word == "":
            word = msg_text
        new_word = new_word + word

    msg_text = "Привет, я бот-переводчик. Для смены языка введите "
    word = await translate_STR_user(msg_text=msg_text, user_id=chat_id, count_lang=1)
    if word == "":
        word = msg_text
    new_word_parse = await Parse_srt_for_MarkdownV2(msg_text=new_word)
    txt = word + " /choose"
    txt_parse = await Parse_srt_for_MarkdownV2(msg_text=txt)
    new_word = new_word_parse + '\n' + txt_parse
    await Send_message_To_User(msg_text=new_word, user_id=chat_id,
                               parse_mode="MarkdownV2", reply_to_message_id=message.message_id,
                               reply_markup=ReplyKeyboardRemove(),
                               disable_notification=True)  # Приветственное сообщение, заодно уберем все лишние кнопки


# Обработчик команды "choose"
@dp.message_handler(commands=['choose'])
async def process_choose_command(message: aiogram.types.Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if globalVar.get(chat_id, None) != None:
        if globalVar[chat_id]['BotIsRun'] == False:
            return

    itAdmin = await It_admin_chat(user_id=user_id, chat_id=chat_id)
    if itAdmin != True:
        return  # Не админ - значит нельзя генерировать кнопки

    markup = create_markup(user_id=chat_id)  # Кнопки создаем для чата. В личной беседе ID чата и пользователя совпадают

    msg_text = "Выберите языки общения"
    word = await translate_STR_user(msg_text=msg_text, user_id=user_id,
                                    count_lang=1)  # Перевод делаем именно для пользователя
    if word == "":
        word = msg_text
        # await message.reply(word, reply_markup=markup)
    word_parse = await Parse_srt_for_MarkdownV2(msg_text=word)
    await Send_message_To_User(msg_text=word_parse, user_id=chat_id,
                               parse_mode="MarkdownV2", reply_markup=markup,
                               disable_notification=True)  # Приветственное сообщение, заодно уберем все лишние кнопки


# Обработчик команды "lang1"
@dp.message_handler(commands=['mylang'])
async def process_choose_command(message: aiogram.types.Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if globalVar.get(chat_id, None) != None:
        if globalVar[chat_id]['BotIsRun'] == False:
            return

    itAdmin = await It_admin_chat(user_id=user_id, chat_id=chat_id)
    if itAdmin != True:
        return  # Не админ - значит нельзя генерировать кнопки

    msg_text = "Выберите язык общения"
    word = await translate_STR_user(msg_text=msg_text, user_id=user_id,
                                    count_lang=1)  # Перевод делаем именно для пользователя
    if word == "":
        word = msg_text
    inline = create_Inline(user_id=chat_id)  # Кнопки создаем для чата. В личной беседе ID чата и пользователя совпадают
    if word == "":
        word = msg_text
    word_parse = await Parse_srt_for_MarkdownV2(msg_text=word)
    await Send_message_To_User(msg_text=word_parse, user_id=chat_id,
                               parse_mode="MarkdownV2", reply_markup=inline,
                               disable_notification=True)  # Приветственное сообщение, заодно уберем все лишние кнопки


# Обработчик команды "help"
@dp.message_handler(commands=['help'])
async def process_help_command(message: aiogram.types.Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    word = await translate_STR_user(msg_text=cfg.help_, user_id=user_id,
                                    count_lang=1)  # Перевод делаем именно для пользователя
    if word == "":
        word = cfg.help_

    help_parse = await Parse_srt_for_MarkdownV2(msg_text=word)
    await Send_message_To_User(msg_text=help_parse, user_id=message.chat.id,
                               parse_mode="MarkdownV2", reply_to_message_id=message.message_id,
                               disable_notification=True)


# Обработчик команды "go". Запускает бота после команды /stop
@dp.message_handler(commands=['go'])
async def process_help_go(message: aiogram.types.Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    globalVar[chat_id] = {'BotIsRun': True}

    msg_text = "Бот запущен"
    word = await translate_STR_user(msg_text=msg_text, user_id=user_id,
                                    count_lang=1)  # Перевод делаем именно для пользователя
    if word == "":
        word = msg_text

    await Send_message_To_User(msg_text=word, user_id=chat_id,
                               parse_mode="MarkdownV2", reply_to_message_id=message.message_id,
                               disable_notification=True)


# Обработчик команды "stop". Останавливает бота
@dp.message_handler(commands=['stop'])
async def process_help_go(message: aiogram.types.Message):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    globalVar[chat_id] = {'BotIsRun': False}

    msg_text = "Бот остановлен"
    word = await translate_STR_user(msg_text=msg_text, user_id=user_id,
                                    count_lang=1)  # Перевод делаем именно для пользователя
    if word == "":
        word = msg_text

    await Send_message_To_User(msg_text=word, user_id=chat_id,
                               parse_mode="MarkdownV2", reply_to_message_id=message.message_id,
                               disable_notification=True)


# Обработчик нажатия кнопок выбора языка
@dp.callback_query_handler(lambda c: c.data)
async def process_callback_kb1btn1(callback_query: aiogram.types.CallbackQuery):
    chat_id = str(callback_query.message.chat.id)

    if globalVar.get(chat_id, None) != None:
        if globalVar[chat_id]['BotIsRun'] == False:
            return

    lang = str(callback_query.data)
    # if cfg.LANGDICT_inline.get(lang_desc, None) != None:
    if cfg.LANGDICT.get(lang, None) != None:
        user_id = str(callback_query.from_user.id)

        """
        #Изменилась идея. Команда инлайновой кнопки - ставит язык пользователя
        #Удалим все языки что есть для указанного чата
        mycursor = mydb.cursor()
        val = (chat_id, )
        mycursor.execute("DELETE FROM users where id = ?", val) #Удаляем из базы языки общения
        mydb.commit()

        #Добавляем в базу выбранный язык
        val = (chat_id, lang)
        #mycursor.execute("UPDATE users SET lang_id = ? WHERE id = ?", val) #Пишем в базу новый язык общения
        mycursor.execute("INSERT INTO users (id, lang_id) VALUES (?, ?)", val) #Пишем в базу новый язык общения
        mydb.commit()

        word = await translate_STR_user(msg_text="Язык общения изменен на", user_lang=lang)
        if word == "":
            word = msg_text 
        new_word = word + " " + lang
        await Send_message_To_User(msg_text=new_word, user_id=chat_id,
                                   reply_markup=ReplyKeyboardRemove()) """

        # Удалим все языки что есть для указанного пользователя
        mycursor = mydb.cursor()
        val = (user_id,)
        mycursor.execute("DELETE FROM users where id = ?", val)  # Удаляем из базы языки общения
        mydb.commit()

        # Добавляем в базу выбранный язык
        val = (user_id, lang)
        # mycursor.execute("UPDATE users SET lang_id = ? WHERE id = ?", val) #Пишем в базу новый язык общения
        mycursor.execute("INSERT INTO users (id, lang_id) VALUES (?, ?)", val)  # Пишем в базу новый язык общения
        mydb.commit()

        word = await translate_STR_user(msg_text="Язык общения изменен на", user_lang=lang)
        if word == "":
            word = msg_text
        new_word = word + " " + lang
        await Send_message_To_User(msg_text=new_word, user_id=chat_id,
                                   reply_markup=ReplyKeyboardRemove(),
                                   disable_notification=True)


# Основная функция. Висит и "слушает" ввод текста от пользователя
# Сюда передается любой вывод сообщений, который небыл обработан индивидуальной командой
@dp.message_handler()
async def echo_message(msg: types.Message):
    user_id = str(msg.from_user.id)
    chat_id = str(msg.chat.id)
    msg_text = str(msg.text)

    if globalVar.get(chat_id, None) != None:
        if globalVar[chat_id]['BotIsRun'] == False:
            return

    # print("Входящее сообщение: ", msg)

    # print("user_id = ", user_id, "/n", "msg_text = ", msg_text, "/n", "chat_id = ", chat_id)

    # Нам необходимо получить всех кто входит в группу и узнать их языки. И вот на эти все
    # языки необходимо перевести исходный текст

    BotInfo = await bot.get_me()
    # print("Общая Информация о боте: ", BotInfo)

    # Chat = await bot.get_chat(chat_id)
    # print("Информация о текущем чате: ", Chat)

    BotChatMember = await bot.get_chat_member(chat_id, BotInfo.id)
    # print("Информация о боте в текущем чате: ", BotChatMember)

    DeleteOrigMsg = True  # Изначально предполагаем что работаем в режиме удаления оригинальных сообщений
    # Не во всех чатах бот сможет удалять сообщения
    if BotChatMember.status == "member":
        # Обычные права. Работаем в режиме повтора без удалений
        DeleteOrigMsg = False
    else:
        # Варианты только "member" или "administrator"
        # Мы тут - значит у нас права администратора. Однако админы тоже иногда не могут удалять сообщения
        if BotChatMember.can_delete_messages == True:
            # Может у далять сообщения
            DeleteOrigMsg = True
        else:
            # Нет прав на удаление
            DeleteOrigMsg = False

    # Это выбор языка?
    it_select_lang = await select_lang(lang_desc=msg_text, user_id=user_id,
                                       chat_id=chat_id, message_id=msg.message_id)
    if it_select_lang == True:
        # print("Выбор языка")
        if DeleteOrigMsg == True:
            # Удалять сообщения можно и нужно
            await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)  # Удаляет исходное сообщение
        return  # Да. Это выбор языка

    # print("Это НЕ выбор языка")

    # По идее вот тут надо еще проверить что строка требует перевода.

    # Переводим полученный текст
    word = await translate_STR_user(msg_text=msg_text, user_id=chat_id)
    # print("Результат перевода = ", word)
    if word == "" or word == msg_text:
        # Строку НЕ смогли перевести или что-то пошло не так
        # Или строка не требует перевода
        return

    # Сообщение может писаться новое, а может пересыласться
    # При пересылке у msg есть поле reply_to_message
    if msg.reply_to_message != None:
        # print("Пересылка")
        reply_to_message_id = msg.reply_to_message.message_id
    else:
        # print("Отправка")
        reply_to_message_id = 0

    msg_text_parse = await Parse_srt_for_MarkdownV2(msg_text=msg_text)
    word_parse = await Parse_srt_for_MarkdownV2(msg_text=word)

    if DeleteOrigMsg == True:
        Name = msg.from_user.first_name + " " + msg.from_user.last_name
        Name_parse = await Parse_srt_for_MarkdownV2(msg_text=Name)

        # Пока идет работа над собиранием участников чата - мы поступим просто...
        if msg_text != word:
            new_msg_text = "[*" + Name_parse + "*](tg://user?id=" + user_id + ")" + "\n" + "__" + msg_text_parse + "__" + "\n" + " " + "\n" + word_parse
        else:
            new_msg_text = "[*" + Name_parse + "*](tg://user?id=" + user_id + ")" + "\n" + msg_text_parse

        await Send_message_To_User(msg_text=new_msg_text, user_id=chat_id,
                                   parse_mode="MarkdownV2",
                                   reply_to_message_id=reply_to_message_id)  # Возвращаем сообщение в чат

        # Удалять сообщения можно и нужно. Удаляем только после отправки
        await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)  # Удаляет исходное сообщение
    else:
        # Удалять сообщения нельзя или ненадо
        # Отправляем только если исходный текст не равен переведенному
        if msg_text != word:
            await Send_message_To_User(msg_text=word_parse, user_id=chat_id,
                                       parse_mode="MarkdownV2",
                                       reply_to_message_id=msg.message_id)  # Возвращаем сообщение в чат


# Проверяет пользователя - является ли он администратором указанного чата
async def It_admin_chat(user_id="", chat_id=""):
    # Если использовать get_chat_administrators в приватной беседе - будет ошибка
    Chat = await bot.get_chat(chat_id)
    itAdmin = False
    if Chat.type == "private":
        # В приватном чате позволяем менять
        itAdmin = True
    else:
        # Чат не приватный - можем посмотреть кто админ
        chat_admin = await bot.get_chat_administrators(chat_id=chat_id)
        for tekAdmin in chat_admin:
            # print("Текущий администратор: ", tekAdmin)
            # print("ID admin = ", tekAdmin.user.id, "ID user = ", user_id)
            if str(tekAdmin.user.id) == str(user_id):
                itAdmin = True
    return itAdmin


# Обработка выбора языка
async def select_lang(lang_desc="", user_id="", chat_id="", message_id=""):
    # Сначала проверим что это строка со спец-символами языка
    if lang_desc[0] != '◌' and lang_desc[0] != '●':
        # Что-то не то
        return False

    # Только админ может менять языки
    itAdmin = await It_admin_chat(user_id=user_id, chat_id=chat_id)

    # print("Работает администратор: ", itAdmin)
    # print("Данные чата: ", Chat)

    if itAdmin == False:
        return True  # Это выбор языка, но у пользователя нет прав

    if lang_desc == "◌ X":  # надо закрыть выбор языков
        word = "ОК"
        markup = ReplyKeyboardRemove()
        await Send_message_To_User(msg_text=word, user_id=chat_id,
                                   parse_mode="MarkdownV2", reply_markup=markup, disable_notification=True)
        return True

    lang_id = ""
    lang_desc2 = lang_desc.replace('●', '◌', 1)  # Нужно для поиска
    if lang_desc2 in cfg.LANGDICT.values():
        for key, desc in cfg.LANGDICT.items():
            if desc == lang_desc2:
                lang_id = key

    if lang_id != "":  # мы нашли описание языка
        if lang_desc[0] == '◌':
            # Мы выбрали язык который ранее небыл выбран. Значит мы его добавляем
            msg_text = "Добавлен язык общения"
            mycursor = mydb.cursor()
            val = (chat_id, lang_id)
            mycursor.execute("INSERT INTO users (id, lang_id) VALUES (?, ?)", val)  # Пишем в базу новый язык общения
            mydb.commit()
        else:
            # Мы выбрали язык который ранее уже был выбран. Значит мы его удаляем
            msg_text = "Удален язык общения"
            mycursor = mydb.cursor()
            val = (chat_id, lang_id)
            mycursor.execute("DELETE FROM users where id = ? and lang_id = ?", val)  # Удаляенм из базы язык общения
            mydb.commit()

        # Переводим именно на язык, который добавили
        word = await translate_STR_user(msg_text=msg_text, user_lang=lang_id)
        if word == "":
            word = msg_text
        new_word = word + " " + lang_id
        new_word_parse = await Parse_srt_for_MarkdownV2(msg_text=new_word)
        markup = create_markup(user_id=chat_id)

        await Send_message_To_User(msg_text=new_word_parse, user_id=chat_id,
                                   parse_mode="MarkdownV2", reply_markup=markup,
                                   disable_notification=True)

    return True


# Производит корректировку строку согласно требованиям MarkdownV2
async def Parse_srt_for_MarkdownV2(msg_text=""):
    list1 = ['_', '*', '[', ']', '(', ')', '~', '"', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    it = iter(list1)
    text = msg_text
    for x in it:
        new_x = "\\" + x
        text = text.replace(x, new_x)

    # print(text)
    return text


# Производит непосредственный перевод
async def translate(msg_text="", user_lang=""):
    try:
        tr = transl.translate(msg_text, dest=user_lang)  # Перевод сообщения
        dt = transl.detect(msg_text)  # Определение языка
        # print("Результат перевода: ", tr)
        # print("Результат перевода: ", tr.extra_data)
        # print("Определение исходного языка: ", dt)
    except NameError:
        word = ""
        err = "Ошибка перевода текста"
        print(err, '\r', NameError)
    else:
        word = tr.text

    # Было замечено, что переводчик меняет команды, а иногда и переводит их
    # Поэтому команды были заменены на некоторые представления и потом эти представления
    # будут меняться по словарю
    for key, cmd in cfg.command.items():
        word = word.replace(key, cmd, 1)

    return word


# Переводит полученнную строку и возвращает результат перевода
async def translate_STR_user(msg_text="", user_id="", user_lang="", count_lang=0):
    # count_lang - количество языков, на которые переводить. 0 - переводить на вес доступные
    # языки для пользователя. Если передать 1 - выберется любой произвольно

    # print("В 'translate_STR_user' передали:")
    # print("         msg_text = ", msg_text)
    # print("         user_id = ", user_id)
    # print("         user_lang = ", user_lang)
    # print("         Chat = ", Chat)
    if msg_text == "":
        return ""

    if user_lang != "":
        # Передали язык на который надо перевести
        word = await translate(msg_text=msg_text, user_lang=user_lang)  # Непосредственный перевод сообщения
        # print("Результат перевода при переданном 'user_lang' в функцию: ",word)
        return word

    if user_id != "":
        # Передали ID пользователя. Ищем языки по нему
        adr = (user_id,)
        # print(adr)
        SQL = "SELECT id as id, lang_id as lang_id FROM users WHERE id = ?"
        if count_lang != 0:
            # Задали лимит возвращаемых языков
            SQL = SQL + "LIMIT " + str(count_lang)
        mycursor = mydb.cursor()
        mycursor.execute(SQL, adr)
        myresult = mycursor.fetchall()  # Можем получить несколько записей
        # print(myresult)
        if myresult is None or myresult == [] or myresult == ():
            # В базе нет такого пользователя. По хорошему надо ему предложить выбрать язык
            # Возвращаем тоже что они и прислал сюда для перевода
            return msg_text
        else:
            # Пользователь найден. Надо перевести на все языки, которые он указал в настройках
            # Предварительно надо прикинуть какой длины будет результирующий текст.
            # Понятно что при переводе количество символов разное, но мы можем понять порядок
            # количества символов. Проблема в том, что телеграм имеет ограничение в 4096
            # знаков. Мы же ограничим его еще больше. Скажем 1000 знаков на все что получится

            # Соберем языки, на которые надо будет переводить
            list_lang = []
            for rec in myresult:
                list_lang.append(rec[1])  # Определили на какой язык надо перевести сообщение (0-ID, 1-язык)

            len_tr = len(msg_text) * len(list_lang)  # Определили примерную длину сообщения,
            # которое получится после перевода

            if len_tr > cfg.MAX_len_srt:  # Ставим ограничение знаков в сообщении
                msg_text_for_trans = cfg.error_str_len
                new_word = cfg.alarm
            else:
                msg_text_for_trans = msg_text
                new_word = ""

            # Создадим список результатов перевода
            list_trans = []
            for user_lang in list_lang:
                # print("Требуется перевод на язык: "user_lang)
                word = await translate(msg_text=msg_text_for_trans,
                                       user_lang=user_lang)  # Непосредственный перевод сообщения
                if word not in list_trans and word != msg_text_for_trans:  # текущего перевода
                    # нет в списке и результат перевода не тоже самое что мы переводили
                    list_trans.append(word)  # Добавим результат в список
                else:  # Такой перевод уже был. И это плохо. Это означает, что переводчик
                    # перестал переводить нам текст.
                    pass

            # start_msg = "… " #Символ, который будет выводиться вначале каждого перевода
            start_msg = "○ "  # Символ, который будет выводиться вначале каждого перевода
            if len(list_lang) == 1 or len(list_trans) == 1:
                start_msg = ""  # Если у нас один язык или результат перевода из одного значения, то
                # мы ничего не выводим

            # Переберем результат перевода и сформируем выходную строку
            for word in list_trans:
                if new_word != "":
                    new_word = new_word + '\n'  # новая строка
                new_word = new_word + start_msg + word

            return new_word


# Отправляет пользователю сообщение
async def Send_message_To_User(msg_text="", user_id="", parse_mode="", reply_to_message_id=0, reply_markup="",
                               disable_notification=False):
    try:
        await bot.send_message(chat_id=user_id, text=msg_text,
                               parse_mode=parse_mode, reply_to_message_id=reply_to_message_id,
                               reply_markup=reply_markup,
                               disable_notification=disable_notification)  # Отправляем сообщение
    except NameError:
        print("Не удалось отправить сообщение '" + msg_text + "' пользователю " + user_id)
        print(NameError)


# Создает markup по ID пользователя или чата
def create_markup(user_id=""):
    markup = ReplyKeyboardMarkup(row_width=5, resize_keyboard=True)

    # Определим языки, которые выбраны для переданного пользователя/чата
    lang_list = []
    adr = (user_id,)
    mycursor.execute("SELECT lang_id as lang_id FROM users WHERE id = ?", adr)  # Ищем в базе пользователя с текущим ID
    myresult = mycursor.fetchall()
    if myresult is None or myresult == [] or myresult == ():
        # pass #Данных нет. Используем ru
        print("Нет выбранных языков для пользователя: ", user_id)
    else:
        # какие-то данные имеются
        # print(myresult)
        for rec in myresult:
            lang_list.append(rec[0])

    # print("Выбранные языки: ", lang_list)
    # print(cfg.LANGDICT)
    for key, lang in cfg.LANGDICT.items():
        if key in lang_list:  # Текущий ключ есть в переданном списке
            lang_desc = lang.replace('◌', '●', 1)  # Отметим как выбранное
            # print(lang_desc)
        else:
            # Оставим как есть
            lang_desc = lang
            # print(lang_desc)
        button = KeyboardButton(lang_desc)
        markup.insert(button)

    return markup


# Создает Inline по ID пользователя или чата
def create_Inline(user_id=""):
    Inline = InlineKeyboardMarkup(row_width=3)

    for key, lang in cfg.LANGDICT.items():
        if key != 'end':
            button = InlineKeyboardButton(lang, callback_data=key)
            Inline.insert(button)

    return Inline


# Проверка что мы данный файл запустили как исполняемый и не импортируем его куда-то
if __name__ == '__main__':
    aiogram.executor.start_polling(dp)

