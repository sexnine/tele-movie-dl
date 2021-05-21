#TODO: Implement notification when download complete
import logging
from restricted import Restricted
import enum
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from yipy.api import Yipy
from transmission_rpc import Client
from config import config

movie_download_dir = config.get("MOVIE_DOWLOAD_DIRECTORY")


ytsapi = Yipy()
transmission_client = Client(host=config.get("TRANSMISSION_HOST"), port=config.get("TRANSMISSION_PORT"), username=config.get("TRANSMISSION_USERNAME"), password=config.get("TRANSMISSION_PASSWORD"))

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

IS_CORRECT_MOVIE, AWAITING_CORRECT_MOVIE = range(2)


def parse_markdown_message(text: str):
    return text.translate(str.maketrans({"_": r"\_",
                                         "*": r"\*",
                                         "[": r"\[",
                                         "]": r"\]",
                                         "(": r"\(",
                                         ")": r"\)",
                                         "~": r"\~",
                                         "`": r"\`",
                                         ">": r"\>",
                                         "#": r"\#",
                                         "+": r"\+",
                                         "-": r"\-",
                                         "=": r"\=",
                                         "|": r"\|",
                                         "{": r"\{",
                                         "}": r"\}",
                                         ".": r"\.",
                                         "!": r"\!",
                                         }))


class TorrentRating(enum.Enum):
    BluRay4k = 1
    BluRay1080p = 2
    Web4k = 3
    Web1080p = 4
    BluRay720p = 5
    Web720p = 6
    BluRay3D = 99

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented


class TorrentData(object):
    quality_ratings = {"bluray2160p": TorrentRating.BluRay4k,
                       "bluray1080p": TorrentRating.BluRay1080p,
                       "web2160p": TorrentRating.Web4k,
                       "web1080p": TorrentRating.Web1080p,
                       "bluray720p": TorrentRating.BluRay720p,
                       "web720p": TorrentRating.Web720p}

    def __init__(self, data):
        self.url = data["url"]
        self.quality = data["quality"]
        self.type = data["type"]
        self.size = data["size"]
        self.quality_description = f"{self.type} {self.quality} ({self.size})"
        self.rating = self.quality_ratings[self.type + self.quality]


class MovieData:
    def __init__(self, data):
        self.title_md = parse_markdown_message(data.get("title_long"))
        self.rating_md = parse_markdown_message(str(data.get("rating")))
        self.image_md = parse_markdown_message(data.get("medium_cover_image"))
        self.summary_md = parse_markdown_message(data.get("summary"))
        self.title = data.get("title_long")
        self.rating = str(data.get("rating"))
        self.image = data.get("medium_cover_image")
        self.summary = data.get("summary")

        self.torrents = [TorrentData(x) for x in data["torrents"]]

    def best_torrent(self):
        return sorted(self.torrents, key=lambda x: x.rating)[0]


def send_movie_to_daemon(torrent: TorrentData):
    print("Sending movie to daemon")
    return transmission_client.add_torrent(torrent.url, download_dir=movie_download_dir)


def is_correct_movie_msg(update: Update, movie: MovieData):
    reply_keyboard = [[], ["👍", "👎"]]
    update.message.reply_text(
        f"__*{movie.title_md}*__  🌟 *{movie.rating_md}*\n\n{movie.summary_md}\n[ ]({movie.image_md})\n\n`Is this the right movie?`",
        parse_mode='MarkdownV2',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )


def reply_with_movie_eta(ctx: CallbackContext):
    data = ctx.job.context
    torrent_response = transmission_client.get_torrent(data["torrent_id"])
    ctx.bot.send_message(data["chat_id"], text=f"🎉 {data['movie_name']} is downloading and will be completed in about {torrent_response.eta}")


@Restricted
def movie_cmd(update: Update, ctx: CallbackContext) -> int:
    movie_name = " ".join(ctx.args)

    if movie_name:
        r = ytsapi.list(query_term=movie_name)
        print(r)
        results = r["data"]["movies"]
        movies = [MovieData(x) for x in results]
        movie = movies[0]
        ctx.user_data["movie_results"] = movies
        ctx.user_data["selected_movie"] = movie
        is_correct_movie_msg(update, movie)
        return IS_CORRECT_MOVIE
    else:
        update.message.reply_text(
            "You didn't specify a movie."
        )
        return ConversationHandler.END


def is_correct_movie(update: Update, ctx: CallbackContext) -> int:
    if update.message.text == "👍":
        movie = ctx.user_data["selected_movie"]
        torrent = movie.best_torrent()
        update.message.reply_text(
            f"👍 Attempting to send the movie to the download server.\nDownloading movie: {movie.title}\nQuality: {torrent.quality_description}",
            reply_markup=ReplyKeyboardRemove()
        )
        torrent_response = send_movie_to_daemon(torrent)
        ctx.job_queue.run_once(reply_with_movie_eta, 60, context={"chat_id": update.message.chat_id, "torrent_id": torrent_response.id, "movie_name": movie.title}, name="movie-torrent-" + str(torrent_response.id))
        return ConversationHandler.END
    else:
        if len(ctx.user_data["movie_results"]) > 1:
            first_row = []
            second_row = []
            extra_movie_options = {}
            movies = ctx.user_data["movie_results"]
            i = 0
            for movie in movies:
                if i == 0:
                    print("c")
                    i += 1
                    continue
                if i >= len(movies) or i >= 5:
                    print("b")
                    break
                if i in [1, 3]:
                    first_row.append(movie.title)
                    extra_movie_options[movie.title] = i
                else:
                    second_row.append(movie.title)
                    extra_movie_options[movie.title] = i
                i += 1

            ctx.user_data["extra_movie_options"] = extra_movie_options
            reply_keyboard = [first_row, second_row, ["None of these are it..."]]
            ctx.user_data["extra_movie_options_keyboard"] = reply_keyboard
            print(first_row)
            print(reply_keyboard)
            update.message.reply_text(
                "Sorry!  Which one of these movies is it?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard)
            )
            return AWAITING_CORRECT_MOVIE
        else:
            update.message.reply_text("Sorry, there are no other results ☹")
        return ConversationHandler.END


def awaiting_correct_movie_cmd(update: Update, ctx: CallbackContext):
    movie_name = update.message.text
    extra_movie_options = ctx.user_data["extra_movie_options"]
    if movie_name in extra_movie_options:
        print(extra_movie_options[movie_name])
        print(ctx.user_data["movie_results"][extra_movie_options[movie_name]])
        ctx.user_data["selected_movie"] = ctx.user_data["movie_results"][extra_movie_options[movie_name]]
        is_correct_movie_msg(update, ctx.user_data["selected_movie"])
        return IS_CORRECT_MOVIE
    elif movie_name == "None of these are it...":
        update.message.reply_text("Sorry, I don't know what movie you want, make sure you inputted the correct title.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        update.message.reply_text("That movie isn't one of the movie options I provided, please press the button of which movie you want.  You should be able to select which movie now.", reply_markup=ReplyKeyboardMarkup(ctx.user_data["extra_movie_options_keyboard"]))
        return AWAITING_CORRECT_MOVIE


def cancel(update: Update, ctx: CallbackContext) -> int:
    # user = update.message.from_user
    update.message.reply_text(
        'Cancelled.', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def timeout(update: Update, ctx: CallbackContext):
    update.message.reply_text(
        "You didn't respond in time, or you responded incorrectly.  Please try again.", reply_markup=ReplyKeyboardRemove()
    )


def main() -> None:
    # Create the Updater and pass it your bot token.
    updater = Updater(config.get("TELEGRAM_BOT_TOKEN"))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('movie', movie_cmd)],
        states={
            IS_CORRECT_MOVIE: [MessageHandler(Filters.regex('^(👍|👎)$'), is_correct_movie)],
            AWAITING_CORRECT_MOVIE: [MessageHandler(Filters.text, awaiting_correct_movie_cmd)],
            ConversationHandler.TIMEOUT: [MessageHandler(Filters.text | Filters.command, timeout)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=15
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
