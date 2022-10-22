from aiogram.types import Message, ReplyKeyboardRemove, Contact
from aiogram.dispatcher import FSMContext

from keyboards.buttons import (
    native_languages_markup,
    share_phone_markup,
    accents_markup,
    genders_markup,
    start_markup,
    register_markup,
    age_markup
    )
from utils.uzbekvoice.helpers import register_user
from utils.uzbekvoice import db
from utils.helpers import send_message
from main import UserRegistration, dp
from utils.uzbekvoice.helpers import check_if_correct_year, native_language


# Answer to all bot commands
@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    chat_id = message.chat.id

    if db.user_exists(chat_id):
        await send_message(chat_id, 'welcome-text', markup=start_markup)
    else:
        await UserRegistration.full_name.set()
        await send_message(chat_id, 'start', markup=register_markup)


@dp.message_handler(commands=['start'], state='*')
async def start_command(message: Message):
    chat_id = message.chat.id

    if db.user_exists(chat_id):
        await send_message(chat_id, 'welcome-text', markup=start_markup)
    else:
        await UserRegistration.full_name.set()
        await send_message(chat_id, 'start', markup=register_markup)


# Answer to all bot commands
@dp.message_handler(text="👤 Ro'yxatdan o'tish")
async def start_command(message: Message):
    chat_id = message.chat.id
    await UserRegistration.full_name.set()
    await send_message(chat_id, 'ask-full-name')
        

@dp.message_handler(state=UserRegistration.full_name)
async def get_name(message: Message, state: FSMContext):
    chat_id = message.chat.id
    async with state.proxy() as data:
        data["tg_id"] = chat_id
        data["full_name"] = message.text
        await UserRegistration.next()
        await send_message(chat_id, 'ask-phone', markup=share_phone_markup)


@dp.message_handler(state=UserRegistration.full_name)
async def get_name(message: Message, state: FSMContext):
    chat_id = message.chat.id
    async with state.proxy() as data:
        data["tg_id"] = chat_id
        data["full_name"] = message.text
        await UserRegistration.next()
        await send_message(chat_id, 'ask-phone', markup=share_phone_markup)


@dp.message_handler(state=UserRegistration.phone_number, content_types=['contact', 'text'])
async def get_phone(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["phone_number"] = str(message.contact.phone_number)
        await UserRegistration.next()
        await send_message(data['tg_id'], 'ask-gender', markup=genders_markup)


@dp.inline_handler()
@dp.message_handler(state=UserRegistration.gender)
async def get_gender(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text == 'Erkak':
            data["gender"] = "M"
        elif message.text == 'Ayol':
            data["gender"] = "F"

    await UserRegistration.next()
    await send_message(data["tg_id"], 'ask-accent', markup=accents_markup)


@dp.message_handler(state=UserRegistration.accent_region)
async def get_accent_region(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["accent_region"] = message.text

    await send_message(data["tg_id"], 'ask-birth-year', markup=age_markup)
    await UserRegistration.next()


@dp.message_handler(state=UserRegistration.year_of_birth)
async def get_birth_year(message: Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text in ["12-17", "18-24", "25-34", "35-..."]:
            data["year_of_birth"] = message.text
            await send_message(data["tg_id"], 'ask-native-language', markup=native_languages_markup)
            await UserRegistration.next()
        else:
            await send_message(data["tg_id"], 'ask-birth-year-again')
            return await UserRegistration.year_of_birth.set()
        await UserRegistration.next()


@dp.message_handler(state=UserRegistration.finish)
async def finish(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data["native_language"] = native_language(message.text)

    await register_user(data)
    await send_message(data["tg_id"], 'register-success', markup=start_markup)
    await state.finish()
