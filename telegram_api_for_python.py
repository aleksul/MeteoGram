ReplyKeyboardRemove = '{"remove_keyboard": true, "selective": false}'

class KeyboardBuilder:
    
    def __init__ (self, texts: list, request_contact=False,request_location=False): #example a = KeyboardBuilder([['HI','Wassup?'],['BYE']])
        self.texts = texts
        self.request_contact = request_contact
        self.request_location = request_location

    def build(self):
        if (self.request_contact == False) and (self.request_location == False):
            return self.texts
        else:
            keyboard = []
            texts = self.texts
            for i in texts:
                temp_list = []
                for j in i:
                    if (self.request_contact == True) and (self.request_location == False):
                        button_dict = {"text": j, "request_contact": True}
                    elif (self.request_contact == False) and (self.request_location == True):
                        button_dict = {"text": j, "request_location": True}
                    elif (self.request_contact == True) and (self.request_location == True):
                        button_dict = {"text": j, "request_contact": True, "request_location": True}                        
                    temp_list.append(button_dict)
                keyboard.append(temp_list)
            return keyboard



class ReplyKeyboardMarkupBuilder:

    def __init__ (self, keyboard: list, resize_keyboard=True, one_time_keyboard=True, seletcive=False):
        self.keyboard = keyboard
        self.resize_keyboard = resize_keyboard
        self.one_time_keyboard = one_time_keyboard
        self.seletcive = seletcive

    def build(self):
        markup = {"keyboard": self.keyboard, "resize_keyboard": self.resize_keyboard, "one_time_keyboard": self.one_time_keyboard, "selective": self.seletcive}
        markup = str(markup)
        markup = markup.replace("True",'true')
        markup = markup.replace("False",'false')
        markup = markup.replace("'",'"')
        return markup



class InlineButtonBuilder:

    def __init__ (self, text: str, url = None, callback_data = None, pay = False):
        self.text = text
        self.url = url
        self.callback_data = callback_data
        self.pay = pay

    def build(self):
        if self.url == None:
            button = {"text": self.text, "callback_data": self.callback_data, "pay": self.pay}
        elif self.callback_data == None:
            button = {"text": self.text, "url": self.url, "pay": self.pay}
        return button

        
class InlineMarkupBuilder:

    def __init__ (self, keyboard):
        self.keyboard = keyboard

    def build(self):
        markup = {"inline_keyboard": self.keyboard}
        markup = str(markup)
        markup = markup.replace("True",'true')
        markup = markup.replace("False",'false')
        markup = markup.replace("'",'"')
        return markup
