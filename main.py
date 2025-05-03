from rasa.core.agent import Agent
from rasa.shared.utils.io import json_to_string
import json
import logging
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler
from googletrans import Translator


T = Translator()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

saved = {}

class Model:

    def __init__(self, model_path: str) -> None:
        self.agent = Agent.load(model_path)

    async def message(self, message: str) -> str:
        message = message.strip()
        result = await self.agent.parse_message(message)
        return json_to_string(result)
    
def save_to_json_file(file_path, new_data):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    for key, value in new_data.items():
        if key in data and isinstance(data[key], list) and isinstance(value, list):
            data[key].extend(value)  
        else:
            data[key] = value 

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


async def start(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")



async def classify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    translated_message = await T.translate(user_message, dest='en')
    translated_message_text =  translated_message.text
    print(translated_message_text)
    user_name = update.message.from_user.first_name
    try: 
        um = json.loads(await mdl.message(translated_message_text))
        
        result = {
            "message" : user_message,
            "id"      : user_name

        }

        intent = um["intent"]["name"]


        if intent not in saved:
            saved[intent] = []  


        saved[intent].append(result)
        
        save_to_json_file("data.json", saved)

        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Intent: {um['intent']['name']} saved!")

    except Exception as e:
        logging.error(f"Error during classification: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred while processing your message.")

def read_data(file_path:str) -> dict:
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        print("error loading json file")
    


ASK_SUBJECT = 1

async def rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="About what subject?")
    return ASK_SUBJECT

async def process_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text  
    um = json.loads(await mdl.message(prompt))  
    result = read_data("data.json")
    
    intent = um["intent"]["name"]
    mes = ""
    if intent in result:
        for d in result[intent]:
            mes += d["id"] + " said: " + d["message"] + "\n"
        
    else:
        mes = f"No data found for intent: {intent}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=mes)
    return ConversationHandler.END

if __name__ == "__main__":
    mdl = Model("C:\\Users\\moad2\\Desktop\\python project\\study\\chatbot\\classification\\models\\nlu.tar.gz")

    application = ApplicationBuilder().token("7621008271:AAHVb-Uh-vOrScXuSSoOkKRwrenhWP8Qyk8").build()

    start_handler = CommandHandler('start', start)
    cls_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), classify)
    conv_handler = ConversationHandler(
    entry_points=[CommandHandler('rappel', rappel)],
    states={
        ASK_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_subject)],
    },
    fallbacks=[],
)


    application.add_handler(conv_handler)
    application.add_handler(start_handler)
    application.add_handler(cls_handler)


    application.run_polling()
    print(saved)


