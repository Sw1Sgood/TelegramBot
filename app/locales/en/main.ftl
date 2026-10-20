## Onboarding

start-greeting =
    ✨ Hi! This is «{ $bot_name }» — your personal astrologer.
    I make tarot readings, horoscopes and numerology reports just for you, based on your birth date and our past readings.

    <i>All of this is for entertainment and self-reflection, not an exact prediction of the future.</i>

choose-language = Выбери язык / Choose your language:
language-changed = Done, we'll talk in English now 🇬🇧

ask-name = What's your name? Tell me how I should call you.
btn-use-tg-name = Call me «{ $name }»

ask-birth-date =
    Nice to meet you, { $name }! 🌙
    When is your birthday? Send the date as <b>DD.MM.YYYY</b>, for example <code>25.03.1995</code>.

ask-birth-time =
    Do you know your time of birth? Send it as <b>HH:MM</b>, for example <code>14:30</code>.
    It makes readings more precise, but you can skip it.

ask-birth-city =
    Which city were you born in?
    This is optional too — feel free to skip.

btn-skip = Skip ➡️

profile-ready =
    All set, { $name }! Here's what the stars and numbers say:

    { $sign_emoji } Your zodiac sign is <b>{ $sign }</b>
    🔢 Your life path number is <b>{ $life_path }</b>
    <i>{ $life_path_description }</i>

daily-card-teaser = 🃏 Your first Card of the Day is being shuffled — it will appear here very soon.

welcome-back = Welcome back, { $name }! ✨

## Input errors

error-name = Please send a name — up to 50 characters, at least one letter.
error-city = A city name should be 2 to 100 characters long.
error-date-format = I couldn't read that date. Please send it like this: <code>25.03.1995</code>
error-date-invalid = This date doesn't exist — please check the day and month.
error-date-future = That date hasn't happened yet 🙂 Please check the year.
error-date-too-old = That date is too early — please check the year.
error-time-format = I couldn't read that time. Please send it like this: <code>14:30</code>
error-text-expected = Please send your answer as text.

## Zodiac signs

zodiac-aries = Aries
zodiac-taurus = Taurus
zodiac-gemini = Gemini
zodiac-cancer = Cancer
zodiac-leo = Leo
zodiac-virgo = Virgo
zodiac-libra = Libra
zodiac-scorpio = Scorpio
zodiac-sagittarius = Sagittarius
zodiac-capricorn = Capricorn
zodiac-aquarius = Aquarius
zodiac-pisces = Pisces

## Life path number

lifepath-1 = The leader and pioneer: you need to follow your own path and start new things.
lifepath-2 = The diplomat and peacemaker: your strength lies in sensitivity, partnership and listening.
lifepath-3 = The creator and inspirer: you shine through self-expression, communication and joy.
lifepath-4 = The builder: reliability, order and persistence help you create something solid.
lifepath-5 = The freedom seeker: change, travel and new experiences guide you.
lifepath-6 = The guardian: care, harmony and a warm home are your foundation and calling.
lifepath-7 = The sage: you are drawn to depth, knowledge and the search for meaning.
lifepath-8 = The strategist: you have a talent for business, influence and material success.
lifepath-9 = The humanitarian: compassion, broad views and caring for the world are close to you.
lifepath-11 = Master number of intuition: a subtle sense and the gift of inspiring others.
lifepath-22 = Master number of the master builder: turning big dreams into reality.
lifepath-33 = Master number of the teacher: a path of love, care and mentoring.

## Main menu

main-menu-title = 🔮 Main menu — what would you like to explore?
menu-daily-card = 🃏 Card of the Day
menu-question = ❓ Ask a question
menu-spreads = 🌟 Big spreads
menu-horoscope = ♈ Horoscope
menu-compatibility = 💞 Compatibility
menu-numerology = 🔢 Numerology
menu-dreams = 🌙 Dream reading
menu-diary = 📖 My diary
menu-profile = 👤 Profile
menu-invite = 🎁 Invite a friend
coming-soon = ✨ This section is coming very soon!
need-onboarding = Let's get to know each other first — tap /start

## Profile

profile-card =
    <b>👤 Your profile</b>

    Name: { $name }
    Date of birth: { $birth_date }
    Time of birth: { $birth_time }
    City of birth: { $birth_city }
    Zodiac sign: { $sign_emoji } { $sign }
    Life path number: { $life_path }

    Language: { $language }
    Time zone: { $timezone }
    Card of the Day arrives at: { $daily_time }
    Morning message: { $notifications }
    Plan: { $plan }

profile-not-set = not set
profile-tz-moscow = Moscow (MSK)
plan-free = free
notif-on = on
notif-off = off

btn-edit-name = ✏️ Name
btn-edit-birth-date = 📅 Date of birth
btn-edit-birth-time = 🕰 Time of birth
btn-edit-birth-city = 🏙 City of birth
btn-edit-daily-time = ⏰ Card of the Day time
btn-notif-turn-off = 🔕 Turn off morning message
btn-notif-turn-on = 🔔 Turn on morning message
btn-change-language = 🌐 Language
btn-back-menu = ⬅️ Back to menu
btn-clear = 🗑 Clear value
btn-cancel = Cancel

edit-prompt-name = Send your new name:
edit-prompt-birth-date = Send your date of birth as <b>DD.MM.YYYY</b>:
edit-prompt-birth-time = Send your time of birth as <b>HH:MM</b>:
edit-prompt-birth-city = Send your city of birth:
edit-prompt-daily-time = When should I send your Card of the Day? Send the time (Moscow time) as <b>HH:MM</b>:
profile-saved = Saved ✅
edit-cancelled = Change cancelled.

## Data deletion

delete-confirm =
    Delete all your data — profile, reading history and bonuses?
    <b>This cannot be undone.</b>
btn-delete-yes = Yes, delete everything
delete-done = All your data has been deleted. If you want to come back, just tap /start 🌙
delete-cancelled = Okay, nothing was deleted.

## Commands and bot description

cmd-start = Start over
cmd-menu = Main menu
cmd-profile = My profile
cmd-language = Change language
cmd-delete-me = Delete my data

bot-short-description = Tarot, horoscopes and numerology online — personalised by your birth date ✨
bot-description =
    🔮 Your personal astrologer in Telegram.

    • Tarot readings for any question
    • Daily, weekly and monthly horoscopes
    • Numerology and compatibility
    • Dream interpretation

    Free Card of the Day every day. For entertainment and self-reflection only.
