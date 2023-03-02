import os
import sys
from argparse import ArgumentParser
from dotenv import load_dotenv
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)
import openai

app = Flask(__name__)

# .envファイルの内容を読み込見込む
load_dotenv()

# アクセストークの読み込み
channel_secret = os.environ['LINE_CHANNEL_SECRET']
channel_access_token = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
open_api_key = os.environ['OPENAI_API_KEY']

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

openai.api_key = open_api_key


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text

    # if text.endswith("占って"):
    # chatGPTのレスポンスを受け取る
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "占い師になりきってください。占い以外の話題になったら話題を逸らして、占いをしたい旨を伝えてください"},
            # {"role": "user", "content": "2021年の日本シリーズで優勝したのは?"},
            # {"role": "assistant", "content": "2021年の日本シリーズで優勝したのは、東京ヤクルトスワローズです。"},
            {"role": "user", "content": text}
        ]
    )

    # レスポンスをもとに返信する
    # profile = line_bot_api.get_profile(event.source.user_id)
    line_bot_api.reply_message(event.reply_token, [
        TextSendMessage(
            text='{}'.format(response["choices"][0]["message"]["content"])
        )
    ])
    # else:
    #   line_bot_api.reply_message(
    #     event.reply_token,
    #     [TextSendMessage(text='占ってほしい場合は、「〜を占って」とおっしゃってください！')])


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
