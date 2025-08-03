import os
from time import sleep

try:
    import openai
    from openai import OpenAI
except ImportError as e:
    pass

from lcb_runner.runner.base_runner import BaseRunner


class OnlineRunner(BaseRunner):
    client = OpenAI(
        api_key=os.getenv("ONLINE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    def __init__(self, args, model):
        super().__init__(args, model)
        self.client_kwargs: dict[str | str] = {
            "model": "qwen3-235b-a22b",
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "top_p": args.top_p,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "n": 1,
            "timeout": args.openai_timeout,
            # "stop": args.stop, --> stop is only used for base models currently
        }

    def _run_single(self, prompt: list[dict[str, str]]) -> list[str]:
        assert isinstance(prompt, list)

        def __run_single(counter):
            try:
                response = self.client.chat.completions.create(
                    messages=prompt,
                    **self.client_kwargs,
                )
                content = response.choices[0].message.content
                return content
            except (
                openai.APIError,
                openai.RateLimitError,
                openai.InternalServerError,
                openai.OpenAIError,
                openai.APIStatusError,
                openai.APITimeoutError,
                openai.InternalServerError,
                openai.APIConnectionError,
            ) as e:
                print("Exception: ", repr(e))
                print("Sleeping for 30 seconds...")
                print("Consider reducing the number of parallel processes.")
                sleep(30)
                return OnlineRunner._run_single(prompt)
            except Exception as e:
                print(f"Failed to run the model for {prompt}!")
                print("Exception: ", repr(e))
                raise e

        outputs = []
        try:
            for _ in range(self.args.n):
                outputs.append(__run_single(10))
        except Exception as e:
            raise e
        return outputs 