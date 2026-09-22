import asyncio
import os
import re
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    KeyboardButton,
    Message,
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
        "Не найден BOT_TOKEN.\n"
        "Проверь файл .env"
    )

if not ADMIN_IDS_RAW:
    raise ValueError(
        "Не найден ADMIN_IDS.\n"
        "Проверь файл .env"
    )

try:
    ADMIN_IDS = [
        int(x.strip())
        for x in ADMIN_IDS_RAW.split(",")
        if x.strip()
    ]
except ValueError:
    raise ValueError(
        "ADMIN_IDS должен содержать только числовые Telegram ID.\n"
        "Пример: ADMIN_IDS=123456789,987654321"
    )


# =========================================================
# BOT / DISPATCHER
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher(storage=MemoryStorage())


# =========================================================
# ПРОДУКЦИЯ
# =========================================================

PRODUCTS = {
    "apples_pears": {
        "name": "🍎 Яблоки и груши",
        "description": "Свежие яблоки и груши из сада.",
    },
    "fresh_raspberry": {
        "name": "❤️ Свежая малина",
        "description": "Свежая сезонная малина.",
    },
    "frozen_raspberry": {
        "name": "❄️ Замороженная малина",
        "description": "Замороженная малина.",
    },
    "jam": {
        "name": "🥞 Варенье",
        "description": "Домашнее варенье.",
    },
}


# =========================================================
# УСЛУГИ
# =========================================================

SERVICES = {
    "excursion": {
        "name": "🌳 Прогулки и экскурсии",
    },
    "horses": {
        "name": "🐴 Лошади и карета",
    },
    "fishing": {
        "name": "🎣 Рыбалка",
    },
    "house": {
        "name": "🏡 Аренда дома",
    },
}


# =========================================================
# СОСТОЯНИЯ
# =========================================================

class OrderState(StatesGroup):
    date = State()
    quantity = State()
    name = State()
    phone = State()
    comment = State()


class BookingState(StatesGroup):
    date = State()
    time = State()
    guests = State()
    bath = State()
    name = State()
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
        resize_keyboard=True,
    )


def products_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🍎 Яблоки и груши"),
            ],
            [
                KeyboardButton(text="❤️ Свежая малина"),
            ],
            [
                KeyboardButton(text="❄️ Замороженная малина"),
            ],
            [
                KeyboardButton(text="🥞 Варенье"),
            ],
            [
                KeyboardButton(text="⬅️ Назад"),
            ],
        ],
        resize_keyboard=True,
    )


def services_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🌳 Прогулки и экскурсии"
                ),
            ],
            [
                KeyboardButton(
                    text="🐴 Лошади и карета"
                ),
            ],
            [
                KeyboardButton(
                    text="🎣 Рыбалка"
                ),
            ],
            [
                KeyboardButton(
                    text="🏡 Аренда дома"
                ),
            ],
            [
                KeyboardButton(
                    text="⬅️ Назад"
                ),
            ],
        ],
        resize_keyboard=True,
    )


def phone_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Отправить номер телефона",
                    request_contact=True,
                )
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def confirm_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Всё верно",
                    callback_data="confirm_request",
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Редактировать",
                    callback_data="edit_request",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data="cancel_request",
                )
            ],
        ]
    )


def bath_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Да, хочу баню, чан и гриль-зону",
                    callback_data="bath_yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏡 Только аренда дома",
                    callback_data="bath_no",
                )
            ],
        ]
    )


def house_rules_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Перейти к бронированию",
                    callback_data="house_rules_continue",
                )
            ]
        ]
    )


def price_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Услуги и прайс",
                    url=PRICE_URL,
                )
            ]
        ]
    )


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def parse_house_date_range(value: str):
    """
    Принимает:
    13.01.2026-14.01.2026
    13.01.2026 - 14.01.2026
    """

    value = value.strip()

    match = re.fullmatch(
        r"(\d{2}\.\d{2}\.\d{4})\s*-\s*(\d{2}\.\d{2}\.\d{4})",
        value
    )

    if not match:
        return None

    start_date = match.group(1)
    end_date = match.group(2)

    if not valid_date(start_date):
        return None

    if not valid_date(end_date):
        return None

    start = datetime.strptime(
        start_date,
        "%d.%m.%Y"
    )

    end = datetime.strptime(
        end_date,
        "%d.%m.%Y"
    )

    if end <= start:
        return None

    nights = (end - start).days

    return {
        "date_range": f"{start_date} - {end_date}",
        "check_in": start_date,
        "check_out": end_date,
        "nights": nights,
    }


def normalize_quantity(value: str):
    value = value.strip().lower()

    value = value.replace("кг", "")
    value = value.replace("килограмм", "")
    value = value.replace("килограмма", "")
    value = value.replace("килограммов", "")
    value = value.strip()

    value = value.replace(",", ".")

    if not re.fullmatch(r"\d+(?:\.\d+)?", value):
        return None

    try:
        quantity = float(value)
    except ValueError:
        return None

    if quantity <= 0:
        return None

    if quantity.is_integer():
        return f"{int(quantity)} кг"

    return f"{quantity:g} кг"


async def send_to_admins(text: str) -> bool:
    success = False

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                parse_mode=ParseMode.HTML,
            )

            print(
                f"✅ Заявка успешно отправлена админу {admin_id}"
            )

            success = True

        except Exception as e:
            print(
                f"❌ НЕ УДАЛОСЬ отправить заявку "
                f"админу {admin_id}: {repr(e)}"
            )

    return success


# =========================================================
# /START
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
        "Вы можете ознакомиться со всеми "
        "нашими услугами и прайсом по ссылке:",
        reply_markup=price_menu(),
    )

    await message.answer(
        "Выберите, что вас интересует:",
        reply_markup=main_menu(),
    )


# =========================================================
# /ID
# =========================================================

@dp.message(Command("id"))
async def get_id(message: Message):
    await message.answer(
        "Ваш Telegram ID:\n\n"
        f"<code>{message.from_user.id}</code>"
    )


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

@dp.message(
    F.text == "🍎 Купить плодово-ягодную продукцию"
)
async def open_products(
    message: Message,
    state: FSMContext
):
    await state.clear()

    await message.answer(
        "🍎 <b>Плодово-ягодная продукция</b>\n\n"
        "Выберите товар:",
        reply_markup=products_menu(),
    )


@dp.message(
    F.text == "🌿 Услуги агротуризма"
)
async def open_services(
    message: Message,
    state: FSMContext
):
    await state.clear()

    await message.answer(
        "🌿 <b>Услуги агротуризма</b>\n\n"
        "Выберите услугу:",
        reply_markup=services_menu(),
    )


@dp.message(F.text == "⬅️ Назад")
async def back_to_main(
    message: Message,
    state: FSMContext
):
    await state.clear()

    await message.answer(
        "Главное меню:",
        reply_markup=main_menu(),
    )


# =========================================================
# ПРОДУКЦИЯ
# =========================================================

PRODUCT_BUTTONS = {
    "🍎 Яблоки и груши": "apples_pears",
    "❤️ Свежая малина": "fresh_raspberry",
    "❄️ Замороженная малина": "frozen_raspberry",
    "🥞 Варенье": "jam",
}


@dp.message(
    F.text.in_(PRODUCT_BUTTONS.keys())
)
async def select_product(
    message: Message,
    state: FSMContext
):
    product_key = PRODUCT_BUTTONS[message.text]
    product = PRODUCTS[product_key]

    await state.update_data(
        product_key=product_key,
        product_name=product["name"],
    )

    await state.set_state(
        OrderState.date
    )

    await message.answer(
        f"{product['name']}\n\n"
        f"{product['description']}\n\n"
        "📅 Укажите желаемую дату получения "
        "в формате <b>ДД.ММ.ГГГГ</b>.\n\n"
        "Например: <code>25.06.2026</code>",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(OrderState.date)
async def product_date(
    message: Message,
    state: FSMContext
):
    value = message.text.strip()

    if not valid_date(value):
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>.\n"
            "Например: <code>25.06.2026</code>"
        )
        return

    await state.update_data(
        date=value
    )

    await state.set_state(
        OrderState.quantity
    )

    await message.answer(
        "⚖️ Укажите количество <b>только в килограммах</b>.\n\n"
        "Например:\n"
        "<code>5</code>\n"
        "<code>5 кг</code>\n"
        "<code>5,5 кг</code>"
    )


@dp.message(OrderState.quantity)
async def product_quantity(
    message: Message,
    state: FSMContext
):
    quantity = normalize_quantity(
        message.text
    )

    if quantity is None:
        await message.answer(
            "❌ Не понял количество.\n\n"
            "Укажите количество только в килограммах.\n"
            "Например: <code>5 кг</code> или "
            "<code>5,5 кг</code>."
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


@dp.message(OrderState.name)
async def product_name(
    message: Message,
    state: FSMContext
):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "❌ Пожалуйста, укажите ваше имя."
        )
        return

    await state.update_data(
        name=name
    )

    await state.set_state(
        OrderState.phone
    )

    await message.answer(
        "📱 Оставьте номер телефона:",
        reply_markup=phone_menu(),
    )


@dp.message(
    OrderState.phone,
    F.contact
)
async def product_phone_contact(
    message: Message,
    state: FSMContext
):
    phone = message.contact.phone_number

    await state.update_data(
        phone=phone
    )

    await state.set_state(
        OrderState.comment
    )

    await message.answer(
        "💬 Есть ли комментарий к заказу?\n\n"
        "Если комментария нет, напишите: <b>нет</b>",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(OrderState.phone)
async def product_phone_text(
    message: Message,
    state: FSMContext
):
    phone = message.text.strip()

    if len(phone) < 5:
        await message.answer(
            "❌ Укажите корректный номер телефона."
        )
        return

    await state.update_data(
        phone=phone
    )

    await state.set_state(
        OrderState.comment
    )

    await message.answer(
        "💬 Есть ли комментарий к заказу?\n\n"
        "Если комментария нет, напишите: <b>нет</b>",
        reply_markup=ReplyKeyboardRemove(),
    )


@dp.message(OrderState.comment)
async def product_comment(
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

    summary = (
        "🛒 <b>Проверьте заявку</b>\n\n"
        f"<b>Товар:</b> {data['product_name']}\n"
        f"<b>Дата:</b> {data['date']}\n"
        f"<b>Количество:</b> {data['quantity']}\n"
        f"<b>Имя:</b> {data['name']}\n"
        f"<b>Телефон:</b> {data['phone']}\n"
        f"<b>Комментарий:</b> {data['comment']}\n\n"
        "Всё верно?"
    )

    await message.answer(
        summary,
        reply_markup=confirm_menu(),
    )


# =========================================================
# УСЛУГИ
# =========================================================

SERVICE_BUTTONS = {
    "🌳 Прогулки и экскурсии": "excursion",
    "🐴 Лошади и карета": "horses",
    "🎣 Рыбалка": "fishing",
    "🏡 Аренда дома": "house",
}


@dp.message(
    F.text.in_(SERVICE_BUTTONS.keys())
)
async def select_service(
    message: Message,
    state: FSMContext
):
    service_key = SERVICE_BUTTONS[message.text]
    service = SERVICES[service_key]

    await state.update_data(
        service_key=service_key,
        service_name=service["name"],
    )

    # -----------------------------------------------------
    # ДОМ — СНАЧАЛА ПРАВИЛА
    # -----------------------------------------------------

    if service_key == "house":

        await message.answer(
            "🏡 <b>Аренда дома</b>\n\n"

            "🕑 <b>Заезд:</b> с 14:00\n"
            "🕛 <b>Выезд:</b> до 12:00\n\n"

            "Дополнительный час после выселения "
            "можно приобрести отдельно.\n\n"

            "👨‍👩‍👧‍👦 <b>Вместимость:</b> до 6 человек "
            "(отлично подходит для семьи или двух семей).\n\n"

            "🚫 <b>Ограничения:</b>\n"
            "• строго без животных;\n"
            "• курение внутри дома запрещено.\n\n"

            "🌳 <b>Что входит в стоимость:</b>\n"
            "• проживание;\n"
            "• бесплатный доступ на территорию "
            "Григорьевских садов.\n\n"

            "🔥 <b>Допуслуги и цены:</b>\n"
            "• банный чан — по запросу;\n"
            "• развлечения, еда и услуги комплекса "
            "оплачиваются отдельно;\n"
            "• итоговая цена за ночь зависит "
            "от дня недели.\n\n"

            "Перед бронированием ознакомьтесь "
            "с условиями.",
            reply_markup=house_rules_menu(),
        )

        return

    # Остальные услуги
    await state.set_state(
        BookingState.date
    )

    await message.answer(
        f"{service['name']}\n\n"
        "📅 Укажите желаемую дату "
        "в формате <b>ДД.ММ.ГГГГ</b>.\n\n"
        "Например: <code>25.06.2026</code>",
        reply_markup=ReplyKeyboardRemove(),
    )


# =========================================================
# ПРАВИЛА ДОМА -> БРОНИРОВАНИЕ
# =========================================================

@dp.callback_query(
    F.data == "house_rules_continue"
)
async def house_rules_continue(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    if (
        not data
        or data.get("service_key") != "house"
    ):
        await callback.answer(
            "Начните бронирование заново.",
            show_alert=True,
        )
        return

    await state.set_state(
        BookingState.date
    )

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await callback.answer()

    await callback.message.answer(
        "📅 Укажите период проживания.\n\n"
        "Введите дату заезда и дату выезда "
        "в формате:\n\n"
        "<code>13.01.2026-14.01.2026</code>\n\n"
        "Можно также с пробелами:\n"
        "<code>13.01.2026 - 14.01.2026</code>"
    )


# =========================================================
# ДАТА УСЛУГИ
# =========================================================

@dp.message(BookingState.date)
async def booking_date(
    message: Message,
    state: FSMContext
):
    data = await state.get_data()

    value = message.text.strip()

    # -----------------------------------------------------
    # ДОМ — ДИАПАЗОН ДАТ
    # -----------------------------------------------------

    if data.get("service_key") == "house":

        parsed = parse_house_date_range(
            value
        )

        if parsed is None:
            await message.answer(
                "❌ Неверный формат периода.\n\n"
                "Введите дату заезда и выезда так:\n"
                "<code>13.01.2026-14.01.2026</code>\n\n"
                "Дата выезда должна быть позже "
                "даты заезда."
            )
            return

        await state.update_data(
            date_range=parsed["date_range"],
            check_in=parsed["check_in"],
            check_out=parsed["check_out"],
            nights=parsed["nights"],
        )

        await state.set_state(
            BookingState.guests
        )

        await message.answer(
            f"✅ <b>Период выбран:</b>\n\n"
            f"<b>Заезд:</b> {parsed['check_in']}\n"
            f"<b>Выезд:</b> {parsed['check_out']}\n"
            f"<b>Ночей:</b> {parsed['nights']}\n\n"
            "👥 Сколько будет гостей?"
        )

        return

    # -----------------------------------------------------
    # ОСТАЛЬНЫЕ УСЛУГИ — ОДНА ДАТА
    # -----------------------------------------------------

    if not valid_date(value):
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>.\n"
            "Например: <code>25.06.2026</code>"
        )
        return

    await state.update_data(
        date=value
    )

    await state.set_state(
        BookingState.time
    )

    await message.answer(
        "🕐 Укажите желаемое время.\n\n"
        "Формат: <b>ЧЧ:ММ</b>\n"
        "Например: <code>14:30</code>"
    )


# =========================================================
# ВРЕМЯ ОСТАЛЬНЫХ УСЛУГ
# =========================================================

@dp.message(BookingState.time)
async def booking_time(
    message: Message,
    state: FSMContext
):
    value = message.text.strip()

    if not re.fullmatch(
        r"(?:[01]\d|2[0-3]):[0-5]\d",
        value
    ):
        await message.answer(
            "❌ Неверное время.\n\n"
            "Введите время в формате <b>ЧЧ:ММ</b>.\n"
            "Например: <code>14:30</code>"
        )
        return

    await state.update_data(
        time=value
    )

    await state.set_state(
        BookingState.guests
    )

    await message.answer(
        "👥 Сколько будет гостей?"
    )


# =========================================================
# КОЛИЧЕСТВО ГОСТЕЙ
# =========================================================

@dp.message(BookingState.guests)
async def booking_guests(
    message: Message,
    state: FSMContext
):
    value = message.text.strip()

    if (
        not value.isdigit()
        or int(value) <= 0
    ):
        await message.answer(
            "❌ Укажите количество гостей числом.\n"
            "Например: <code>4</code>"
        )
        return

    guests = int(value)

    data = await state.get_data()

    # Максимум для дома — 6 человек
    if (
        data.get("service_key") == "house"
        and guests > 6
    ):
        await message.answer(
            "❌ Для аренды дома максимальная "
            "вместимость — 6 человек.\n\n"
            "Укажите количество гостей от 1 до 6."
        )
        return

    await state.update_data(
        guests=guests
    )

    # Дом -> дополнительная услуга
    if data.get("service_key") == "house":

        await state.set_state(
            BookingState.bath
        )

        await message.answer(
            "🔥 Хотите дополнительно "
            "баню, чан и гриль-зону?",
            reply_markup=bath_menu(),
        )

        return

    # Остальные услуги -> имя
    await state.set_state(
        BookingState.name
    )

    await message.answer(
        "👤 Как вас зовут?"
    )


# =========================================================
# БАНЯ / ЧАН / ГРИЛЬ
# =========================================================

@dp.callback_query(
    F.data == "bath_yes"
)
async def bath_yes(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    if not data:
        await callback.answer(
            "Эта заявка уже обработана.",
            show_alert=True,
        )
        return

    await state.update_data(
        bath="Да, баня, чан и гриль-зона"
    )

    await state.set_state(
        BookingState.name
    )

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await callback.answer()

    await callback.message.answer(
        "👤 Как вас зовут?"
    )


@dp.callback_query(
    F.data == "bath_no"
)
async def bath_no(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    if not data:
        await callback.answer(
            "Эта заявка уже обработана.",
            show_alert=True,
        )
        return

    await state.update_data(
        bath="Только аренда дома"
    )

    await state.set_state(
        BookingState.name
    )

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await callback.answer()

    await callback.message.answer(
        "👤 Как вас зовут?"
    )


# =========================================================
# ИМЯ
# =========================================================

@dp.message(BookingState.name)
async def booking_name(
    message: Message,
    state: FSMContext
):
    name = message.text.strip()

    if len(name) < 2:
        await message.answer(
            "❌ Пожалуйста, укажите ваше имя."
        )
        return

    await state.update_data(
        name=name
    )

    await state.set_state(
        BookingState.phone
    )

    await message.answer(
        "📱 Оставьте номер телефона:",
        reply_markup=phone_menu(),
    )


# =========================================================
# ТЕЛЕФОН — КОНТАКТ
# =========================================================

@dp.message(
    BookingState.phone,
    F.contact
)
async def booking_phone_contact(
    message: Message,
    state: FSMContext
):
    phone = message.contact.phone_number

    await state.update_data(
        phone=phone
    )

    await state.set_state(
        BookingState.comment
    )

    await message.answer(
        "💬 Есть ли комментарий?\n\n"
        "Если комментария нет, напишите: <b>нет</b>",
        reply_markup=ReplyKeyboardRemove(),
    )


# =========================================================
# ТЕЛЕФОН — ТЕКСТ
# =========================================================

@dp.message(BookingState.phone)
async def booking_phone_text(
    message: Message,
    state: FSMContext
):
    phone = message.text.strip()

    if len(phone) < 5:
        await message.answer(
            "❌ Укажите корректный номер телефона."
        )
        return

    await state.update_data(
        phone=phone
    )

    await state.set_state(
        BookingState.comment
    )

    await message.answer(
        "💬 Есть ли комментарий?\n\n"
        "Если комментария нет, напишите: <b>нет</b>",
        reply_markup=ReplyKeyboardRemove(),
    )


# =========================================================
# КОММЕНТАРИЙ
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

    summary = (
        "🌿 <b>Проверьте заявку</b>\n\n"
        f"<b>Услуга:</b> {data['service_name']}\n"
    )

    # -----------------------------------------------------
    # ДОМ
    # -----------------------------------------------------

    if data["service_key"] == "house":

        summary += (
            f"<b>Период:</b> "
            f"{data['date_range']}\n"
            f"<b>Заезд:</b> "
            f"{data['check_in']} с 14:00\n"
            f"<b>Выезд:</b> "
            f"{data['check_out']} до 12:00\n"
            f"<b>Ночей:</b> "
            f"{data['nights']}\n"
            f"<b>Гостей:</b> "
            f"{data['guests']}\n"
            f"<b>Доп. услуга:</b> "
            f"{data['bath']}\n"
        )

    # -----------------------------------------------------
    # ОСТАЛЬНЫЕ УСЛУГИ
    # -----------------------------------------------------

    else:

        summary += (
            f"<b>Дата:</b> "
            f"{data['date']}\n"
            f"<b>Время:</b> "
            f"{data['time']}\n"
            f"<b>Гостей:</b> "
            f"{data['guests']}\n"
        )

    summary += (
        f"<b>Имя:</b> {data['name']}\n"
        f"<b>Телефон:</b> {data['phone']}\n"
        f"<b>Комментарий:</b> {data['comment']}\n\n"
        "Всё верно?"
    )

    await message.answer(
        summary,
        reply_markup=confirm_menu(),
    )


# =========================================================
# ПОДТВЕРЖДЕНИЕ ЗАЯВКИ
# =========================================================

@dp.callback_query(
    F.data == "confirm_request"
)
async def confirm_request(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    # Защита от повторного нажатия
    if not data:
        await callback.answer(
            "Эта заявка уже обработана.",
            show_alert=True,
        )

        try:
            await callback.message.edit_reply_markup(
                reply_markup=None
            )
        except Exception:
            pass

        return

    username = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else "не указан"
    )

    telegram_id = callback.from_user.id

    # -----------------------------------------------------
    # ПРОДУКЦИЯ
    # -----------------------------------------------------

    if "product_name" in data:

        admin_text = (
            "🛒 <b>НОВАЯ ЗАЯВКА НА ПРОДУКЦИЮ</b>\n\n"
            f"<b>Товар:</b> {data['product_name']}\n"
            f"<b>Дата:</b> {data['date']}\n"
            f"<b>Количество:</b> {data['quantity']}\n"
            f"<b>Имя:</b> {data['name']}\n"
            f"<b>Телефон:</b> {data['phone']}\n"
            f"<b>Комментарий:</b> {data['comment']}\n\n"
            f"<b>Telegram:</b> {username}\n"
            f"<b>Telegram ID:</b> "
            f"<code>{telegram_id}</code>"
        )

    # -----------------------------------------------------
    # УСЛУГИ
    # -----------------------------------------------------

    else:

        admin_text = (
            "🌿 <b>НОВАЯ ЗАЯВКА НА УСЛУГУ</b>\n\n"
            f"<b>Услуга:</b> {data['service_name']}\n"
        )

        # -------------------------------------------------
        # АРЕНДА ДОМА
        # -------------------------------------------------

        if data["service_key"] == "house":

            admin_text += (
                f"<b>Период:</b> "
                f"{data['date_range']}\n"
                f"<b>Заезд:</b> "
                f"{data['check_in']} с 14:00\n"
                f"<b>Выезд:</b> "
                f"{data['check_out']} до 12:00\n"
                f"<b>Количество ночей:</b> "
                f"{data['nights']}\n"
                f"<b>Гостей:</b> "
                f"{data['guests']}\n"
                f"<b>Доп. услуга:</b> "
                f"{data['bath']}\n"
            )

        # -------------------------------------------------
        # ОСТАЛЬНЫЕ УСЛУГИ
        # -------------------------------------------------

        else:

            admin_text += (
                f"<b>Дата:</b> "
                f"{data['date']}\n"
                f"<b>Время:</b> "
                f"{data['time']}\n"
                f"<b>Гостей:</b> "
                f"{data['guests']}\n"
            )

        admin_text += (
            f"<b>Имя:</b> {data['name']}\n"
            f"<b>Телефон:</b> {data['phone']}\n"
            f"<b>Комментарий:</b> {data['comment']}\n\n"
            f"<b>Telegram:</b> {username}\n"
            f"<b>Telegram ID:</b> "
            f"<code>{telegram_id}</code>"
        )

    # Убираем кнопки сразу после нажатия
    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception as e:
        print(
            f"⚠️ Не удалось убрать кнопки: {repr(e)}"
        )

    await callback.answer(
        "Отправляем заявку..."
    )

    # Отправляем администраторам
    success = await send_to_admins(
        admin_text
    )

    # Очищаем состояние
    await state.clear()

    if success:

        await callback.message.answer(
            "✅ <b>Заявка отправлена!</b>\n\n"
            "Спасибо! Мы получили вашу заявку и "
            "свяжемся с вами для подтверждения.",
            reply_markup=main_menu(),
        )

    else:

        await callback.message.answer(
            "⚠️ <b>Не удалось отправить заявку "
            "администратору.</b>\n\n"
            "Пожалуйста, попробуйте ещё раз.",
            reply_markup=main_menu(),
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
    data = await state.get_data()

    if not data:
        await callback.answer(
            "Эта заявка уже обработана.",
            show_alert=True,
        )
        return

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await callback.answer()

    await state.clear()

    if "product_name" in data:

        await callback.message.answer(
            "✏️ Начнём заполнение заявки заново.\n\n"
            "Выберите товар:",
            reply_markup=products_menu(),
        )

    else:

        await callback.message.answer(
            "✏️ Начнём заполнение заявки заново.\n\n"
            "Выберите услугу:",
            reply_markup=services_menu(),
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

    try:
        await callback.message.edit_reply_markup(
            reply_markup=None
        )
    except Exception:
        pass

    await callback.answer(
        "Заявка отменена."
    )

    await callback.message.answer(
        "❌ <b>Заявка отменена.</b>\n\n"
        "Вы можете начать заново.",
        reply_markup=main_menu(),
    )


# =========================================================
# ДИАГНОСТИКА АДМИНА
# =========================================================

async def check_admin_connection():

    print("")
    print("======================================")
    print("🔎 ПРОВЕРКА СВЯЗИ С АДМИНИСТРАТОРОМ")
    print("======================================")

    for admin_id in ADMIN_IDS:

        print("")
        print(
            f"👤 Проверяем ADMIN_ID: {admin_id}"
        )

        try:
            chat = await bot.get_chat(
                admin_id
            )

            print(
                "✅ Telegram ID найден!"
            )

            print(
                f"   ID: {chat.id}"
            )

            print(
                f"   Тип чата: {chat.type}"
            )

            print(
                f"   Имя: "
                f"{chat.first_name or 'не указано'}"
            )

            print(
                f"   Фамилия: "
                f"{chat.last_name or 'не указана'}"
            )

            if chat.username:
                print(
                    f"   Username: "
                    f"@{chat.username}"
                )
            else:
                print(
                    "   Username: отсутствует"
                )

            print("")
            print(
                "📨 Отправляем тестовое сообщение..."
            )

            await bot.send_message(
                chat_id=admin_id,
                text=(
                    "🔔 <b>ТЕСТ СВЯЗИ С БОТОМ</b>\n\n"
                    "Если ты видишь это сообщение "
                    "в личном Telegram — связь "
                    "с администратором работает.\n\n"
                    f"Telegram ID: "
                    f"<code>{admin_id}</code>"
                ),
            )

            print(
                "✅ Тестовое сообщение успешно "
                "передано Telegram."
            )

        except Exception as e:

            print("")
            print(
                "❌ ОШИБКА ПРИ ПРОВЕРКЕ "
                "АДМИНИСТРАТОРА:"
            )

            print(
                repr(e)
            )

    print("")
    print("======================================")
    print("🔎 ПРОВЕРКА ЗАВЕРШЕНА")
    print("======================================")
    print("")


# =========================================================
# MAIN
# =========================================================

async def main():

    print(
        "======================================"
    )

    print(
        "🌳 ГРИГОРЬЕВСКИЕ САДЫ"
    )

    print(
        "🤖 Бот запускается..."
    )

    print(
        f"👤 ADMIN_IDS: {ADMIN_IDS}"
    )

    print(
        "======================================"
    )

    await check_admin_connection()

    await dp.start_polling(bot)


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":
    asyncio.run(main())
