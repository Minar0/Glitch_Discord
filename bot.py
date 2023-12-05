from typing import Any
import discord
from discord.flags import Intents
import aiohttp
import configparser
import pprint

class GlitchClient(discord.Client):
    def __init__(self, personality_string, intents: Intents) -> None:
        self.personality_string=personality_string
        #self.ll_model = ll_model
        super().__init__(intents=intents)


    #-----------Event Functions-----------#
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
  
    async def on_message(self, message):
        if message.author == self.user:
            return

        needs_response = False
        if message.type == discord.MessageType.reply:
            ref_message_id = message.reference.message_id
            ref_message = await message.channel.fetch_message(ref_message_id)
            if ref_message.author == self.user:
                needs_response = True
        if "<@1180692348196376626>" in message.content:
            needs_response = True
        if not needs_response:
            return

        author_name = "Minaro" if message.author.id == 308746205859414028 else message.author.display_name
        content = message.clean_content
        print(f'\nMessage from {author_name}: {content}')
        
        response = "No response generated"
        async with message.channel.typing():
            proc_message = await self.generate_proc_message(message.channel)
            response = await self.send_to_agent(proc_message)

        await message.reply(response)
    

    #-----------Accessory Functions-----------#
    async def generate_proc_message(self, channel, message_count=10):
        llm_messages = [{}]*(message_count+1)
        llm_messages[0] = {
            "role": "system", 
            "content": self.personality_string
        }

        i=len(llm_messages)-1
        async for message in channel.history(limit=message_count):
            content = message.clean_content

            #API reqiest. Consider changing to get_member instead
            author_member = await channel.guild.fetch_member(message.author.id) if channel.guild else message.author
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
            "temperature": 0.5,
            "max_tokens": 50,
            "stop": ["###"]
        }
        #pprint.pprint(proc_message)
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
                        return return_message
                    else:
                        print(f"Request failed with status code {response.status}: {await response.text()}")
                        return "My speech center appears to be having a problem. Please let Minaro know and he'll fix me."
        except Exception as e:
            print(f"An error occurred: {e}")
            return "It looks like my speech center has been shut down. If you pester Minaro enough, he might turn it on."



api_keys = configparser.ConfigParser()
api_keys.read('api_keys.ini')
discord_key = api_keys['API']['discord']

intents = discord.Intents.default()
intents.message_content = True
with open('./personality.txt', 'r') as file:
    personality = file.read()

client = GlitchClient(personality, intents=intents)
client.run(discord_key)