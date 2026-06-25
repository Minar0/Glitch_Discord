import discord
from discord.flags import Intents
from datetime import datetime
from typing import Any
import json
import requests
import configparser
import pprint
import re
import csv

#region Hyperparameters
max_tokens = 50 #How many tokens Glitch is allowed to generate. Setting it too low will lead to him getting cut off. Setting it too high might lead to him getting... wordy.
creativity = 0.7 #Value between 0-1. Also called temperature. Lower values are more deterministic. They might be faster too.
message_lookback_amount = 7 #How many messages Glitch will look back in for conversation context. Setting it too high could lead to long response times.
print_proc_message = False #Used for trouble shooting. Prints the message sent to LlamaGPT in the log. Kinda long and annoying so I usually leave it off unless needed.
link_to_memory = './glitch_memory' #Location for all the things Glitch knows.
url = 'http://localhost:11434/api/chat' #Url of the ollama server
model = 'llama3.1:8b' #The model used to generate the response. Script does not check if this is correct
#endregion

class GlitchClient(discord.Client):
    def __init__(self, personality_string, people_opinions, intents: Intents) -> None:
        self.personality_string = personality_string
        self.people_opinions = people_opinions
        super().__init__(intents=intents)


    #region Event Functions
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
  
    async def on_message(self, message):
        if message.author == self.user:
            return

        #print("<@&1180692348196376626>" in message.content)
        #print(message.content)

        #Checks if the received message should be responded to
        needs_response = False
        if message.type == discord.MessageType.reply:
            ref_message_id = message.reference.message_id
            ref_message = await message.channel.fetch_message(ref_message_id)
            if ref_message.author == self.user:
                needs_response = True
        elif "<@1180692348196376626>" in message.content or "<@&1183304745151103027>" in message.content:
            needs_response = True
        elif message.channel.type == discord.ChannelType.private:
            needs_response = True
        if not needs_response:
            return
        contains_word, filtered_word = contains_filtered_word(message.clean_content)
        if contains_word:
            print(f'Input message filtered on word: {filtered_word}')
            await message.reply("Your message was caught by my input filter, let Minaro know if you think this is an error")
            return

        author_global_name = message.author.global_name
        author_username = message.author.name
        content = message.clean_content
        print(f'\nMessage from {author_global_name}: {content}')
        
        #Let channel know that he's typing
        response = "No response generated"
        print('Beginning text generation')
        async with message.channel.typing():
            proc_message = await self.generate_proc_message(message.channel)
            response = await self.send_to_agent(proc_message)
            opinion_change=0

            pattern = r'\(([-+]?\d+)\)'
            matches = re.findall(pattern, response)
            if matches:
                if author_username not in self.people_opinions:
                    self.people_opinions[author_username]=0
                
                opinion_change = clamp_value(-5, 5, int(matches[0]))
                self.people_opinions[author_username] = clamp_value(-100, 100, self.people_opinions[author_username]+opinion_change)

                write_dict_to_json(self.people_opinions, f'{link_to_memory}/opinions_list.json')

                post_processed_response = re.sub(pattern, '', response)
            else:
                post_processed_response = response

            if opinion_change > 0:
                await message.add_reaction('😀')
            elif opinion_change < 0:
                await message.add_reaction('😠')

            contains_word, filtered_word = contains_filtered_word(post_processed_response)
            if contains_word:
                post_processed_response = '[Filtered]'
                print(f'Response message filtered on word: {filtered_word}')
        print('Finished text generation\n')
        await message.reply(post_processed_response)
    #endregion

    #region Accessory Functions
    async def generate_proc_message(self, channel, message_count=message_lookback_amount):
        llm_messages = [{}]*(message_count+1)
        llm_messages[0] = {
            "role": "system", 
            "content": self.personality_string+"\n"+get_date_time_str()
        }

        i=len(llm_messages)-1
        async for message in channel.history(limit=message_count):
            content = message.clean_content
            author_member = message.author

            if author_member == self.user:
                llm_messages[i]={
                    "role": "assistant", 
                    "content": f"{content}"
                }
            else:
                message_author = author_member.global_name
                opinion_of_user = self.people_opinions[message_author] if message_author in self.people_opinions else 0
                llm_messages[i]={
                    "role": "user", 
                    "content": f"{message_author} <{opinion_of_user}>: {content}"
                }
            i-=1

        proc_message = {
            "messages": llm_messages,
            "temperature": creativity,
            "max_tokens": max_tokens,
            "stop": ["###"]
        }
        if print_proc_message: pprint.pprint(proc_message)
        return proc_message
    
    async def send_to_agent(self, proc_message):
        #Sends the text to the ollama server
        ollama_payload = {
            "model": model,
            "messages": proc_message["messages"],
            "stream": False
        }

        response = requests.post(url, json = ollama_payload)
        json_response = json.loads(response.text)
        print(f"Response: {json_response["message"]["content"]}")
        
        return_message = self.process_agent_response(json_response["message"]["content"])
        return return_message
        
        
    def process_agent_response(self, message):
        #Sometimes the model puts odd tokens into the message.
        pattern = r'^([^<]+)\s*<(\d+)>:?'
        result = re.sub(pattern, '', message).strip()
        return result
    #endregion


#region Useful Functions That Don't Need To Be Inside The Client Class
#Get the current date and time in a pretty format
def get_date_time_str():
        current_datetime = datetime.now()
        date = current_datetime.strftime(f'%B {get_day_suffix(current_datetime.day)}, %Y')
        time = current_datetime.strftime('%I:%M%p CST')
        return f'The date is {date}\nThe time is {time}'

#Get the correct suffix for the day. IE: 5 -> 5th, 23->23rd, 31->31st, etc
def get_day_suffix(day):
    suff_num = day % 10
    day_suff='th'
    if not (10 <= day <=20) and (suff_num <= 3): #Why DO we have different names for numbers 10-20??? Whats up with that?
        normal_suffixes = {
            1: "st",
            2: "nd",
            3: "rd"
        }
        day_suff = normal_suffixes.get(suff_num)
    return f'{day}{day_suff}'

#R/W functions
def load_json_to_dict(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        write_dict_to_json({}, filename)
        return {}

def write_dict_to_json(dict, filename):
    with open(filename, "w") as file:
        json.dump(dict, file, indent=2)

def load_txt(filename):
    with open(filename, 'r') as file:
        return file.read()

def load_first_csv_row(filename):
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return next(reader, None)

#https://tenor.com/view/futurama-robot-pincers-gif-17376524
def clamp_value(min, max, value):
    if value < min:
        return min
    elif value > max:
        return max
    else:
        return value

#Checks if the response needs to be filtered. It's necessary when you have shit friends.
def contains_filtered_word(text):
    text = re.sub(r'[^A-Za-z0-9 ]+', '', text)
    text_array = text.split()
    for word in text_array:
        if word.lower() in filter_list:
            return True, word
    return False, ''
#endregion

#region Initialization
api_keys = configparser.ConfigParser()
api_keys.read('api_keys.ini')
discord_key = api_keys['API']['discord']

intents = discord.Intents.default()
intents.message_content = True

personality = load_txt(f'{link_to_memory}/personality.txt')
opinions = load_json_to_dict(f'{link_to_memory}/opinions_list.json')
filter_list = load_first_csv_row(f'{link_to_memory}/filter_list.csv')

client = GlitchClient(personality, opinions, intents)
client.run(discord_key)
#endregion
