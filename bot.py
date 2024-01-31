import telebot, database as db, buttons as bt
from geopy import Nominatim

# Создать объект бота
bot = telebot.TeleBot('6712141501:AAEyRoq6IJ7e-XF4q4PULCMHK4URNuEq_xc')
# Использование карт
geolocator = Nominatim(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/121.0.0.0 Safari/537.36')
# Временные данные
users = {}
admin_id = 791555605

# Обработка команды start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    # Проверка пользователя
    check = db.checker(user_id)
    if check:
        products = db.get_pr_but()
        bot.send_message(user_id, f'Добро пожаловать, {message.from_user.first_name}👋',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(user_id, f'Выберите пункт меню:',
                         reply_markup=bt.main_menu_buttons(products))
    else:
        bot.send_message(user_id, "Здравствуйте, добро пожаловать👋\n Давайте начнем "
                                  "регистрацию, введите свое имя!")
        # Переход на этап получения имени
        bot.register_next_step_handler(message, get_name)


# Этап получения имени
def get_name(message):
    name = message.text
    user_id = message.from_user.id
    bot.send_message(user_id, "Отлично, а теперь отправьте номер!",
                     reply_markup=bt.num_bt())
    # Этап получения номера
    bot.register_next_step_handler(message, get_number, name)


# Этап получения номера
def get_number(message, name):
    user_id = message.from_user.id
    # Если юзер отправил номер по кнопке
    if message.contact:
        number = message.contact.phone_number
        bot.send_message(user_id, 'Супер! Последний этап: отправьте локацию',
                         reply_markup=bt.loc_bt())
        # Этап получения локации
        bot.register_next_step_handler(message, get_location, name, number)
    # Если юзер отправил номер не по кнопке
    else:
        bot.send_message(user_id, 'Отправьте номер через кнопку',
                         reply_markup=bt.num_bt())
        # Этап получения номера
        bot.register_next_step_handler(message, get_number, name)

# Этап получения локации
def get_location(message, name, number):
    user_id = message.from_user.id
    # Если юзер отправил локацию по кнопке
    if message.location:
        location = str(geolocator.reverse(f'{message.location.latitude}, '
                                      f'{message.location.longitude}'))
        db.register(user_id, name, number, location)
        products = db.get_pr_but()
        bot.send_message(user_id, 'Регистрация прошла успешно👍',
                         reply_markup=bt.main_menu_buttons(products))
    # Если юзер отправил локацию не по кнопке
    else:
        bot.send_message(user_id, 'Отправьте локацию через кнопку',
                         reply_markup=bt.loc_bt())
        # Этап получения номера
        bot.register_next_step_handler(message, get_location, name, number)


# Функция выбора количества
@bot.callback_query_handler(lambda call: call.data in ['back', 'to_cart', 'increment', 'decrement'])
def choose_count(call):
    chat_id = call.message.chat.id

    if call.data == 'increment':
        count = users[chat_id]['pr_amount']
        users[chat_id]['pr_amount'] += 1
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id,
                                      reply_markup=bt.choose_pr_count(count, 'increment'))
    elif call.data == 'decrement':
        count = users[chat_id]['pr_amount']
        users[chat_id]['pr_amount'] -= 1
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id,
                                      reply_markup=bt.choose_pr_count(count, 'decrement'))
    elif call.data == 'back':
        products = db.get_pr_but()
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        bot.send_message(chat_id, 'Возвращаю вас обратно в меню',
                         reply_markup=bt.main_menu_buttons(products))
    elif call.data == 'to_cart':
        products = db.get_pr(users[chat_id]['pr_name'])
        prod_amount = users[chat_id]['pr_amount']
        user_total = products[4] * prod_amount

        db.add_pr_to_cart(chat_id, products[0], prod_amount, user_total)
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        bot.send_message(chat_id, 'Товар успешно добавлен в корзину, ваши действия?',
                         reply_markup=bt.cart_buttons())


# Корзина
@bot.callback_query_handler(lambda call: call.data in ['cart', 'back', 'order', 'clear', 'trash', 'feedback'])
def cart_handle(call):
    chat_id = call.message.chat.id
    products = db.get_pr_but()

    if call.data == 'clear':
        db.clear_cart(chat_id)
        bot.edit_message_text('Ваша корзина пуста, выберите новый товар', chat_id=chat_id,
                              message_id=call.message.message_id, reply_markup=bt.main_menu_buttons(products))
    elif call.data == 'order':
        group_id = -4151609363
        cart = db.make_order(chat_id)
        text = f'Новый заказ!\n\n' \
               f'Имя пользователя: @{call.message.chat.username}\n' \
               f'Товар: {cart[0][1]}\n' \
               f'Количество: {cart[0][2]}\n' \
               f'Итого: {cart[0][3]}\n\n' \
               f'Адрес: {cart[1][0]}'
        bot.send_message(group_id, text)
        bot.edit_message_text('Спасибо за оформление заказа, специалисты скоро с вами свяжутся!',
                              chat_id=chat_id, message_id=call.message.message_id,
                              reply_markup=bt.main_menu_buttons(products))
    elif call.data == 'back':
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        bot.send_message(chat_id, 'Возвращаю вас обратно в меню',
                         reply_markup=bt.main_menu_buttons(products))
    elif call.data == 'cart':
        cart = db.show_cart(chat_id)
        if cart:
            text = f'Ваша корзина:\n\n' \
                   f'Товар: {cart[0]}\n' \
                   f'Количество: {cart[1]}\n' \
                   f'Итого: {cart[2]}\n\n' \
                   f'Что хотите сделать?'
            bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
            bot.send_message(chat_id, text, reply_markup=bt.cart_buttons())
        else:
            products = db.get_pr_but()
            bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
            bot.send_message(chat_id, 'Ваша корзина пуста!', reply_markup=bt.main_menu_buttons(products))
    elif call.data == 'trash':
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        bot.send_message(chat_id, 'Спасибо вам за то, что решили помочь с очищением города, мы очень это ценим! Вы '
                                  'можете приехать в наш филиал для сдачи мусора👇')
        bot.send_location(chat_id=chat_id, latitude=41.31070101309289, longitude=69.24906232208943,
                          reply_markup=bt.back_button())
    elif call.data == 'feedback':
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        bot.send_message(chat_id, 'Для связи с оператором вы можете позвонить по номеру\n'
                                  '+998933952165\n'
                                  'Или написать нам в телеграм @prosto_kamich!', reply_markup=bt.back_button())



# Вывод информации о продукте
@bot.callback_query_handler(lambda call: int(call.data) in db.get_pr_name_id())
def get_user_product(call):
    chat_id = call.message.chat.id
    prod = db.get_pr(int(call.data))
    users[chat_id] = {'pr_name': call.data, 'pr_amount': 1}
    bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
    text = f'Название товара: {prod[0]}\n' \
           f'Описание товара: {prod[1]}\n' \
           f'Количество на складе: {prod[2]}\n' \
           f'Цена: {prod[4]} сум'

    bot.send_photo(chat_id, photo=prod[3], caption=text, reply_markup=bt.choose_pr_count())


# Обработка команды admin
@bot.message_handler(commands=['admin'])
def act(message):
    if message.from_user.id == admin_id:
        bot.send_message(admin_id, 'Выберите действие', reply_markup=bt.admin_menu())
        # Переход на этап выбора
        bot.register_next_step_handler(message, admin_choose)
    else:
        bot.send_message(message.from_user.id, 'Вы не админ!')

# Выбор действия админом
def admin_choose(message):
    if message.text == 'Добавить продукт':
        bot.send_message(admin_id, 'Напишите название продукта!',
                         reply_markup=telebot.types.ReplyKeyboardRemove())
        # Переход на этап получения названия
        bot.register_next_step_handler(message, get_pr_name)
    elif message.text == 'Удалить продукт':
        check = db.check_pr()
        if check:
            bot.send_message(admin_id, 'Напишите id продукта!',
                             reply_markup=telebot.types.ReplyKeyboardRemove())
            # Переход на этап получения названия
            bot.register_next_step_handler(message, get_pr_id)
        else:
            bot.send_message(admin_id, 'Продуктов в базе пока нет!',)
            # Возврат на этап выбора
            bot.register_next_step_handler(message, admin_choose)
    elif message.text == 'Изменить продукт':
        check = db.check_pr()
        if check:
            bot.send_message(admin_id, 'Напишите id продукта!',
                             reply_markup=telebot.types.ReplyKeyboardRemove())
            # Переход на этап получения названия
            bot.register_next_step_handler(message, get_pr_change)
        else:
            bot.send_message(admin_id, 'Продуктов в базе пока нет!',)
            # Возврат на этап выбора
            bot.register_next_step_handler(message, admin_choose)
    elif message.text == 'Перейти в меню':
        products = db.get_pr_but()
        bot.send_message(admin_id, 'Ок!',
                        reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.send_message(admin_id, 'Добро пожаловать в меню!',
                         reply_markup=bt.main_menu_buttons(products))
    else:
        bot.send_message(admin_id, 'Неизвестная операция', reply_markup=bt.admin_menu())
        # Возврат на этап выбора
        bot.register_next_step_handler(message, admin_choose)
    
# Этап получения названия продукта
def get_pr_name(message):
    if message.text:
        pr_name = message.text
        bot.send_message(admin_id, 'Отлично, теперь придумайте описание!')
        # Переход на этап получения описания
        bot.register_next_step_handler(message, get_pr_des, pr_name)
    else:
        bot.send_message(admin_id, 'Отправьте названия товара в виде текста!')
        # Возврат на этап получения названия
        bot.register_next_step_handler(message, get_pr_name)

# Этап получения описания
def get_pr_des(message, pr_name):
    if message.text:
        pr_des = message.text
        bot.send_message(admin_id, 'Теперь введите количество товара')
        # Переход на этап получения кол-ва
        bot.register_next_step_handler(message, get_pr_count, pr_name, pr_des)
    else:
        bot.send_message(admin_id, 'Отправьте описание товара в виде текста!')
        # Возврат на этап получения описания
        bot.register_next_step_handler(message, get_pr_des, pr_name)

# Этап получения кол-ва
def get_pr_count(message, pr_name, pr_des):
    try:
        pr_count = int(message.text)
        bot.send_message(admin_id, 'А сейчас перейдите на сайт https://postimages.org/ru/, загрузите фото '
                                   'товара и отправьте прямую ссылка на него!')
        # Переход на этап получения фото
        bot.register_next_step_handler(message, get_pr_photo, pr_name, pr_des, pr_count)
    except ValueError or telebot.apihelper.ApiTelegramException:
        bot.send_message(admin_id, 'Ошибка в количестве, попытайтесь еще раз!')
        # Возврат на этап получения кол-ва
        bot.register_next_step_handler(message, get_pr_count, pr_name, pr_des)

# Этап получения фото
def get_pr_photo(message, pr_name, pr_des, pr_count):
    if message.text:
        pr_photo = message.text
        bot.send_message(admin_id, 'Супер, последний штрих: какова цена товара?')
        # Переход на этап получения цены
        bot.register_next_step_handler(message, get_pr_price, pr_name, pr_des, pr_count, pr_photo)
    else:
        bot.send_message(admin_id, 'Некорректная ссылка!')
        # Возврат на этап получения фото
        bot.register_next_step_handler(message, get_pr_photo, pr_name, pr_des, pr_count)


# Этап получения цены
def get_pr_price(message, pr_name, pr_des, pr_count, pr_photo):
    try:
        pr_price = float(message.text)
        db.add_pr(pr_name, pr_des, pr_count, pr_photo, pr_price)
        bot.send_message(admin_id, 'Продукт успешно добавлен, хотите что-то еще?',
                         reply_markup=bt.admin_menu())
        # Переход на этап выбора
        bot.register_next_step_handler(message, admin_choose)
    except ValueError or telebot.apihelper.ApiTelegramException:
        bot.send_message(admin_id, 'Ошибка в цене, попытайтесь еще раз!')
        # Возврат на этап получения цены
        bot.register_next_step_handler(message, get_pr_price, pr_name, pr_des, pr_count, pr_photo)


# Этап удаления продукта:
def get_pr_id(message):
    try:
        pr_id = int(message.text)
        check = db.check_pr_id(pr_id)
        if check:
            db.del_pr(pr_id)
            bot.send_message(admin_id, 'Продукт удален успешно, что-то еще?',
                             reply_markup=bt.admin_menu())
            # Переход на этап выбора
            bot.register_next_step_handler(message, admin_choose)
        else:
            bot.send_message(admin_id, 'Такого продукта нет!')
            # Возврат на этап получения id
            bot.register_next_step_handler(message, get_pr_id)
    except ValueError or telebot.apihelper.ApiTelegramException:
        bot.send_message(admin_id, 'Ошибка в id, попытайтесь еще раз!')
        # Возврат на этап получения id
        bot.register_next_step_handler(message, get_pr_id)


# Этап изменения кол-ва товара
def get_pr_change(message):
    try:
        pr_id = int(message.text)
        check = db.check_pr_id(pr_id)
        if check:
            bot.send_message(admin_id, 'Сколько товара прибыло?',)
            # Переход на этап прихода
            bot.register_next_step_handler(message, get_amount, pr_id)
        else:
            bot.send_message(admin_id, 'Такого продукта нет!')
            # Возврат на этап получения id
            bot.register_next_step_handler(message, get_pr_change)
    except ValueError or telebot.apihelper.ApiTelegramException:
        bot.send_message(admin_id, 'Ошибка в id, попытайтесь еще раз!')
        # Возврат на этап получения id
        bot.register_next_step_handler(message, get_pr_change)


# Этап прихода
def get_amount(message, pr_id):
    try:
        new_amount = int(message.text)
        db.change_pr_count(pr_id, new_amount)
        bot.send_message(admin_id, 'Кол-во продукта изменено успешно, что-то еще?',
                         reply_markup=bt.admin_menu())
        # Переход на этап выбора
        bot.register_next_step_handler(message, admin_choose)
    except ValueError or telebot.apihelper.ApiTelegramException:
        bot.send_message(admin_id, 'Ошибка в количестве, попытайтесь еще раз!')
        # Возврат на этап получения id
        bot.register_next_step_handler(message, get_amount, pr_id)


# Запуск бота
bot.polling(non_stop=True)

