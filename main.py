import logging
import google.generativeai as palm
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

# Configurez l'API de Google Gemini
palm.configure(api_key=open('token.txt').read().strip())

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the states for the conversation
ANSWERING_QUESTIONS = range(7)

# Define the questions
questions = [
    "Quel est votre nom et prénom ?",
    "Pouvez-vous me parler un peu de vous et de votre parcours éducatif ?",
    "Quel programme spécifique postulez-vous à l'université ?",
    "Qu'est-ce qui vous a inspiré à poursuivre des études dans ce domaine particulier ?",
    "Quelles compétences et qualités possédez-vous qui font de vous un candidat solide pour ce programme ?",
]

answers = {}

# Define the command handler for starting the conversation


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id not in answers:
        answers[user_id] = []

    welcome_message = (
        "Bonjour et bienvenue sur  ProHtech bot! 🎓\n\n"
        "Si vous envisagez de postuler à des universités au Maroc et avez besoin d'aide pour rédiger une lettre de motivation, vous êtes au bon endroit ! ProHtech bot est là pour vous assister.\n\n"
        "Je vais vous poser quelques questions sur votre parcours, vos réalisations et vos motivations. Ensuite, je vais générer une lettre de motivation personnalisée juste pour vous. C'est parti !\n\n"
        "Pour commencer, veuillez me donner votre nom et prénom :"
    )
    await update.message.reply_text(welcome_message)
    return ANSWERING_QUESTIONS


async def ask_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    question_number = len(answers[user_id])

    if question_number < len(questions):
        if question_number == 0:
            await update.message.reply_text(questions[question_number])
        else:
            personalized_question = questions[question_number]
            await update.message.reply_text(personalized_question)

        return ANSWERING_QUESTIONS
    else:
        return await generate_motivational_letter(update, context)


async def receive_answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    answers[user_id].append(update.message.text)
    return await ask_questions(update, context)


async def generate_motivational_letter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Construct the prompt
    prompt = "Écrire une lettre de motivation en français destinée au bureau des admissions d'une université, basée sur les informations suivantes. Assurez-vous d'inclure mon nom à la fin de la lettre :\n\n"
    for i, question in enumerate(questions):
        prompt += f"{questions[i]}\nAnswer: {answers[user_id][i]}\n\n"

    messages = [
        {"role": "system", "content": "Vous êtes un assistant utile, compétent en rédaction de lettres de motivation."},
        {"role": "user", "content": prompt}
    ]

    # Use Gemini API to generate the rest of the letter
    model = palm.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(
            f"""Écrire une lettre de motivation en français destinée au bureau des admissions d'une université, basée sur les informations suivantes
         {messages} Assurez-vous d'inclure mon nom à la fin de la lettre :\n\n
         Vous êtes un assistant utile, compétent en rédaction de lettres de motivation """
        )
        letter = response.text.strip()
        await update.message.reply_text("Merci pour vos réponses. Voici votre lettre de motivation :\n\n" + letter)

    except Exception as e:
        await update.message.reply_text(f"Une erreur s'est produite lors de la génération de la lettre : {e}")

        # Clear user's answers
    del answers[user_id]
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id in answers:
        del answers[user_id]
    await update.message.reply_text('Conversation annulée.')
    return ConversationHandler.END


def main():
    # Set up the Telegram bot
    application = ApplicationBuilder().token(
        "token telegram ici").build()

    # Define the conversation handler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ANSWERING_QUESTIONS: [MessageHandler(
                filters.TEXT & ~filters.COMMAND, receive_answers)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conversation_handler)

    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
