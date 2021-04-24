#подключаем необходимые модули и библиотеки
import time
import re
import math
import random
from datetime import datetime
from datetime import timedelta
import uuid
new_code = uuid.uuid4().hex # генератор шестнадцатиричного кода / купона


import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType, ParseMode, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButtonPollType, PollType, PollAnswer
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Regexp
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import sqlite3

# переменные
bot = Bot(token='1506104835:AAHmaJwI2XLM7vB-JHrnuXJucauwmDBIusQ')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

now = datetime.now()
global is_logo
is_logo = False


#функции баз данных
# функция отправки запросов в базу
def send_to_db(text, input_t):
	conn = sqlite3.connect('game.db')
	cur = conn.cursor()
	cur.execute(text, input_t)
	conn.commit()

# функция получения данных с базы
def get_from_db(text, input_t):
	conn = sqlite3.connect('game.db')
	cur = conn.cursor()
	cur.execute(text, input_t)
	return cur.fetchall()
	conn.commit()

# функция получения юзера из базы данных по ID
def get_user_by_id(sender_id):
	user = get_from_db('SELECT * FROM subscribers WHERE id = ?', (int(sender_id), ))
	return user[0]


# функция проверки подписки
async def check_user_subscribe(sender_id):
	b = await bot.get_chat_member(chat_id='-1001465373630', user_id=sender_id)
	if b.status == 'left':
		return False
	else:
		return True


# функция создания клавиатур
def create_keyboard(keys: list, row_width: int):
	keyboard = []
	for key in keys:
		keyboard.append(KeyboardButton(key))
	return ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=row_width).add(*keyboard)

def create_inline_keyboard(keys: dict, row_width: int):
	keyboard = []
	for key in keys.keys():
		keyboard.append(InlineKeyboardButton(key, callback_data=keys[key]))
	return InlineKeyboardMarkup(one_time_keyboard=True, row_width=row_width).add(*keyboard)


# функция отправки главного сообщения
async def send_main_msg(sender_id):
	list_admins = list()
	admins = get_from_db('SELECT * FROM admins', ())
	for admin in admins:
		list_admins.append(admin[0])
	if int(sender_id) in list_admins:
		main_markup = create_keyboard(['👤 Профиль', '🎮 Игры для получения опыта', '🔗 Реферальные ссылки', '🔁 Перевод уровня в скидки', '📄 Правила', '☑️ Проверить купон', '💬 Отправить сообщение всем пользователям'], 2)
	else:
		main_markup = create_keyboard(['👤 Профиль', '🎮 Игры для получения опыта', '🔗 Реферальные ссылки', '🔁 Перевод уровня в скидки', '📄 Правила'], 2)
	await bot.send_message(sender_id, 'Главное меню', reply_markup=main_markup)

# функция отправки профиля
async def send_profile(sender_id):
	profile_markup = create_keyboard(['🗒 Мои купоны', '↩ Назад в главное меню'], 2)
	finded_user = get_user_by_id(str(sender_id))
	logo = get_user_by_id(str(sender_id))[4]
	max_xp = get_from_db('SELECT * FROM level_data WHERE level = ?', (finded_user[2], ))[0][1]
	if max_xp == 'MAX':
		text = f'<b>🌀 {finded_user[1]} 🌀</b>\n〰️〰️〰️〰️〰️〰️〰️\n📶 Уровень:<code> {finded_user[2]}</code>\n⭐️ Опыт:<code> {max_xp}</code> XP'
	else:
		text = f'<b>🌀 {finded_user[1]} 🌀</b>\n〰️〰️〰️〰️〰️〰️〰️\n📶 Уровень:<code> {finded_user[2]}</code>\n⭐️ Опыт:<code> {finded_user[3]}/{max_xp}</code> XP'

	
	await bot.send_photo(sender_id, logo, caption=text, reply_markup=profile_markup, parse_mode='html')

# функция добавляения опыта
async def add_xp(user_id, xp_plus: int):
	user = get_user_by_id(int(user_id))
	level_user = user[2]
	xp_user = user[3]
	max_xp_for_lvl = int(get_from_db('SELECT * FROM level_data WHERE level = ?', (level_user, ))[0][1])
	sum_xp = xp_user + xp_plus
	if sum_xp >= max_xp_for_lvl:
		while sum_xp >= max_xp_for_lvl:
			max_xp_for_lvl = int(get_from_db('SELECT * FROM level_data WHERE level = ?', (level_user, ))[0][1])
			sum_xp -= max_xp_for_lvl
			level_user += 1
			test = get_from_db('SELECT * FROM level_data WHERE level = ?', (level_user, ))[0][1]
			try:
				int(test)
			except:
				level_user = 50
		if user[5] != 'False' and level_user == 5:
			await bot.send_message(user[5], f'Пользователь <i>{user[1]}</i>, который зарегестрировался по твоей ссылке, достиг 5-го уровня! За это ты получаешь <code>25</code> XP', parse_mode='html')
			await add_xp(user[5], 25)
			await bot.send_message(user_id, 'Ты достиг 5-го уровня! Поздравляю! 🎉')
		elif level_user == 50:
			await bot.send_message(user_id, '🎉 ТЫ ДОСТИГ МАКСИМАЛЬНОГО УРОВНЯ!!!!! 🎉')
		else:
			await bot.send_message(user_id, f'Ты достиг {level_user}-го уровня! Поздравляю! 🎉')
		
		send_to_db('UPDATE subscribers SET level = ? WHERE id = ?', (level_user, int(user_id)))
	send_to_db('UPDATE subscribers SET xp = ? WHERE id = ?', (sum_xp, int(user_id)))
	user = get_user_by_id(int(user_id))
	level_user = user[2]
	xp_user = user[3]
	await send_main_msg(user_id)

# функция виктрины
async def quiz(sender_id, genre: str, count: int):
	if genre == '':
		quizzes = get_from_db('SELECT * FROM quiz', ())
	else:
		quizzes = get_from_db('SELECT * FROM quiz WHERE genre = ?', (genre, ))
	random_question = random.choice(quizzes)
	answers = random_question[2].split(';')
	random.shuffle(answers)
	index_rigth_answer = answers.index(random_question[1])
	if random_question[4] != None:
		await bot.send_photo(sender_id, random_question[4])
	my_quiz = await bot.send_poll(sender_id, f'{count}. {random_question[0]}?', answers, type='quiz', correct_option_id=index_rigth_answer,
		explanation=random_question[3], is_anonymous=False, explanation_parse_mode='html')
	return my_quiz

# функция отправки кода бонуса
async def send_coupon(sender_id, level: int):
	global new_code
	new_code = uuid.uuid4().hex				# генератор шестнадцатиричного кода / купона
	user = get_user_by_id(int(sender_id))
	name = user[1]
	sale = (level/5)*3
	level_user = user[2]
	level_user -= level
	
	if str(sale)[-1] == '0':
		sale_print = int(sale)
	else:
		sale_print = round(sale, 2)
	send_to_db('UPDATE subscribers SET level = ? WHERE id = ?', (level_user, int(sender_id)))
	send_to_db('INSERT INTO coupons VALUES(?, ?, ?, ?, ?)', (new_code, sender_id, name, sale_print, 1))
	await bot.send_message(sender_id, f'Твой уровень снизился до <code>{level_user}-го</code>\nВот код твоего одноразового купона на {sale_print}%:\n<i>(Нажми на код, чтобы скопировать)</i>\n<code>{new_code}</code>.\n\n<i>(При покупке ключа у администратора, пришли этот код ему)</i>', parse_mode='html')
	await send_main_msg(sender_id)

def is_forward(message):
	try:
		from_id = message.forward_from.id
		return from_id
	except AttributeError:
		return False


'''

list_xp_for_levels = list()
for n in range(1, 51):
	num = math.ceil(10 * 1.2 ** (n - 1))
	num_l = int('-' + str(len(str(num)) - 2))
	list_xp_for_levels.append(int(round(num, num_l)))

print(str(list_xp_for_levels) + '/n' + str(len(list_xp_for_levels)))
n = 1
for i in list_xp_for_levels:
	print(i)
	cur.execute('INSERT INTO level_data VALUES(?, ?);', (n, i))
	n += 1				message.poll.correct_option_id
'''

# состояния для FSM
class Form(StatesGroup):
	username = State()
	how_many_level_to_sales = State()
	forwaded_msg = State()
	coupon_form = State()
	msg_send_to_all = State()
	level_rate = State()



@dp.message_handler(regexp=r'/start buy')
async def new_referal_user(message: types.Message, state: FSMContext):
	print('test')
# приветствие для приглашённых по реферальным ссылкам
@dp.message_handler(regexp=r'/start \d{7,12}_referal')
async def new_referal_user(message: types.Message, state: FSMContext):
	if await check_user_subscribe(message.chat.id):
		sender_id = re.findall(r"\d{7,12}", message.text)[0]
		try:
			sender = get_user_by_id(str(sender_id))[1]
			is_new_user = get_from_db('SELECT * FROM subscribers WHERE id = ?', (str(message.chat.id), ))
			global is_referal
			is_referal = str(sender_id)
			if str(sender_id) == str(message.chat.id):
				await message.answer('❌ Ты не можешь пройти по своей же реферальной\nссылке! ❌')
			else:
				if is_new_user == []:
					await message.answer(f'Привет! Ты же от <u>{sender}</u>, правильно?', parse_mode='html')
					await message.answer('Давай знакомиться!')
					time.sleep(0.75)
					await message.answer('Представься!')
					await bot.send_message(sender_id, 'По вашей ссылке перешли и сейчас регистрируются!')
					await Form.username.set()
				else:
					await message.answer(f'❌ Ты уже зарегестрирован! Передай <i>{sender}</i>,\nчтобы по его ссылкам регестрировались <b>НОВЫЕ</b> пользователи! ❌', parse_mode='html')
		except IndexError:
			await message.answer('❌ Некорректная ссылка ❌')
	else:
		await message.answer('Для того чтобы пользоваться этим ботом, необходимо быть подписаным на канал', reply_markup=InlineKeyboardMarkup(row_width=2, one_time_keyboard=True).add(InlineKeyboardButton('Подписаться', url='https://t.me/joinchat/p8RgHuKqCH8xZjhi')))


# приветсвие
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
	if await check_user_subscribe(message.chat.id):
		await message.answer('Привет!')
		finded_user = get_from_db('SELECT * FROM subscribers WHERE id = ?', (str(message.chat.id), ))
		
		if finded_user == []:
			global is_referal
			is_referal = 'False'
			await message.answer('Ты же новичок, да?\nТогда давай знакомиться!')
			time.sleep(0.75)
			await message.answer('Представься!')
			await Form.username.set()
		else:
			await message.answer('Как приятно вернутся домой! Скажи?')
			await send_main_msg(message.chat.id)
	else:
		await message.answer('Для того чтобы пользоваться этим ботом, необходимо быть подписаным на канал', reply_markup=InlineKeyboardMarkup(row_width=2, one_time_keyboard=True).add(InlineKeyboardButton('Подписаться', url='https://t.me/joinchat/p8RgHuKqCH8xZjhi')))


# обработка фото
@dp.message_handler(content_types=ContentType.PHOTO)
async def new_photo(message: types.Message):
	if await check_user_subscribe(message.chat.id):
		if get_user_by_id(message.chat.id)[4] == None:
			name = get_user_by_id(message.chat.id)[1]
			send_to_db('DELETE FROM subscribers WHERE id = ?', (message.chat.id, ))
			new_user = (str(message.chat.id), name, 1, 0, message.photo[0]['file_id'], is_referal)
			send_to_db('INSERT INTO subscribers VALUES(?, ?, ?, ?, ?, ?);', new_user)
			await send_main_msg(message.chat.id)
			is_logo = False
		else:
			print(message.photo[0].file_id)
	else:
		await message.answer('Для того чтобы пользоваться этим ботом, необходимо быть подписаным на канал', reply_markup=InlineKeyboardMarkup(row_width=2, one_time_keyboard=True).add(InlineKeyboardButton('Подписаться', url='https://t.me/joinchat/p8RgHuKqCH8xZjhi')))



# создание клавиатур
cancel_markup = create_keyboard(['🚫 Отмена'], 1)
games_markup = create_keyboard(['❔ Викторины ❓', '🎲 Игра на удачу', '↩ Назад в главное меню'], 2)
quiz_markup = create_keyboard(['🔫 Викторина по боевикам (Макс. +14 XP)', '👾 Викторина по старым играм (Макс. +14 XP)', '👻 Викторина по хоррорам (Макс. +14 XP)', '🎯 Викторина по приключениям (Макс. +14 XP)', '🧱 Викторина по симуляторам (Макс. +14 XP)', '🏁 Викторина по спортивным играм (Макс. +14 XP)', '🕹 Викторина по всем жанрам (Макс. +20 XP)', '↩ Назад в меню игор'], 1)


# обработка текста
@dp.message_handler(content_types=ContentType.TEXT)
async def message_send(message: types.Message):
	if await check_user_subscribe(message.chat.id):
		if message.text == '👤 Профиль':
			await send_profile(message.chat.id)
		elif message.text == '🎮 Игры для получения опыта':
			await message.answer('Во что сыграем?', reply_markup=games_markup)
		elif message.text == '❔ Викторины ❓':
			await message.answer('В какую викторину ты хочешь поиграть?', reply_markup=quiz_markup)
		elif message.text == '↩ Назад в меню игор':
			await message.answer('Возвращаюсь в предыдущее меню...', reply_markup=games_markup)
		elif message.text == '🏁 Викторина по спортивным играм (Макс. +14 XP)':
			global max_question
			max_question = 7
			global count_correct
			count_correct = 0
			global count
			count = 1
			global genre
			genre = 'sport'
			global this_quiz
			this_quiz = await quiz(message.chat.id, genre, count)
		elif message.text == '🎯 Викторина по приключениям (Макс. +14 XP)':
			max_question = 7
			count_correct = 0
			count = 1
			genre = 'action'
			this_quiz = await quiz(message.chat.id, genre, count)
		elif message.text == '🔫 Викторина по боевикам (Макс. +14 XP)':
			max_question = 7
			count_correct = 0
			count = 1
			genre = 'thriller'
			this_quiz = await quiz(message.chat.id, genre, count)
		elif message.text == '👾 Викторина по старым играм (Макс. +14 XP)':
			max_question = 7
			count_correct = 0
			count = 1
			genre = 'old'
			this_quiz = await quiz(message.chat.id, genre, count)
		elif message.text == '👻 Викторина по хоррорам (Макс. +14 XP)':
			max_question = 7
			count_correct = 0
			count = 1
			genre = 'horror'
			this_quiz = await quiz(message.chat.id, genre, count)
		elif message.text == '🧱 Викторина по симуляторам (Макс. +14 XP)':
			max_question = 7
			count_correct = 0
			count = 1
			genre = 'simulator'
			this_quiz = await quiz(message.chat.id, genre, count)
		elif message.text == '🕹 Викторина по всем жанрам (Макс. +20 XP)':
			max_question = 7
			count_correct = 0
			count = 1
			genre = ''
			this_quiz = await quiz(message.chat.id, genre, count)


		elif message.text == '🎲 Игра на удачу':
			await message.answer('<b>Правила</b>\n\nТы выбираешь сколько своих уровней ты хочешь поставить (<i>Минимум — 2</i>), и с вероятностью <code>50%</code>, ты либо теряешь свои уровни, либо удваиваешь их', parse_mode='html')
			time.sleep(0.75)
			await message.answer(f'Сколько уровней ты хочешь поставить?\n(Сейчас у тебя {get_user_by_id(message.chat.id)[2]} уровней)', reply_markup=cancel_markup)
			await Form.level_rate.set()


		elif message.text == '🔗 Реферальные ссылки':
			referal_links_markup = create_keyboard(['🆕 Генерировать реферальную ссылку', '↩ Назад в главное меню'], 1)
			await message.answer('Что ты хочешь сделать?', reply_markup=referal_links_markup)
		elif message.text == '🆕 Генерировать реферальную ссылку':
			ref_link_markup = create_inline_keyboard({'🌐 Копировать':'copy_ref_link'}, 1)
			global result_url
			result_url = f'https://t.me/game_sales_keys_bot?start={message.chat.id}_referal'
			await message.answer(f'<a href="{result_url}">Вот</a> ссылка', parse_mode='html', reply_markup=ref_link_markup)

		elif message.text == '🔁 Перевод уровня в скидки':

			await message.answer('Сколько уровней ты хочешь перевести в сыкидку?\n<i>(минимум — 5 уроней)</i>', parse_mode='html', reply_markup=cancel_markup)
			await Form.how_many_level_to_sales.set()
		elif message.text == '☑️ Проверить купон':
			list_admins = list()
			admins = get_from_db('SELECT * FROM admins', ())
			for admin in admins:
				list_admins.append(admin[0])
			if message.chat.id in list_admins:
				await message.answer('Перешлите сообщение пользователя, в котором он прислал купон', reply_markup=cancel_markup)
				await Form.forwaded_msg.set()
			else:
				pass
		elif message.text == '🗒 Мои купоны':
			
			coupons = get_from_db('SELECT * FROM coupons WHERE owner_id=?', (message.chat.id, ))
			global list_coupons
			list_coupons = list()
			for coupon in coupons:
				list_coupons.append(f'{coupon[3]}% — {coupon[0]}')
			if len(list_coupons) == 0:
				await message.answer('У тебя пока нет купонов', reply_markup=create_keyboard(['🗒 Мои купоны', '↩ Назад в главное меню'], 2))
			else:
				global coupons_markup
				coupons_markup = create_keyboard(list_coupons, row_width=1).add('🚫 Отмена')
				await message.answer('Вот список твоих купонов:', reply_markup=coupons_markup)
				close_markup = create_inline_keyboard({'Закрыть список моих купонов':'close_list'}, row_width=1)
				
				await message.answer('Закрыть?', reply_markup=close_markup)
				await Form.coupon_form.set()
		elif message.text == '💬 Отправить сообщение всем пользователям':
			list_admins = list()
			admins = get_from_db('SELECT * FROM admins', ())
			for admin in admins:
				list_admins.append(admin[0])
			if message.chat.id in list_admins:
				await message.answer('Отправьте сообщение, которое нужно написать всем польззователям бота', reply_markup=cancel_markup)
				await Form.msg_send_to_all.set()
			else:
				pass

		elif message.text == '↩ Назад в главное меню':
			await send_main_msg(message.chat.id)
	else:
		await message.answer('Для того чтобы пользоваться этим ботом, необходимо быть подписаным на канал', reply_markup=InlineKeyboardMarkup(row_width=2, one_time_keyboard=True).add(InlineKeyboardButton('Подписаться', url='https://t.me/joinchat/p8RgHuKqCH8xZjhi')))




@dp.poll_answer_handler()
async def handle_poll_answer(quiz_answer: PollAnswer):
	global this_quiz
	if this_quiz.poll.correct_option_id == quiz_answer.option_ids[0]:
		global count_correct
		count_correct += 1
	else:
		pass
	global count
	count += 1
	global max_question
	if count > max_question:
		if count_correct == max_question:
			await bot.send_message(quiz_answer.user.id, f'💯 Ты <u>ИДЕАЛЬНО</u> прошёл викторину! Тебе начислено <code>{count_correct*2}</code> XP 🏆', parse_mode='html')
		else:
			if math.ceil(max_question/2) > count_correct:
				emoji = '📉'
			else:
				emoji = '📈'
			await bot.send_message(quiz_answer.user.id, f'{emoji} Твой результат: <code>{count_correct}/{max_question}</code>. Тебе начислено <code>{count_correct*2}</code> XP 🎉', parse_mode='html')
		await add_xp(quiz_answer.user.id, count_correct*2)
	else:
		await bot.send_chat_action(quiz_answer.user.id, 'typing')
		time.sleep(1.5)
		global genre
		this_quiz = await quiz(quiz_answer.user.id, genre, count)



# обработка запросов машины сосояний

#добавляем возможность отмены, если пользователь передумал заполнять
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='🚫 Отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
	current_state = await state.get_state()
	await state.finish()

	msg = await message.reply('Отменяю')
	text = msg.text
	start_text = msg.text
	time.sleep(0.3)
	i = 1
	while i < 12:
		if i == 4 or i == 8:
			text = start_text
		else:
			text = text + '.'
		await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text)
		time.sleep(0.3)
		i += 1
	await send_main_msg(message.chat.id)



@dp.message_handler(state=Form.username)
async def new_username_process(message: types.Message, state: FSMContext):
	is_name_taken = get_from_db('SELECT * FROM subscribers WHERE username = ?', (message.text, ))
	if is_name_taken == []:
		global new_name
		new_name = message.text
		await message.answer('Отлично! А теперь пришли мне свою будущую аватарку')
		new_user = (str(message.chat.id), message.text, 1, 0, None, is_referal)
		send_to_db('INSERT INTO subscribers VALUES(?, ?, ?, ?, ?, ?);', new_user)
		await state.finish()
	else:
		await message.answer('Это имя уже занято!')
		await message.answer('Представься!')
		await Form.username.set()



@dp.message_handler(lambda message: message.text.isdigit() == False, state=Form.how_many_level_to_sales)
async def process_how_many_level_to_sales_invalid1(message: types.Message):
	return await message.answer('❌ Это не число! ❌')

@dp.message_handler(lambda message: int(message.text) > get_user_by_id(message.chat.id)[2], state=Form.how_many_level_to_sales)
async def process_how_many_level_to_sales_invalid2(message: types.Message):
	return await message.answer('❌ Нельзя перевести больше уровней, чем у тебя есть! ❌')

@dp.message_handler(lambda message: int(message.text) < 5, state=Form.how_many_level_to_sales)
async def process_how_many_level_to_sales_invalid3(message: types.Message):
	await message.answer('❌ нельзя переводить меньше 5-ти уровней ❌')

@dp.message_handler(state=Form.how_many_level_to_sales)
async def new_level_process(message: types.Message, state: FSMContext):
	await send_coupon(message.chat.id, int(message.text))
	await state.finish()



@dp.message_handler(lambda message: is_forward(message) == False, state=Form.forwaded_msg)
async def forward_msg_process_inavalid(message: types.Message, state: FSMContext):
	return await message.answer('❌ Это не пересланное сообщение ❌')

@dp.message_handler(state=Form.forwaded_msg)
async def forward_msg_process(message: types.Message, state: FSMContext):
	from_id = is_forward(message)
	owner = get_from_db('SELECT * FROM coupons WHERE id = ?', (message.text, ))
	try:
		owner = owner[0]
		global coupon_id
		coupon_id = message.text
		if message.forward_from.id == owner[1]:
			use_markup = create_inline_keyboard({'Использовать этот купон':'use_coupon'}, 1)
			await message.answer(f'✅ Купон действительно принадлежит пользователю {owner[2]} ✅', reply_markup=use_markup)
		else:
			await message.answer('❌ Этот купона не принадлежит человеку, который его присваивает ❌')
	except IndexError:
		await message.answer('❌ Такой купон не зарегестрирован ❌')
	await send_main_msg(message.chat.id)
	await state.finish()



@dp.message_handler(lambda message: message.text not in list_coupons, state=Form.coupon_form)
async def coupon_process_inavalid(message: types.Message, state: FSMContext):
	return await message.answer('Такого купона нет. Выбери купон кнопкой на клавиатуре', reply_markup=coupons_markup)

@dp.message_handler(state=Form.coupon_form)
async def coupon_process(message: types.Message, state: FSMContext):
	copy_code_markup = create_inline_keyboard({'🔗 Скопировать код купона':'copy_code_coupon'}, row_width=1)
	await message.answer('Скопировать этот купон?', reply_markup=copy_code_markup)
	global new_code
	new_code = message.text[message.text.rindex(' ') + 1:]
	await state.finish()



@dp.message_handler(state=Form.msg_send_to_all)
async def send_msg_process(message: types.Message, state: FSMContext):
	text = message.text
	subscribers = get_from_db('SELECT * FROM subscribers', ())
	await bot.send_chat_action(message.chat.id, 'typing')
	for subsriber in subscribers:
		await bot.send_message(subsriber[0], text)
	time.sleep(0.5)
	await message.answer('Готово!')
	await state.finish()



@dp.message_handler(lambda message: message.text.isdigit() == False, state=Form.level_rate)
async def process_level_rate_invalid1(message: types.Message):
	return await message.answer('❌ Это не число! ❌')

@dp.message_handler(lambda message: int(message.text) < 2, state=Form.level_rate)
async def process_level_rate_invalid1(message: types.Message):
	return await message.answer('❌ Минимальный уровень для ставки — <code>2</code> ❌', parse_mode='html')

@dp.message_handler(lambda message: int(message.text) > get_user_by_id(message.chat.id)[2], state=Form.level_rate)
async def process_level_rate_invalid1(message: types.Message):
	return await message.answer('❌ Нельзя поставить больше уровней, чем у тебя есть ❌', parse_mode='html')

@dp.message_handler(state=Form.level_rate)
async def level_rate_process(message: types.Message, state: FSMContext):
	user = get_user_by_id(message.chat.id)
	global level_user
	level_user = user[2]
	global rate
	rate = int(message.text)
	if rate == level_user:
		sure_markup = create_inline_keyboard({'✅ Продолжить':'yes_sure', '❌ Отменить':'no_sure'}, row_width=2)
		await message.answer('Ты уверен, что хочешь поставить ВСЕ свои уровни?', reply_markup=sure_markup)
	else:
		await bot.send_chat_action(message.chat.id, 'typing')
		list_result = ['win', 'lose']
		result = random.choice(list_result)
		time.sleep(5)
		if result == 'win':
			new_level = level_user + rate
			if new_level > 50:
				new_level = 50
			await message.answer(f'🎉 Ты победил! Поздравляю!\nТвой новый уровень — <code>{new_level}</code> 🎉', parse_mode='html', reply_markup=games_markup)
			send_to_db('UPDATE subscribers SET level = ? WHERE id = ?', (new_level, int(message.chat.id)))
		else:
			new_level = level_user - rate
			if new_level < 1:
				new_level = 1
			await message.answer(f'😢 Прости, но ты проиграл\nТвой новый уровень — <code>{new_level}</code> 😢', parse_mode='html', reply_markup=games_markup)
			send_to_db('UPDATE subscribers SET level = ? WHERE id = ?', (new_level, int(message.chat.id)))
	await state.finish()



#функции для инлайн кнопок
@dp.callback_query_handler(lambda c:c.data == 'copy_ref_link')
async def process_callback_button1(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)
	await bot.send_message(callback_query.from_user.id, f'<code>{result_url}</code>', disable_web_page_preview=True, parse_mode='html')

@dp.callback_query_handler(lambda c:c.data == 'copy_code_coupon')
async def process_callback_button2(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)
	profile_markup = create_keyboard(['🗒 Мои купоны', '↩ Назад в главное меню'], 2)
	await bot.send_message(callback_query.from_user.id, f'<code>{new_code}</code>', parse_mode='html', reply_markup=profile_markup)

@dp.callback_query_handler(lambda c:c.data == 'close_list')
async def process_callback_button3(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)
	profile_markup = create_keyboard(['🗒 Мои купоны', '↩ Назад в главное меню'], 2)
	await bot.send_message(callback_query.from_user.id, 'Закрываю...', reply_markup=profile_markup)

@dp.callback_query_handler(lambda c:c.data == 'use_coupon')
async def process_callback_button4(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)
	list_admins = list()
	admins = get_from_db('SELECT * FROM admins', ())
	for admin in admins:
		list_admins.append(admin[0])
	if int(callback_query.from_user.id) in list_admins:
		main_markup = create_keyboard(['👤 Профиль', '🎮 Игры для получения опыта', '🔗 Реферальные ссылки', '🔁 Перевод уровня в скидки', '📄 Правила', '☑️ Проверить купон', '💬 Отправить сообщение всем пользователям'], 2)
	else:
		main_markup = create_keyboard(['👤 Профиль', '🎮 Игры для получения опыта', '🔗 Реферальные ссылки', '🔁 Перевод уровня в скидки', '📄 Правила'], 2)
	send_to_db('DELETE FROM coupons WHERE id = ?', (coupon_id, ))
	await bot.send_message(callback_query.from_user.id, 'Купон успешно удалён', reply_markup=main_markup)

@dp.callback_query_handler(lambda c:c.data == 'yes_sure')
async def process_callback_button45(callback_query: types.CallbackQuery):
	await bot.answer_callback_query(callback_query.id)
	await bot.send_chat_action(callback_query.from_user.id, 'typing')
	list_result = ['win', 'lose']
	result = random.choice(list_result)
	time.sleep(5)
	if result == 'win':
		new_level = level_user + rate
		if new_level > 50:
			new_level = 50
		await bot.send_message(callback_query.from_user.id, f'🎉 Ты победил! Поздравляю!\nТвой новый уровень — <code>{new_level}</code> 🎉', parse_mode='html', reply_markup=games_markup)
		send_to_db('UPDATE subscribers SET level = ? WHERE id = ?', (new_level, int(callback_query.from_user.id)))
	else:
		new_level = level_user - rate
		if new_level < 1:
			new_level = 1
		await bot.send_message(callback_query.from_user.id, f'😢 Прости, но ты проиграл\nТвой новый уровень — <code>{new_level}</code> 😢', parse_mode='html', reply_markup=games_markup)
		send_to_db('UPDATE subscribers SET level = ? WHERE id = ?', (new_level, int(callback_query.from_user.id)))

@dp.callback_query_handler(lambda c:c.data == 'no_sure')
async def process_callback_button45(callback_query: types.CallbackQuery):
	await bot.send_message(callback_query.from_user.id, 'Правильный выбор', reply_markup=games_markup)

#запускаем поллинг
if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True)