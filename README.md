# GlitchOS-Discord
A small chatbot I built. Runs on Discord and uses Ollama as a backend for text generation. Uses the same name and personality as my Android virtual assistant but with an LLM text generator and no other usability.

<br />
If you want to run this yourself, you'll have to run ollama as a webserver and use deepseek. I just run it locally and connect to it via localhost. You can change the model you wanna use, but deepseek works well for me
<br />
You'll also have to make your own Discord bot and grab it's key. I use a .ini file called api_keys.ini to store secrets. Put the secret under [API] and call it discord. There's a template under api_keys_template.ini
<br />
Feel free to change the personality.txt and/or name, just credit me if you make your own bot off my work. Also let me know, cause people using my code is pretty neat. <br />
