import logging
from telegram import (
    Poll,
    ParseMode,
    KeyboardButton,
    KeyboardButtonPollType,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    ForceReply,
    User,
)
from telegram.ext import Updater, CommandHandler, MessageHandler, PollAnswerHandler, Filters, CallbackContext
import sqlite3
import os
import functools

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#database parts
def openDB(dbName):
    con = sqlite3.connect(dbName)
    # con.row_factory = sqlite3.Row
    return con

def congrats(tele_id, id_list): 
    rank=0
    for i in id_list:
        if tele_id != i:
            rank += 1
        else:
            break
    if rank==len(id_list): #user not in leaderboard
        return('You are not on the leaderboard! Get up there by trying some of our questions!')
    else:
        rank+=1
        if rank<=3:
            return(f'Congrats! You are on the podium! Proudly at rank {rank}!')
        else:
            return (f'Nice! You are at rank {rank}! Keep the hustle on!')
   
    
def get_leaderboard(chat_id):
    con = openDB('bigbrain.db')
    cur = con.execute(
        '''
    SELECT TELE_ID, PTS 
    FROM PLAYERS
    WHERE CHAT_ID = ?
    ORDER BY PTS DESC
    '''
    , (chat_id, )).fetchall()
    con.close()
    return cur

def get_question():
    con = openDB('bigbrain.db')
    res = con.execute(
        '''
    SELECT SUBJECT, QN, CHOICES, ANS, PTS, DIFFICULTY_LVL
    FROM QN_BANK
    WHERE QN_TYPE = 'MCQ'
    ORDER BY RANDOM()
    LIMIT 1; 
    '''
    ).fetchone()
    con.close()
    return res

STICKERS = {
    'big_brain_bear': 'CAACAgUAAxkBAAECnqNg-ptwI6CGNHliIr-vgNAK-RNjZgACdQQAAiOf0FdQkHdZ5tocnyAE',
    'leader_board':'CAACAgUAAxkBAAECnqVg-pufsl8pCV-20846FkjViVwn8gAC_QIAArai2FfYiion2s85oyAE',
    'bear_with_stick':'CAACAgUAAxkBAAECnqdg-pu4UlIrAAHCexIvpUKwqNsV9lYAApkEAAIgZdFXXW36FJ3SGnUgBA',
    'bear_needs_help':'CAACAgUAAxkBAAECnsRg-rkHZbrafvE8YaGR_8WkRZCKBwACEwMAAtOW2FfCAdtIYrubcCAE'
}

with open('help.txt') as f:
    HELP_TEXT = f.read()

with open('about.txt') as f:
    ABOUT = f.read()

try:
    with open('TOKEN') as f:
        TOKEN = f.readline().strip()
except:
    TOKEN = os.environ['TOKEN']

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )

def group_only(func):
    @functools.wraps(func)
    def wrapper(update: Update, context: CallbackContext) -> None:
        if update.message.chat_id < 0:
            func(update, context)
        else:
            update.message.reply_text('Please use this command in a group.')
    return wrapper

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    chat_id = update.message.chat_id
    update.message.bot.send_sticker(chat_id, STICKERS['bear_needs_help'])
    update.message.bot.send_message(chat_id, HELP_TEXT, parse_mode="MarkdownV2")

def about(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    update.message.bot.send_sticker(chat_id, STICKERS['big_brain_bear'])
    update.message.bot.send_message(chat_id, ABOUT, parse_mode="MarkdownV2")

@group_only
def group_leaderboard(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    players = get_leaderboard(chat_id)
    id_only = [i[0] for i in players]
    res = []

    #get top 3 in the group
    left = 3
    for id, pts in players:
        if not left:
            break
        try:    
            # check if player is in group.
            # update.message.bot.get_chat_member(chat_id, id).user.full_name
            user = update.message.bot.get_chat_member(chat_id, id)
            res.append((id, user.user.full_name, pts))
            left -= 1
        except Exception as e:
            print(e)
    
    emojis = "🥇🥈🥉"
    # message = "__👑*Leaderboard*__\n"
    message = ""
    for e, (_, name, pts) in zip(emojis, res):
        message += f"{e} *{name}* {pts} pts\n"
    
    update.message.bot.send_sticker(chat_id, STICKERS['leader_board'])
    update.message.bot.send_message(chat_id, congrats(update.effective_user.id, id_only))
    if message:
        update.message.bot.send_message(chat_id, message, parse_mode="MarkdownV2")
    else:
        update.message.bot.send_message(chat_id, "No one played yet! Start playing now! 🐻")

@group_only
def question(update: Update, context: CallbackContext) -> None:
    subject, qn, choices, ans, pts, diff = get_question()
    pts = int(pts)
    choices = choices.split("|")
    correct = choices.index(ans)
    message = context.bot.send_poll(
        update.effective_chat.id,
        f"Subject: {subject}\n{qn}",
        choices,
        correct_option_id=correct,
        is_anonymous=False,
        type='quiz',
        close_date=10,
        explanation=f"Difficulty: {diff}"
        # allows_multiple_answers=True,
    )
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "answers": choices,
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
            "answers": 0,
            "correct": correct,
            "pts": pts
        }
    }
    context.bot_data.update(payload)
    
def receive_poll_answer(update: Update, context: CallbackContext) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    poll_id = answer.poll_id
    try:
        answers = context.bot_data[poll_id]["answers"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return

    points = context.bot_data[poll_id]['pts']
    chat_id = context.bot_data[poll_id]['chat_id']
    if answer['option_ids'][0] == context.bot_data[poll_id]['correct']:
        # add 1 point since answer is correct
        id=answer['user']['id']

        con=openDB('bigbrain.db')
        cur=con.cursor()
        #GETTING THE POINTS AND UPDATING PTS
        try:
            curr_pts = cur.execute('SELECT PTS FROM PLAYERS WHERE TELE_ID=? AND CHAT_ID=?',(id, chat_id)).fetchone()[0]
            cur.execute('UPDATE PLAYERS SET PTS=? WHERE TELE_ID=? AND CHAT_ID = ?',(curr_pts+points,id, chat_id))
        except:
            curr_pts = points
            cur.execute('INSERT INTO PLAYERS (TELE_ID, CHAT_ID, PTS) VALUES(?,?,?)',(id, chat_id, curr_pts))
        
        con.commit()
        con.close()
    

    # {'user': {'language_code': 'en', 'first_name': 'Chnn', 'username': 'chnn2', 'id': 266267665, 'is_bot': False}, 'option_ids': [0], 'poll_id': '6330144811999297563'}

    print(answer)




    
    
def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("rank", group_leaderboard))
    dispatcher.add_handler(CommandHandler("q", question))
    dispatcher.add_handler(CommandHandler("about", about))
    dispatcher.add_handler(PollAnswerHandler(receive_poll_answer))

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
