import sys
import os
import subprocess

# Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print(f"{CYAN}=========================================={RESET}")
    print(f"{CYAN}       FreeNet Main Menu by AhmadOo       {RESET}")
    print(f"{CYAN}=========================================={RESET}")

def run_script(script_name):
    """
    Runs a script located in the 'scripts' directory.
    """
    script_path = os.path.join("scripts", script_name)
    if not os.path.exists(script_path):
        print(f"{RED}Error: Script '{script_name}' not found in 'scripts' folder.{RESET}")
        input("Press Enter to continue...")
        return
    
    print(f"{GREEN}Starting {script_name} ...{RESET}")
    print(f"{YELLOW}------------------------------------------{RESET}")
    try:
        # Run the script using the current python executable
        # checks=False allows it to fail without throwing Python exception here, 
        # so we can handle the exit code if we want (but we just let it run).
        subprocess.run([sys.executable, script_path], check=False)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Script interrupted by user.{RESET}")
    except Exception as e:
        print(f"{RED}An error occurred while trying to run the script: {e}{RESET}")
    
    print(f"{YELLOW}------------------------------------------{RESET}")
    print(f"{GREEN}Script finished execution.{RESET}")
    input("Press Enter to return to the main menu...")

def main():
    while True:
        clear_screen()
        print_banner()
        print(f"{GREEN}[1]{RESET} Host Finder")
        print(f"{GREEN}[2]{RESET} Direct Scanner")
        print(f"{GREEN}[3]{RESET} SSL Scanner")
        print(f"{GREEN}[4]{RESET} Proxy Scanner")
        print(f"{GREEN}[5]{RESET} Payload Tester")
        print(f"{RED}[6]{RESET} Exit")
        print(f"{CYAN}=========================================={RESET}")
        
        choice = input("Select an option: ").strip().lower()
        
        if choice == '1':
            run_script("mode_find.py")
        elif choice == '2':
            run_script("mode_direct.py")
        elif choice == '3':
            run_script("mode_ssl.py")
        elif choice == '4':
            run_script("mode_proxy.py")
        elif choice == '5':
            run_script("mode_payload.py")
        elif choice == '6':
            print("Exiting...")
            break
        else:
            input(f"{RED}Invalid option '{choice}'. Press Enter to try again.{RESET}")

if __name__ == "__main__":
    try:
        # Enable colors for Windows terminal if needed
        os.system('') 
        main()
    except KeyboardInterrupt:
        print("\nGoodbye!")
