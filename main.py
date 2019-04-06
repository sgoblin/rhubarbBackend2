#!/usr/bin/env python3
import motor, tornado.web, tornado.ioloop, tornado.websocket, bson, urllib, time, pymongo, json, os
from tornado import gen
from os import environ

good_origins = ["rhubarbdev.sgoblin.com", "chatbot.sgoblin.com", "network-limit.codio.io", "rhubarb.sgoblin.com", "deliver-athlete.codio.io"]

class Application(tornado.web.Application):
    def __init__(self, MONGOURL):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
        ]

        client = motor.MotorClient(MONGOURL)

        settings = dict(
            db = client.rhubarbchat_1_1
        )

        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("You should not be here.")

'''class GetMessagesHandler():
    '''

class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    handlers = set()
    cache = []
    cache_size = 100

    def check_origin(self, origin):
        parsed_origin = urllib.parse.urlparse(origin)
        print(parsed_origin.netloc)
        return parsed_origin.netloc in good_origins

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
        print("sending message to " + str(len(cls.handlers)) + " clients")
        for handler in cls.handlers:
            try:
                handler.write_message(chat)
            except:
                print("Error sending message")

    @gen.coroutine
    def open(self):
        ChatSocketHandler.handlers.add(self)
        print("Client connected!")
        chatMessages = self.settings["db"].chatmessages
        cursor = chatMessages.find({})
        docs = yield cursor.sort("_id", pymongo.DESCENDING).to_list(length=5)
        docsList = []
        for document in docs:
            docsList.append(document)
            #print(document)
        print(docsList)
        for document in docsList[::-1]:
            self.write_message(document)
        print("Done sending previous messages")

    def on_message(self, message):
        imsorrydave = {"message": "I'm sorry Dave, I can't do that.", "name": "HAL"}
        print(message)
        message = json.loads(message)
        messageData = message["message"]
        messageLower = messageData.lower().strip()
        messageSender = message["name"]
        ChatSocketHandler.update_cache(message)
        ChatSocketHandler.send_updates(message)
        chatMessages = self.settings["db"].chatmessages
        messageObject = {"_id": time.time(), "name": messageSender, "message": messageData}
        chatMessages.insert_one(messageObject)
        if (messageLower == "open the pod bay doors, hal" or messageLower == "open the pod bay doors hal" or  messageLower == "open the pod bay doors, hal!" or messageLower == "open the pod bay doors, hal." or messageLower == "open the pod bay doors hal!" or messageLower == "open the pod bay doors hal."):
            ChatSocketHandler.update_cache(imsorrydave)
            ChatSocketHandler.send_updates(imsorrydave)
            imsorryObject = {"_id": time.time(), "message": imsorrydave["message"], "name": imsorrydave["name"]}
            chatMessages.insert_one(imsorryObject)

    def on_close(self):
        ChatSocketHandler.handlers.remove(self)
        print("Boo hoo, client disconnected :'(")

def main(MONGOURL):
    app = Application(MONGOURL)
    app.listen(8081, ssl_options={
        "certfile": os.path.join(os.path.dirname(os.path.realpath(__file__)), "certs", "rhubarb.crt"),
        "keyfile": os.path.join(os.path.dirname(os.path.realpath(__file__)), "certs", "rhubarb.key"),
    })
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main(environ["MONGOURL"])
