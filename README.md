# GlitchOS-Discord
A small chatbot I built. Runs on Discord and uses LlamaGPT as a backend for speech synthesis. Uses the same name and personality as my Android virtual assistant but with an LLM speech synthesizer and no other usability.

Uhhh, I added llama-gpt as a submodule. No idea if that's correct or not.
<br />
If you want to run this yourself, you'll have to run llama-gpt in webserver mode. I just run it locally and connect to it via localhost. There is a python library that should let you run it directly without a webserver, but I couldn't get it to work.
<br />
You'll also have to make your own Discord bot and grab it's key. I use a .ini file called api_keys.ini to store secrets. Put the secret under [API] and call it discord. There's a template under api_keys_template.ini
<br />
Feel free to change the personality.txt and/or name, just credit me if you make your own bot off my work. Also let me know, cause people using my code is pretty neat. <br />

LlamaGPT:
https://github.com/getumbrel/llama-gpt.git
