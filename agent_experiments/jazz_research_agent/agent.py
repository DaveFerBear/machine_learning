import anthropic
from dotenv import load_dotenv
load_dotenv()

from typing import List


class JazzAgent(object):
    def __init__(self):
        self.client = client = anthropic.Anthropic()
        self.system_prompt = '''You are an expert jazz researcher. You have access to a corpus of data that you should refer to.'''
        self.messages = []
        self.load_corpus()
        
    
    def load_corpus(self):
        self.corpus = []
        with open("./jazz_research_agent/corpus.txt") as corpus:
            for line in corpus:
                l = line.strip()
                if l:
                    self.corpus.append(l)
        print(f'corpus loaded with {len(self.corpus)} lines')


    def reset(self):
        self.messages = []

    def search_corpus(self, k) -> List[str]:
        return [l for l in self.corpus if k.lower() in l.lower()] # janky "RAG"


    def print_conversation(self):
        for m in self.messages:
            print(m)
            print("*"*10)


    def prompt(self, user_message, is_first_call=True):
        if is_first_call:
            self.messages.append({'role': 'user', 'content': user_message})
        res = self.client.messages.create(
            system=self.system_prompt,
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=self.messages,
                       tools=[{
                "name": "search_corpus",
                "description": "Search the jazz corpus for matching lines (musicians, albums, facts).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Keywords to search for.",
                        },
                    },
                    "required": ["query"],
                },
            }],
        )
        self.messages.append({'role': 'assistant', 'content': res.content})
        if res.stop_reason == 'tool_use':
            tool_results = []
            for m in res.content:
                if m.type == 'tool_use':
                    if m.name == 'search_corpus':
                        search_res = self.search_corpus(m.input['query'])
                        tool_results.append({
                            'type': 'tool_result',
                            'tool_use_id': m.id,
                            'content': '\n'.join(search_res),
                        })
                    else:
                        raise Exception("Invalid tool ", m.name)
            self.messages.append({'role': 'user', 'content': tool_results})
            return self.prompt(None, is_first_call=False)
        return '\n'.join(b.text for b in res.content if b.type == 'text')



def test():
    a1 = JazzAgent()
    res = a1.search_corpus("Marcus Vega")
    assert all(["Marcus Vega" in r for r in res])

    res = a1.prompt("What instrument did Marcus Vega play?")
    print(res)
    a1.reset()

    a2 = JazzAgent()
    res2 = a2.prompt("Which musicians played piano? Return the musician as a list, and what search queries you tried.")
    print(res2)

    a2.print_conversation()
    

if __name__ == '__main__':
    test()