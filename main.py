def configure():
    from dotenv import load_dotenv
    load_dotenv()


def main():
    configure()
    from messageHandler import MessageHandler
    from telethon import TelegramClient, events
    import os
    messageHandler = MessageHandler()
    teleBot = TelegramClient('bot', os.getenv('TELEGRAM_API_ID'), os.getenv(
        'TELEGRAM_API_HASH'), request_retries=100, connection_retries=100, retry_delay=5).start(bot_token=os.getenv('TELEGRAM_BOT_TOKEN'))

    @teleBot.on(events.NewMessage(incoming=True))
    async def handleMessage(event):
        try:
            responses = await messageHandler.handleMessage(event)
        except Exception as e:
            await event.reply(f"An Error Occurred\n\n{e}")
        for response in responses:
            if response[0] == 0:
                await event.respond(response[2])
            elif response[0] == 1:
                await event.reply(response[2])
    teleBot.start()
    teleBot.run_until_disconnected()


if __name__ == '__main__':
    main()
