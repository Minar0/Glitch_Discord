from llama_cpp import Llama
llm = Llama(model_path="C:/Users/William/Documents/Projects/Programming/Glitch_discord/llama-gpt/models/ggml_llava-v1.5-13b/ggml-model-q5_k.gguf")

print(llm.create_chat_completion(
      messages = [
        {
          "role": "system",
          "content": "A chat between a curious user and an artificial intelligence assitant. The assistant gives helpful, detailed, and polite answers to the user's questions. The assistant callse functions with appropriate input when necessary"
        },
        {
          "role": "user",
          "content": "Extract Jason is 25 years old"
        }
      ]
))