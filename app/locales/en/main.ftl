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

    A new one will be waiting for you tomorrow. Don't want to wait? Invite a friend: for each one who makes a reading, you get 3 bonus readings 🎁 A subscription with unlimited readings is coming very soon too.
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

## Big spreads

spreads-title =
    🌟 Big spreads — for questions you want to explore in depth.

    • <b>Celtic Cross</b> — 10 cards, a detailed look at the situation
    • <b>Relationship</b> — 5 cards about the two of you
    • <b>Yes or no</b> — a short answer to a clear question
    • <b>Two paths</b> — what awaits on each option
spread-btn-celtic = ✝️ Celtic Cross (10 cards)
spread-btn-relationship = 💞 Relationship (5 cards)
spread-btn-yesno = ⚖️ Yes or no (1 card)
spread-btn-two-paths = 🔀 Two paths (3 cards)
spread-title-question = 🔮 Question reading
spread-title-celtic = ✝️ Celtic Cross
spread-title-relationship = 💞 Relationship reading
spread-title-yesno = ⚖️ Yes or no
spread-title-two-paths = 🔀 Two paths
spread-ask-celtic = ✝️ The Celtic Cross looks at a situation in depth. Describe it or ask a question in one message (up to { $max } characters).
spread-ask-relationship = 💞 Tell me which relationship you'd like to explore — for example: "What's going on between me and Alex?" (up to { $max } characters).
spread-ask-yesno = ⚖️ Ask a question that can be answered "yes" or "no" — for example: "Should I go to this meeting?" (up to { $max } characters).
spread-ask-two-paths = 🔀 Describe the two options you're choosing between — for example: "Stay at my current job or move to a new company?" (up to { $max } characters).
yesno-verdict-yes = ✅ Most likely yes
yesno-verdict-no = ❌ Most likely no
yesno-verdict-maybe = 🌫 Unclear for now — the answer is still forming
position-answer = Answer
position-path-a = First path
position-path-b = Second path
position-advice = The cards' advice
position-you = You
position-partner = Partner
position-connection = What connects you
position-obstacle = What stands in the way
position-potential = The relationship's potential
position-situation = Situation
position-challenge = Challenge
position-goal = Goal
position-foundation = Foundation
position-self = Yourself
position-environment = Environment
position-hopes = Hopes and fears
position-outcome = Outcome

premium-locked-credit =
    🔒 This section is available with a subscription or for a bonus reading.

    The subscription is coming very soon, and you can get bonus readings right now: invite a friend — for each one who makes a reading, you get 3 bonuses 🎁
credit-spent = 🎁 A bonus reading was used. Left: { $left }
referral-rewarded = 🎁 Your friend made their first reading — you've received { $bonus } bonus readings! You can spend them on any section.

## Compatibility

compat-title = 💞 Compatibility
compat-ask = 💞 Send your partner's date of birth as <b>DD.MM.YYYY</b> — I'll compare your zodiac signs and life path numbers.
compat-people =
    You: { $you } · life path { $you_lp }
    Partner: { $partner } · life path { $partner_lp }
compat-score = Compatibility: { $score }%
compat-elements-label = Elements:
compat-numbers-label = Numbers:
compat-pair-fire-fire = Two fires — a bright, passionate couple. You energise each other, but remember to give way instead of competing.
compat-pair-earth-earth = Two earths — reliability and shared values. Planning and daily life come easily; add a little spontaneity.
compat-pair-air-air = Two airs — lightness, conversation and shared interests. You always have something to talk about; don't forget emotional depth.
compat-pair-water-water = Two waters — deep emotional understanding. You feel each other without words; protect your personal boundaries.
compat-pair-air-fire = Air fans the fire — an inspiring union. You push each other toward new things and are rarely bored together.
compat-pair-earth-water = Water nourishes earth — a harmonious, caring union. One gives stability, the other warmth and sensitivity.
compat-pair-earth-fire = Fire and earth — energy meets stability. If you agree on the pace, you'll complement each other.
compat-pair-air-water = Air and water — mind and feelings. Learn each other's language: one needs to talk, the other to feel.
compat-pair-fire-water = Fire and water — opposites attract. The relationship can be very strong if you respect your differences.
compat-pair-air-earth = Air and earth — dreams and practicality. Together you can bring ideas to life if you find a shared rhythm.
compat-numbers-harmonious = Your life path numbers are in the same group — you share a similar rhythm and view of what matters.
compat-numbers-different = Your life path numbers are in different groups — you see life differently, and that can enrich you both.
compat-advice-high = Cherish what you have: talk about your feelings and make time just for the two of you.
compat-advice-mid = Your differences aren't a barrier but a resource. Discuss expectations honestly and gently.
compat-advice-low = You'll need more patience and conversation, but strong couples are born exactly from learning to understand each other.

## Numerology

num-title = 🔢 Numerology portrait: { $name }
num-life-path = Life path number — { $number }
num-birthday = Birthday number — { $number }
num-personal-year = Personal year { $year } — { $number }
num-year-prefix = This year is
num-expression = Destiny number (by name) — { $number }
num-soul = Soul number — { $number }
num-personality = Personality number — { $number }
num-full-teaser = 🔒 The full name reading — destiny, soul and personality numbers — is available with a subscription or for a bonus reading.
num-btn-full = 🔓 Full name reading

## Dreams

dream-title = 🌙 Dream interpretation
dream-ask = 🌙 Describe your dream in one message (up to { $max } characters): what happened, who was there, how you felt.
dream-too-long = Your description is a bit long — please shorten it to { $max } characters.
dream-thinking = 🌙 Looking into your dream…
dream-text-only = For now I can only read dreams as text — please describe it in words 🙏
dream-intro = Here are the symbols I see in your dream:
dream-generic = Dreams speak to us in the language of feelings. Remember the mood in the dream and after waking up: it will hint at what the dream is about — a worry, a desire, or changes already beginning in your life.
dream-advice = Write down the dream and how you felt — reread it in a few days: the meaning often becomes clearer with time.

## Invite a friend

invite-text =
    🎁 <b>Invite friends — get bonus readings</b>

    For every friend who makes their first reading, you get { $bonus } bonus readings. Spend them on big spreads, compatibility, dream interpretation and the full numerology reading.

    Your link:
    { $link }

    Friends joined: { $invited }
    Made a reading: { $rewarded }
    Bonus readings available: { $credits }
invite-btn-share = 📤 Share the link
invite-share-text = Try "Твой личный астролог" — tarot readings and horoscopes by your birth date ✨

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
llm-reading-type-yesno = yes-or-no reading
llm-reading-type-two-paths = two-paths reading
llm-reading-type-relationship = relationship reading
llm-reading-type-celtic = Celtic Cross
llm-reading-type-compatibility = compatibility
llm-reading-type-dream = dream interpretation
llm-task-question = Today is { $date }. Make a three-card reading for the question: past, present, future.
llm-task-yesno = Today is { $date }. A one-card yes-or-no reading. Start with the answer: "Most likely yes", "Most likely no" or "Unclear for now", then explain it through the card. Length: 100–180 words.
llm-task-two-paths = Today is { $date }. A two-paths reading: the first card shows what awaits on the first path, the second on the second path, the third is advice. Help the person weigh the options, but leave the decision to them.
llm-task-relationship = Today is { $date }. A five-card relationship reading: you, partner, what connects you, what stands in the way, the relationship's potential. Up to 350 words.
llm-task-celtic = Today is { $date }. A ten-card Celtic Cross reading. Describe each position briefly in 1–2 sentences and bring it all together in a conclusion. Up to 450 words.
llm-compat-task = Describe the couple's compatibility. First person ({ $name }): sign { $you }, life path number { $you_lp }. Partner: sign { $partner }, life path number { $partner_lp }. Calculated compatibility: { $score }%.
llm-dream-task =
    The person's name: { $name }
    Dream: "{ $dream }"
llm-base-meaning = Base meaning
llm-question = The person's question: "{ $question }"
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
