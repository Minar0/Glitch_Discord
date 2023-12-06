import discord
from discord.flags import Intents
from datetime import datetime
from typing import Any
import aiohttp
import configparser
import pprint

#region Tweakable Values
max_tokens = 50 #How many tokens Glitch is allowed to generate. Setting it too low will lead to him getting cut off. Setting it too high might lead to him getting... wordy
creativity = 0.5 #Value between 0-1. Also called temperature. Lower values are more deterministic. They might be faster too
message_lookback_amount = 5 #How many messages Glitch will look back in for conversation context. Setting it too high could lead to long response times
print_proc_message = False #Used for trouble shooting. Prints the message sent to LlamaGPT in the log. Kinda long and annoying so I usually leave it off unless needed
#endregion

class GlitchClient(discord.Client):
    def __init__(self, personality_string, intents: Intents) -> None:
        self.personality_string=personality_string
        super().__init__(intents=intents)


    #region Event Functions
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
  
    async def on_message(self, message):
        if message.author == self.user:
            return

        #Checks if the received message should be responded to
        needs_response = False
        if message.type == discord.MessageType.reply:
            ref_message_id = message.reference.message_id
            ref_message = await message.channel.fetch_message(ref_message_id)
            if ref_message.author == self.user:
                needs_response = True
        elif "<@1180692348196376626>" in message.content or message.channel.type == discord.ChannelType.private:
            needs_response = True
        if not needs_response:
            return

        author_name = "Minaro" if message.author.id == 308746205859414028 else message.author.display_name
        content = message.clean_content
        print(f'\nMessage from {author_name}: {content}')
        
        #Let channel know that he's typing
        response = "No response generated"
        async with message.channel.typing():
            proc_message = await self.generate_proc_message(message.channel)
            response = await self.send_to_agent(proc_message)

        await message.reply(response)
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

            #API request. Consider changing to get_member instead
            try:
                author_member = await channel.guild.fetch_member(message.author.id) if channel.guild else message.author
            except:
                author_member = message.author
            if author_member == self.user:
                llm_messages[i]={
                    "role": "assistant", 
                    "content": f"{content}"
                }
            else:
                llm_messages[i]={
                    "role": "user", 
                    "content": f"{author_member.display_name} ({author_member.name}): {content}"
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
        url = 'http://localhost:3001/v1/chat/completions'
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=proc_message) as response:
                    if response.status == 200:
                        json_response = await response.json()
                        return_message = json_response['choices'][0]['message']['content']
                        print(f"Response: {return_message} \nTokens: {json_response['usage']}")
                        if json_response['usage']['completion_tokens'] >= max_tokens:
                            return_message += "...\n\noh, looks like I've hit my message length limit. Sorry."
                        return return_message
                    else:
                        print(f"Request failed with status code {response.status}: {await response.text()}")
                        return "My speech center appears to be having a problem. Please let Minaro know and he'll fix me."
        except Exception as e:
            print(f"An error occurred: {e}")
            return "It looks like my speech center has been shut down. If you pester Minaro enough, he might turn it on."
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
#endregion

#region Initialization
api_keys = configparser.ConfigParser()
api_keys.read('api_keys.ini')
discord_key = api_keys['API']['discord']

intents = discord.Intents.default()
intents.message_content = True

with open('./personality.txt', 'r') as file:
    personality = file.read()

client = GlitchClient(personality, intents=intents)
client.run(discord_key)
#endregion