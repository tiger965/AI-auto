# ui/cli/__init__.py
from .commands import register_commands
from .prompt import setup_prompt
from .themes import apply_theme

def initialize_cli():
    """Initialize the CLI interface for Window 7.3"""
    # Apply the default theme
    apply_theme("default")
    
    # Setup the command prompt
    setup_prompt()
    
    # Register all available commands
    register_commands()
    
    # Start the CLI loop
    start_cli_loop()
    
def start_cli_loop():
    """Main CLI interaction loop"""
    from .helpers import parse_input, advanced_parse_input
    from .formatters import format_output
    
    running = True
    while running:
        try:
            # Display prompt and get user input
            user_input = input_with_prompt()
            
            # Parse the natural language input (using advanced NLP)
            command, args = advanced_parse_input(user_input)
            
            # Execute the command
            result = execute_command(command, args)
            
            # Format and display the result
            format_output(result)
            
        except KeyboardInterrupt:
            print("\nExiting CLI...")
            running = False
        except Exception as e:
            print(f"Error: {str(e)}")

def input_with_prompt():
    """Get input with customized prompt"""
    from .prompt import get_prompt
    return input(get_prompt())

def execute_command(command, args):
    """Execute the given command with arguments"""
    from .commands import get_command
    cmd_func = get_command(command)
    if cmd_func:
        return cmd_func(args)
    else:
        return {"error": f"Unknown command: {command}"}