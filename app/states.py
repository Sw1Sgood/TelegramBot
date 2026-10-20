from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    language = State()
    name = State()
    birth_date = State()
    birth_time = State()
    birth_city = State()


class ProfileEdit(StatesGroup):
    value = State()


class ReadingFlow(StatesGroup):
    question = State()


class InsightFlow(StatesGroup):
    partner_date = State()
    dream = State()
