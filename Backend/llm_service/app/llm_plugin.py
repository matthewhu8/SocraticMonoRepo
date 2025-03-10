from abc import ABC, abstractmethod 
from transformers import AutoTokenizer, AutoModelForCausalLM


# abstract class to be inherited; think of it likes an interface in Java
class LLMPlugin(ABC):
    @abstractmethod
    def generate(self, prompt, maxToken):
        pass

class llamaPlugin(LLMPlugin):
    def __init__(self, model_path: str):
        print("Loading Llama model...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")
        print("Llama model finished loading!")

    def generate(self, prompt: str, max_tokens: int = 128) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        print("Converted prompt to input tensors!")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        print("Converted input tensors to model device!")
        print("Generating response...")
        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            do_sample=True
        )
        print("Response generation completed!")
        generated_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        completion = generated_text[len(prompt):].strip()
        return completion

        