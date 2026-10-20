## Onboarding

start-greeting =
    ✨ Hi! This is «{ $bot_name }» — your personal astrologer and tarot reader.
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


welcome-back = Welcome back, { $name }! ✨

## Readings

daily-card-gift = 🎁 And here is your first Card of the Day — a gift for getting to know each other:
shuffling = 🔮 Shuffling the deck…
card-reversed = reversed
position-past = Past
position-present = Present
position-future = Future
daily-card-title = <b>🃏 Card of the Day — { $card }</b>
daily-advice-label = ✨ Advice for today:
daily-card-again = Today's card has already been drawn — here it is. A new one will be waiting for you tomorrow 🌅
reading-question-title = 🔮 Question reading
reading-intro = { $name }, here is what the cards show.
advice-label = ✨ Advice:

question-ask =
    ❓ Ask the cards a question — send it in one message (up to { $max } characters).

    Open questions work best:
    • "What should I understand about our relationship?"
    • "How should I approach the new job?"
    • "What should I pay attention to this month?"
question-too-long = Your question is a bit long — please shorten it to { $max } characters.
rate-limited = One second, the cards are still being shuffled… Try again in a couple of seconds.
queue-notice = Lots of people right now — you're in the queue, it will take up to a minute ⏳
reading-error = Sorry, I couldn't make the reading 🙏 It wasn't counted — please try again a bit later.
limit-question-free =
    You've already had today's free reading 🌙

    A new one will be waiting for you tomorrow. And very soon there will be a subscription with unlimited readings, weekly and monthly horoscopes and big spreads.
limit-premium = That's enough readings for today — the cards need rest too 🌙 Come back tomorrow.
paywall-teaser = 💫 Want to go deeper? A subscription is coming soon: unlimited readings, the Celtic Cross, compatibility and weekly and monthly horoscopes.
premium-locked = 🔒 This section will be available with a subscription — coming very soon ✨
btn-new-reading = 🔮 New reading

crisis-response =
    I'm so sorry you're going through this 💛 I won't do a reading for this — right now it's more important to have a real person by your side who can support and help you.

    Please reach out — it's free and confidential:
    • If you're in immediate danger, call your local emergency number (<b>112</b> in Europe, <b>911</b> in the US).
    • Find a free helpline in your country at findahelpline.com.

    You're not alone, and talking to someone is the right step.

## Diary

diary-title = 📖 Your reading diary. Tap a reading to open it:
diary-empty = Your diary is empty for now — make your first reading ✨
diary-daily-card = Card of the Day

## Horoscope

horo-choose = { $sign_emoji } Horoscope for <b>{ $sign }</b>. Choose a period:
btn-horo-day = Today
btn-horo-week = Week
btn-horo-month = Month
horo-title-day = <b>{ $sign_emoji } { $sign } — horoscope for today, { $date }</b>
horo-title-week = <b>{ $sign_emoji } { $sign } — horoscope for the week { $start }–{ $end }</b>
horo-title-month = <b>{ $sign_emoji } { $sign } — horoscope for { $month } { $year }</b>
horo-mood = 🌤 Mood:
horo-love = 💞 Love:
horo-work = 💼 Work and money:
horo-advice = ✨ Advice:
horo-lucky-color = 🎨 Lucky colour: { $color }
horo-lucky-number = 🍀 Lucky number: { $number }
horo-lucky-day = 📅 Lucky day: { $day }
horo-personal-day = 🔢 Your personal day number is <b>{ $number }</b>: { $meaning }
horo-personal-month = 🔢 Your personal month number is <b>{ $number }</b>: { $meaning }

personal-1 = a time to begin and take the initiative.
personal-2 = a time for partnership, patience and diplomacy.
personal-3 = a time for communication, creativity and joy.
personal-4 = a time for work, order and plans.
personal-5 = a time for change, freedom and new experiences.
personal-6 = a time to care for loved ones and home.
personal-7 = a time for reflection, study and rest.
personal-8 = a time for goals, money and decisive steps.
personal-9 = a time to finish things and let go.

month-1 = January
month-2 = February
month-3 = March
month-4 = April
month-5 = May
month-6 = June
month-7 = July
month-8 = August
month-9 = September
month-10 = October
month-11 = November
month-12 = December

## Data for the AI (not shown to users)

llm-profile =
    About the person:
    Name: { $name }
    Zodiac sign: { $sign }
    Life path number: { $life_path }
llm-history-empty = No past readings.
llm-history =
    This person's past readings (for context):
    { $items }
llm-reading-type-daily = Card of the Day
llm-reading-type-question = question reading
llm-base-meaning = Base meaning
llm-question = The person's question: "{ $question }"
llm-question-task = Today is { $date }. Make a three-card reading for the question: past, present, future.
llm-daily-task = Today is { $date }. This is the Card of the Day — one card for today. Write 60–120 words: what this card means for the person's day, ending with a paragraph starting "Advice:" with one short piece of advice. Don't repeat the card name at the start — it's already shown.
llm-horoscope-task = Write a horoscope for { $sign } for { $period } ({ $start } – { $end }).
llm-period-day = today
llm-period-week = the week
llm-period-month = the month

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
