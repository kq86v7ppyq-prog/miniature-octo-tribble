# Telegram bot for psychologist intake questions

Bot asks scripted intake questions before booking a psychologist appointment, collects answers, and sends the finished questionnaire to a configured Telegram chat or group.

## Setup

1. Create a bot with @BotFather and get the token.
2. 2. Install dependencies:
  
   3. ```bash
      pip install -r requirements.txt
      ```

      3. Create `.env` next to `bot.py`:
     
      4. ```bash
         cp .env.example .env
         ```

         4. Fill `.env`:
        
         5. ```env
            BOT_TOKEN=token_from_BotFather
            RECIPIENT_CHAT_ID=chat_or_group_id_for_questionnaires
            ```

            5. To configure a recipient from Telegram, add the bot to the target chat or group and send:
           
            6. ```text
               /admin
               ```

               6. Run the bot:
              
               7. ```bash
                  python bot.py
                  ```

                  ## Commands

                  - `/start` - start the questionnaire
                  - - `/cancel` - stop the questionnaire
                    - - `/id` - show current chat ID
                      - - `/admin` - save current chat or group as questionnaire recipient
                        - - `/help` - show commands
                         
                          - ## Notes
                         
                          - For Render hosting, set `BOT_TOKEN` and `RECIPIENT_CHAT_ID` as environment variables. Do not commit `.env`.
                          - 
