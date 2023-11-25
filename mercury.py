from llama_cpp.llama_types import ChatCompletionMessage
from llama_cpp import Llama
import logging
import json
from advanced_prompts import SYSTEM_PROMPT
import inspect
from tools import *
from llama_cpp import LlamaGrammar, Llama

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

llm = Llama(
    model_path="./models/openhermes-2.5-mistral-7b-16k.Q8_0.gguf", n_ctx=16384, n_gpu_layers=35)


def call_function_from_response(response):
    # Parse the response assuming it's a JSON string
    results = []
    for response_data in response:
        # Iterate over each function call in the response
        func_call = response_data.get('function_call', {})
        func_name = func_call.get("function_name")
        func_args = func_call.get("function_args", {})
        if func_name and func_name in globals():
            function_to_call = globals()[func_name]
            result = None

            # Inspect the function to get its parameters
            params = inspect.signature(function_to_call).parameters

            # Call the function with its arguments
            if len(params) == 1:
                # Single argument, unpack the dict and pass the value
                arg_name = next(iter(params))
                x = {}
                x["function_call"] = {}
                x["function_call"]["function_name"] = func_name
                x["function_call"]["function_args"] = func_args
                x["function_call"]["function_result"] = function_to_call(
                    func_args[arg_name])
                result = x["function_call"]["function_result"]
                results.append(x)
            else:
                # Multiple arguments, pass the dict as kwargs
                x = {}
                x["function_call"] = {}
                x["function_call"]["function_name"] = func_name
                x["function_call"]["function_args"] = func_args
                x["function_call"]["function_result"] = function_to_call(
                    **func_args)
                result = x["function_call"]["function_result"]
                results.append(x)

            print(f"Result of calling {func_name}:", result)
        else:
            print(f"Function '{func_name}' is not available.")
    return results


system_content = SYSTEM_PROMPT.format(funcs=json.dumps(functions()))

prompt_template = """
<|im_start|>system
  {system_content}
<|im_end|>

<|im_start|>user
  {user_content}
<|im_end|>

<|im_start|>assistant
"""

output_chars = []
while True:
    grammar = LlamaGrammar.from_file("./json_arr.gbnf")
    user_content = input("Prompt: ").strip()
    prompt_ = prompt_template.format(
        system_content=system_content, user_content=user_content)

    output = llm(prompt=prompt_, stop=["<|im_end|>"], echo=False, stream=True,
                 mirostat_mode=2, mirostat_tau=4.0, mirostat_eta=1.1, grammar=grammar)

    count = 0
    for oo in output:
        text = oo["choices"][0]["text"]
        print(text, end="")
        output_chars.append(text)

    print("\n")

    try:
        parsed = json.loads(''.join(output_chars))
        function_output = call_function_from_response(parsed)
        print(function_output)
        prompt_ += "<|im_start|>assistant"+"\n" + \
            function_output[0]["function_result"]+"<|im_end|>"
        output_chars = []
        output = llm(prompt=f"Try to answer the user's original question: {user_content} based on the function output: {function_output}", stop=[
                     "<|im_end|>"], echo=False, stream=True, mirostat_mode=2, mirostat_tau=4.0, mirostat_eta=1.1, grammar=grammar)
        for oo in output:
            text = oo["choices"][0]["text"]
            print(text, end="")
            output_chars.append(text)
        print(output_chars)
        print("\n")
    except Exception as e:
        print(e)

# text = json.loads(output["choices"][0]["text"])
# func_name = text["function_name"]
# func_args = text["function_args"]
# print(f"{func_name}: {func_args}")

# print(json.dumps(output, indent=2))
