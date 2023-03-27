def configure():
	from dotenv import load_dotenv
	load_dotenv()

def main():
	configure()
	from messageHandler import MessageHandler
	from telethon import TelegramClient, events
	import os
	messageHandler = MessageHandler()
	teleBot = TelegramClient('bot', os.getenv('teleApiId'), os.getenv('teleApiHash')).start(bot_token=os.getenv('teleBotToken'))

	@teleBot.on(events.NewMessage(incoming=True))
	async def handleMessage(event):
		responses = await messageHandler.handleMessage(event)
		for response in responses:
			if response[0] == 0:
				await event.respond(response[2])
			elif response[0] == 1:
				await event.reply(response[2])
	teleBot.start()
	teleBot.run_until_disconnected()

if __name__ == '__main__':
	main()