import asyncio
import os
import re
from datetime import datetime, date

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import (
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from dotenv import load_dotenv


# =========================================================
# НАСТРОЙКИ
# =========================================================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")

PRICE_URL = "https://teletype.in/@grigorievskiysad/RJVYKJYPjC_"


if not BOT_TOKEN:
    raise ValueError(
        "Не найден BOT_TOKEN. Проверь переменную окружения."
    )


if not ADMIN_IDS_RAW:
    raise ValueError(
        "Не найден ADMIN_IDS. Проверь переменную окружения."
    )


ADMIN_IDS = [
    int(x.strip())
    for x in ADMIN_IDS_RAW.split(",")
    if x.strip()
]


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher(
    storage=MemoryStorage()
)


# =========================================================
# СОСТОЯНИЯ
# =========================================================

class OrderState(StatesGroup):

    product = State()
    subtype = State()
    category = State()
    quantity = State()

    name = State()
    contact_method = State()
    phone = State()
    comment = State()


class BookingState(StatesGroup):

    service = State()
    date = State()
    time = State()
    guests = State()

    name = State()
    contact_method = State()
    phone = State()
    comment = State()


# =========================================================
# КЛАВИАТУРЫ
# =========================================================

def main_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🍎 Купить плодово-ягодную продукцию"
                )
            ],
            [
                KeyboardButton(
                    text="🌿 Услуги агротуризма"
                )
            ],
        ],
        resize_keyboard=True
    )


def products_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="🍎 Яблоки и груши"
                )
            ],

            [
                KeyboardButton(
                    text="❤️ Свежая малина"
                )
            ],

            [
                KeyboardButton(
                    text="❄️ Замороженная малина"
                )
            ],

            [
                KeyboardButton(
                    text="Варенье"
                )
            ],

            [
                KeyboardButton(
                    text="⬅️ Назад"
                )
            ]

        ],
        resize_keyboard=True
    )


def apples_pears_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="🍎 Яблоки"
                )
            ],

            [
                KeyboardButton(
                    text="🍐 Груши"
                )
            ],

            [
                KeyboardButton(
                    text="⬅️ Назад"
                )
            ]

        ],
        resize_keyboard=True
    )


def category_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="1 категория"
                )
            ],

            [
                KeyboardButton(
                    text="2 категория"
                )
            ],

            [
                KeyboardButton(
                    text="3 категория"
                )
            ],

            [
                KeyboardButton(
                    text="Техническая (на переработку)"
                )
            ]

        ],
        resize_keyboard=True
    )


def raspberry_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="Отборная"
                )
            ],

            [
                KeyboardButton(
                    text="1 категория"
                )
            ],

            [
                KeyboardButton(
                    text="2 категория"
                )
            ],

            [
                KeyboardButton(
                    text="3 категория"
                )
            ]

        ],
        resize_keyboard=True
    )


def frozen_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="175 г — отборная"
                )
            ],

            [
                KeyboardButton(
                    text="300 г — отборная"
                )
            ],

            [
                KeyboardButton(
                    text="500 г — 1 категория"
                )
            ],

            [
                KeyboardButton(
                    text="850 г — 1 категория"
                )
            ],

            [
                KeyboardButton(
                    text="1,8 кг — 1 категория"
                )
            ]

        ],
        resize_keyboard=True
    )


def jam_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="Варенье из сливы 250 мл"
                )
            ],

            [
                KeyboardButton(
                    text="Варенье из малины 185 мл"
                )
            ],

            [
                KeyboardButton(
                    text="Варенье из малины 250 мл"
                )
            ],

            [
                KeyboardButton(
                    text="Варенье из малины 350 мл"
                )
            ],

            [
                KeyboardButton(
                    text="Варенье жимолость 250 мл"
                )
            ]

        ],
        resize_keyboard=True
    )


def contact_method_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="📞 Телефон"
                )
            ],

            [
                KeyboardButton(
                    text="💬 Переписка"
                )
            ]

        ],
        resize_keyboard=True
    )


def phone_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить номер телефона",
                    request_contact=True
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def confirm_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✅ Всё верно",
                    callback_data="confirm_request"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✏️ Редактировать",
                    callback_data="edit_request"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_request"
                )
            ]

        ]
    )


def services_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="🌳 Прогулки и экскурсии"
                )
            ],

            [
                KeyboardButton(
                    text="🐴 Лошади и карета"
                )
            ],

            [
                KeyboardButton(
                    text="🎣 Рыбалка"
                )
            ],

            [
                KeyboardButton(
                    text="🏡 Аренда дома"
                )
            ],

            [
                KeyboardButton(
                    text="⬅️ Назад"
                )
            ]

        ],
        resize_keyboard=True
    )


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def normalize_number(value):

    value = value.lower().strip()

    value = (
        value
        .replace("кг", "")
        .replace("банок", "")
        .replace("банки", "")
        .replace("банка", "")
        .replace("шт", "")
        .replace(",", ".")
        .strip()
    )

    if not re.fullmatch(
        r"\d+(?:\.\d+)?",
        value
    ):
        return None

    return value


def validate_date(value):

    try:

        selected_date = datetime.strptime(
            value.strip(),
            "%d.%m.%Y"
        ).date()

    except ValueError:

        return None

    return selected_date


def validate_time(value):

    value = value.strip()

    if not re.fullmatch(
        r"(?:[01]\d|2[0-3]):[0-5]\d",
        value
    ):
        return None

    try:

        selected_time = datetime.strptime(
            value,
            "%H:%M"
        ).time()

    except ValueError:

        return None

    return selected_time


async def send_to_admins(text):

    result = False

    for admin_id in ADMIN_IDS:

        try:

            await bot.send_message(
                chat_id=admin_id,
                text=text
            )

            result = True

        except Exception as e:

            print(
                f"Ошибка отправки админу {admin_id}: {e}"
            )

    return result


# =========================================================
# START
# =========================================================

@dp.message(CommandStart())
async def start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🌳 <b>Григорьевские сады</b>\n\n"
        "Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu()
    )


@dp.message(Command("id"))
async def get_id(message: Message):

    await message.answer(
        f"Ваш Telegram ID:\n\n"
        f"<code>{message.from_user.id}</code>"
    )


# =========================================================
# ПРОДУКЦИЯ
# =========================================================

@dp.message(
    F.text == "🍎 Купить плодово-ягодную продукцию"
)
async def products_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🍎 Выберите продукцию:",
        reply_markup=products_menu()
    )


# =========================================================
# ЯБЛОКИ И ГРУШИ
# =========================================================

@dp.message(
    F.text == "🍎 Яблоки и груши"
)
async def apples_start(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        product="Яблоки и груши"
    )

    await message.answer(
        "Выберите:",
        reply_markup=apples_pears_menu()
    )


@dp.message(
    F.text.in_(
        [
            "🍎 Яблоки",
            "🍐 Груши"
        ]
    )
)
async def choose_fruit(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        subtype=message.text
    )

    await state.set_state(
        OrderState.category
    )

    await message.answer(
        "Выберите категорию:",
        reply_markup=category_menu()
    )


# =========================================================
# МАЛИНА СВЕЖАЯ
# =========================================================

@dp.message(
    F.text == "❤️ Свежая малина"
)
async def fresh_raspberry_start(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        product="Свежая малина"
    )

    await state.set_state(
        OrderState.category
    )

    await message.answer(
        "Выберите качество:",
        reply_markup=raspberry_menu()
    )


# =========================================================
# ЗАМОРОЖЕННАЯ МАЛИНА
# =========================================================

@dp.message(
    F.text == "❄️ Замороженная малина"
)
async def frozen_start(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        product="Замороженная малина"
    )

    await message.answer(
        "Выберите упаковку:",
        reply_markup=frozen_menu()
    )


# =========================================================
# ВАРЕНЬЕ
# =========================================================

@dp.message(
    F.text == "Варенье"
)
async def jam_start(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        product="Варенье"
    )

    await message.answer(
        "Выберите вариант:",
        reply_markup=jam_menu()
    )


# =========================================================
# СОХРАНЕНИЕ КАТЕГОРИИ
# =========================================================

@dp.message(
    F.text.in_(
        [
            "1 категория",
            "2 категория",
            "3 категория",
            "Техническая (на переработку)",
            "Отборная"
        ]
    )
)
async def save_category(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    await state.update_data(
        category=message.text
    )

    await state.set_state(
        OrderState.quantity
    )

    if data.get("product") == "Свежая малина":

        await message.answer(
            "⚖️ Укажите количество свежей малины в кг:\n\n"
            "Например: 5",
            reply_markup=ReplyKeyboardRemove()
        )

        return

    await message.answer(
        "⚖️ Укажите количество в кг:\n\n"
        "Например: 5",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ЗАМОРОЖЕННАЯ МАЛИНА — УПАКОВКА
# =========================================================

@dp.message(
    F.text.in_(
        [
            "175 г — отборная",
            "300 г — отборная",
            "500 г — 1 категория",
            "850 г — 1 категория",
            "1,8 кг — 1 категория"
        ]
    )
)
async def save_frozen_package(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        package=message.text
    )

    await state.set_state(
        OrderState.quantity
    )

    await message.answer(
        "🔢 Сколько упаковок хотите заказать?",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ВАРЕНЬЕ — ВАРИАНТ
# =========================================================

@dp.message(
    F.text.in_(
        [
            "Варенье из сливы 250 мл",
            "Варенье из малины 185 мл",
            "Варенье из малины 250 мл",
            "Варенье из малины 350 мл",
            "Варенье жимолость 250 мл"
        ]
    )
)
async def save_jam(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        package=message.text
    )

    await state.set_state(
        OrderState.quantity
    )

    await message.answer(
        "🔢 Сколько банок хотите заказать?",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# КОЛИЧЕСТВО
# =========================================================

@dp.message(OrderState.quantity)
async def order_quantity(
    message: Message,
    state: FSMContext
):

    quantity = normalize_number(
        message.text
    )

    if not quantity:

        await message.answer(
            "❌ Укажите количество числом.\n\n"
            "Например: 5"
        )

        return

    await state.update_data(
        quantity=quantity
    )

    await state.set_state(
        OrderState.name
    )

    await message.answer(
        "👤 Как вас зовут?"
    )


# =========================================================
# ИМЯ ЗАКАЗА
# =========================================================

@dp.message(OrderState.name)
async def order_name(
    message: Message,
    state: FSMContext
):

    if len(message.text.strip()) < 2:

        await message.answer(
            "Введите имя."
        )

        return

    await state.update_data(
        name=message.text.strip()
    )

    await state.set_state(
        OrderState.contact_method
    )

    await message.answer(
        "Как удобнее с вами связаться?",
        reply_markup=contact_method_menu()
    )


# =========================================================
# СПОСОБ СВЯЗИ — ЗАКАЗ
# =========================================================

@dp.message(OrderState.contact_method)
async def order_contact_method(
    message: Message,
    state: FSMContext
):

    if message.text not in [
        "📞 Телефон",
        "💬 Переписка"
    ]:

        await message.answer(
            "Пожалуйста, выберите один из вариантов:",
            reply_markup=contact_method_menu()
        )

        return

    await state.update_data(
        contact_method=message.text
    )

    if message.text == "📞 Телефон":

        await state.set_state(
            OrderState.phone
        )

        await message.answer(
            "📱 Оставьте номер телефона:",
            reply_markup=phone_menu()
        )

        return

    await state.update_data(
        phone="Не требуется"
    )

    await state.set_state(
        OrderState.comment
    )

    await message.answer(
        "💬 Комментарий к заказу?\n\n"
        "Если нет — напишите: нет",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ТЕЛЕФОН — ЗАКАЗ
# =========================================================

@dp.message(
    OrderState.phone,
    F.contact
)
async def order_phone_contact(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.contact.phone_number
    )

    await state.set_state(
        OrderState.comment
    )

    await message.answer(
        "💬 Комментарий к заказу?\n\n"
        "Если нет — напишите: нет",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(OrderState.phone)
async def order_phone_text(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.text.strip()
    )

    await state.set_state(
        OrderState.comment
    )

    await message.answer(
        "💬 Комментарий к заказу?\n\n"
        "Если нет — напишите: нет",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# КОММЕНТАРИЙ И ФОРМА ЗАКАЗА
# =========================================================

@dp.message(OrderState.comment)
async def order_comment(
    message: Message,
    state: FSMContext
):

    comment = message.text.strip()

    if comment.lower() == "нет":
        comment = "Нет"

    await state.update_data(
        comment=comment
    )

    data = await state.get_data()

    text = (
        "🛒 <b>Проверьте заявку</b>\n\n"
        f"<b>Товар:</b> {data.get('product')}\n"
        f"<b>Вид:</b> {data.get('subtype', '-')}\n"
        f"<b>Категория:</b> {data.get('category', '-')}\n"
        f"<b>Упаковка:</b> {data.get('package', '-')}\n"
        f"<b>Количество:</b> {data.get('quantity')}\n\n"
        f"<b>Имя:</b> {data.get('name')}\n"
        f"<b>Способ связи:</b> {data.get('contact_method')}\n"
        f"<b>Телефон:</b> {data.get('phone')}\n"
        f"<b>Комментарий:</b> {data.get('comment')}\n\n"
        "Всё верно?"
    )

    await message.answer(
        text,
        reply_markup=confirm_menu()
    )


# =========================================================
# АГРОТУРИЗМ
# =========================================================

@dp.message(
    F.text == "🌿 Услуги агротуризма"
)
async def services_start(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "🌿 Выберите услугу:",
        reply_markup=services_menu()
    )


@dp.message(
    F.text.in_(
        [
            "🌳 Прогулки и экскурсии",
            "🐴 Лошади и карета",
            "🎣 Рыбалка",
            "🏡 Аренда дома"
        ]
    )
)
async def choose_service(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        service=message.text
    )

    await state.set_state(
        BookingState.date
    )

    await message.answer(
        "📅 Укажите желаемую дату:\n\n"
        "Например:\n"
        "<code>25.06.2026</code>",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ПРОВЕРКА ДАТЫ
# =========================================================

@dp.message(BookingState.date)
async def booking_date(
    message: Message,
    state: FSMContext
):

    selected_date = validate_date(
        message.text
    )

    if selected_date is None:

        await message.answer(
            "❌ Не удалось распознать дату.\n\n"
            "Введите дату в формате:\n"
            "<code>25.06.2026</code>"
        )

        return

    today = date.today()

    if selected_date < today:

        await message.answer(
            "❌ Нельзя выбрать прошедшую дату.\n\n"
            "Укажите сегодняшнюю или будущую дату."
        )

        return

    await state.update_data(
        date=message.text.strip()
    )

    await state.set_state(
        BookingState.time
    )

    await message.answer(
        "🕐 Укажите желаемое время:\n\n"
        "Например:\n"
        "<code>14:00</code>"
    )


# =========================================================
# ПРОВЕРКА ВРЕМЕНИ
# =========================================================

@dp.message(BookingState.time)
async def booking_time(
    message: Message,
    state: FSMContext
):

    selected_time = validate_time(
        message.text
    )

    if selected_time is None:

        await message.answer(
            "❌ Неверное время.\n\n"
            "Введите время в формате:\n"
            "<code>14:00</code>\n\n"
            "Часы: от 00 до 23\n"
            "Минуты: от 00 до 59"
        )

        return

    await state.update_data(
        time=message.text.strip()
    )

    await state.set_state(
        BookingState.guests
    )

    await message.answer(
        "👥 Сколько будет гостей?"
    )


# =========================================================
# ГОСТИ
# =========================================================

@dp.message(BookingState.guests)
async def booking_guests(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        guests=message.text.strip()
    )

    await state.set_state(
        BookingState.name
    )

    await message.answer(
        "👤 Как вас зовут?"
    )


# =========================================================
# ИМЯ БРОНИ
# =========================================================

@dp.message(BookingState.name)
async def booking_name(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        name=message.text.strip()
    )

    await state.set_state(
        BookingState.contact_method
    )

    await message.answer(
        "Как удобнее с вами связаться?",
        reply_markup=contact_method_menu()
    )


# =========================================================
# СПОСОБ СВЯЗИ — БРОНЬ
# =========================================================

@dp.message(BookingState.contact_method)
async def booking_contact_method(
    message: Message,
    state: FSMContext
):

    if message.text not in [
        "📞 Телефон",
        "💬 Переписка"
    ]:

        await message.answer(
            "Пожалуйста, выберите один из вариантов:",
            reply_markup=contact_method_menu()
        )

        return

    await state.update_data(
        contact_method=message.text
    )

    if message.text == "📞 Телефон":

        await state.set_state(
            BookingState.phone
        )

        await message.answer(
            "📱 Оставьте номер телефона:",
            reply_markup=phone_menu()
        )

        return

    await state.update_data(
        phone="Не требуется"
    )

    await state.set_state(
        BookingState.comment
    )

    await message.answer(
        "💬 Есть комментарий?\n\n"
        "Если нет — напишите: нет",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# ТЕЛЕФОН — БРОНЬ
# =========================================================

@dp.message(
    BookingState.phone,
    F.contact
)
async def booking_phone_contact(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.contact.phone_number
    )

    await state.set_state(
        BookingState.comment
    )

    await message.answer(
        "💬 Есть комментарий?\n\n"
        "Если нет — напишите: нет",
        reply_markup=ReplyKeyboardRemove()
    )


@dp.message(BookingState.phone)
async def booking_phone(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        phone=message.text.strip()
    )

    await state.set_state(
        BookingState.comment
    )

    await message.answer(
        "💬 Есть комментарий?\n\n"
        "Если нет — напишите: нет",
        reply_markup=ReplyKeyboardRemove()
    )


# =========================================================
# КОММЕНТАРИЙ И ФОРМА БРОНИ
# =========================================================

@dp.message(BookingState.comment)
async def booking_comment(
    message: Message,
    state: FSMContext
):

    comment = message.text.strip()

    if comment.lower() == "нет":
        comment = "Нет"

    await state.update_data(
        comment=comment
    )

    data = await state.get_data()

    text = (
        "🌿 <b>Проверьте заявку</b>\n\n"
        f"<b>Услуга:</b> {data.get('service')}\n"
        f"<b>Дата:</b> {data.get('date')}\n"
        f"<b>Время:</b> {data.get('time')}\n"
        f"<b>Гостей:</b> {data.get('guests')}\n\n"
        f"<b>Имя:</b> {data.get('name')}\n"
        f"<b>Способ связи:</b> {data.get('contact_method')}\n"
        f"<b>Телефон:</b> {data.get('phone')}\n"
        f"<b>Комментарий:</b> {data.get('comment')}\n\n"
        "Всё верно?"
    )

    await message.answer(
        text,
        reply_markup=confirm_menu()
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ
# =========================================================

@dp.callback_query(
    F.data == "confirm_request"
)
async def confirm_request(
    callback: CallbackQuery,
    state: FSMContext
):

    data = await state.get_data()

    username = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else "нет"
    )

    text = ""

    # =====================================================
    # ЗАКАЗ ПРОДУКЦИИ
    # =====================================================

    if data.get("product"):

        text = (
            "🛒 <b>НОВАЯ ЗАЯВКА ПРОДУКЦИЯ</b>\n\n"
            f"<b>Товар:</b> {data.get('product')}\n"
            f"<b>Вид:</b> {data.get('subtype', '-')}\n"
            f"<b>Категория:</b> {data.get('category', '-')}\n"
            f"<b>Упаковка:</b> {data.get('package', '-')}\n"
            f"<b>Количество:</b> {data.get('quantity')}\n\n"
            f"<b>Имя:</b> {data.get('name')}\n"
            f"<b>Способ связи:</b> {data.get('contact_method')}\n"
            f"<b>Телефон:</b> {data.get('phone')}\n"
            f"<b>Комментарий:</b> {data.get('comment')}\n\n"
            f"Telegram: {username}\n"
            f"ID: <code>{callback.from_user.id}</code>"
        )

    # =====================================================
    # АГРОТУРИЗМ
    # =====================================================

    else:

        text = (
            "🌿 <b>НОВАЯ ЗАЯВКА АГРОТУРИЗМ</b>\n\n"
            f"<b>Услуга:</b> {data.get('service')}\n"
            f"<b>Дата:</b> {data.get('date')}\n"
            f"<b>Время:</b> {data.get('time')}\n"
            f"<b>Гостей:</b> {data.get('guests')}\n\n"
            f"<b>Имя:</b> {data.get('name')}\n"
            f"<b>Способ связи:</b> {data.get('contact_method')}\n"
            f"<b>Телефон:</b> {data.get('phone')}\n"
            f"<b>Комментарий:</b> {data.get('comment')}\n\n"
            f"Telegram: {username}\n"
            f"ID: <code>{callback.from_user.id}</code>"
        )

    sent = await send_to_admins(text)

    await state.clear()

    await callback.answer()

    if sent:

        await callback.message.answer(
            "✅ <b>Заявка отправлена!</b>\n\n"
            "Мы свяжемся с вами для подтверждения.",
            reply_markup=main_menu()
        )

    else:

        await callback.message.answer(
            "⚠️ Не удалось отправить заявку.\n\n"
            "Пожалуйста, попробуйте ещё раз.",
            reply_markup=main_menu()
        )


# =========================================================
# РЕДАКТИРОВАНИЕ
# =========================================================

@dp.callback_query(
    F.data == "edit_request"
)
async def edit_request(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.answer()

    await callback.message.answer(
        "✏️ Начнём заново.\n\n"
        "Выберите раздел:",
        reply_markup=main_menu()
    )


# =========================================================
# ОТМЕНА
# =========================================================

@dp.callback_query(
    F.data == "cancel_request"
)
async def cancel_request(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.answer(
        "Заявка отменена"
    )

    await callback.message.answer(
        "❌ Заявка отменена.",
        reply_markup=main_menu()
    )


# =========================================================
# НАЗАД
# =========================================================

@dp.message(
    F.text == "⬅️ Назад"
)
async def back(
    message: Message,
    state: FSMContext
):

    await state.clear()

    await message.answer(
        "Главное меню:",
        reply_markup=main_menu()
    )


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    print(
        "🌳 Григорьевские сады бот запущен"
    )

    print(
        f"ADMIN IDS: {ADMIN_IDS}"
    )

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
