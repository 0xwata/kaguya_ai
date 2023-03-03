import os
import sys
from argparse import ArgumentParser
from dotenv import load_dotenv
from flask import Flask, request, abort, g
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
  MessageEvent,
  TextMessage,
  TextSendMessage,
)
import openai

app = Flask(__name__)

cache = {}
input_text_cache = ""
output_text_cache = ""

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
  try:
    text = event.message.text
    print(cache)
    user_cache = cache.get(event.source.user_id, "NotFound")
    if user_cache == "NotFound":
      messages=[
        {"role": "system", "content": "占い師になりきってください。占い以外の話題になったら話題を逸らして、占いをしたい旨を伝えてください"},
        {"role": "user", "content": text}
      ]
      # chatGPTのレスポンスを受け取る
      response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
      )
    else:
      messages=[
        {"role": "system", "content": "占い師になりきってください。占い以外の話題になったら話題を逸らして、占いをしたい旨を伝えてください"},
        {"role": "user", "content": user_cache["input_text_cache"]},
        {"role": "assistant", "content": user_cache["output_text_cache"]},
        {"role": "user", "content": text}
      ]
      # chatGPTのレスポンスを受け取る
      response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
      )

    # レスポンスをもとに返信する
    # profile = line_bot_api.get_profile(event.source.user_id)
    line_bot_api.reply_message(event.reply_token, [
      TextSendMessage(
        text="{}）".format(response["choices"][0]["message"]["content"])
      )])
    cache[event.source.user_id] = {
      "input_text_cache": text,
      "output_text_cache": response["choices"][0]["message"]["content"]
    }


  except:
   line_bot_api.reply_message(event.reply_token, [
   TextSendMessage(text="すみません、バグりました。")])

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8000)
