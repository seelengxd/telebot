

  

# big brain bear
telegram bot submission for nus lifehack 2021 (003 justea)

  

## about
This is a telegram bot aimed to engage students via simple and fast revision\.
Solving questions *\(/q\)*  will help you rise in the leaderboard *\(/rank\)*\.

## usage
- the bot needs be added to a group - some of the commands will tell you to do so if you attempt to use them while talking to the bot in private chat.
https://t.me/verybigbrain_bot

 - This bot is being run on my computer. (~~probably should have figured out how to stop getting errors about PORT on heroku~~) No downloading/running it yourself should be necessary.

### commands

- /about - Short description about the bot
- /help - Command list
- /q - Randomly selects one question and gives it to the group
- /rank - Leaderboard + your own rank in the group

## technical implementation
- We are using *sqlite* as our database.
- *python-telegram-bot* is used for.... making the telegram bot.

## possible improvements
- add question
- using webhooks instead of polling for real time data/more efficiency
- run bot on heroku instead
