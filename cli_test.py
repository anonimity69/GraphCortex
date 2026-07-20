import pexpect
import sys

def run():
    print("Spawning CLI...")
    child = pexpect.spawn("/Users/shrayanendranathmandal/Developer/GraphCortex/.venv/bin/python src/graph_cortex/interfaces/cli/main.py", encoding='utf-8', timeout=120)
    
    child.expect("User > ")
    
    print("Sending query...")
    child.sendline("Can you tell me about the battery issues in Project Orion?")
    
    print("Waiting for Agent response...")
    child.expect("Agent:")
    child.expect("User > ")
    
    agent_response = child.before.strip()
    
    with open("cli_output_capture.txt", "w") as f:
        f.write(agent_response)
        
    print("Response captured. Exiting...")
    child.sendline("/exit")
    child.expect(pexpect.EOF)

if __name__ == "__main__":
    run()
