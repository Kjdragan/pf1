import subprocess
import os
import webbrowser

# Paths
input_path = r"C:\Users\kevin\repos\pf1\Kevin\gitdiagram.mmd"
output_path = r"C:\Users\kevin\repos\pf1\Kevin\gitdiagram.png"
puppeteer_config_path = r"C:\Users\kevin\repos\pf1\Kevin\puppeteer-config.json"

# Image quality settings
width = 2000  # Width in pixels
height = 2000  # Height in pixels (will maintain aspect ratio)
scale = 2.0    # Scale factor (2.0 = double resolution)

# Find the mmdc executable path
# Common locations for npm global installs
possible_mmdc_paths = [
    r"C:\Users\kevin\AppData\Roaming\npm\mmdc.cmd",  # User install
    r"C:\Users\kevin\AppData\Roaming\npm\mmdc",
    r"C:\Program Files\nodejs\node_modules\@mermaid-js\mermaid-cli\bin\mmdc.js",
    r"C:\Program Files\nodejs\node_modules\.bin\mmdc",
    r"C:\Users\kevin\AppData\Roaming\npm\node_modules\@mermaid-js\mermaid-cli\bin\mmdc.js"
]

# Find the first path that exists
mmdc_path = None
for path in possible_mmdc_paths:
    if os.path.exists(path):
        mmdc_path = path
        print(f"Found mmdc at: {mmdc_path}")
        break

if not mmdc_path:
    # Try to find it using where command (Windows equivalent of which)
    try:
        result = subprocess.run(["where", "mmdc"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            mmdc_path = result.stdout.strip().split('\n')[0]
            print(f"Found mmdc using 'where' command: {mmdc_path}")
    except Exception as e:
        print(f"Error trying to locate mmdc: {e}")

# Mermaid CLI command
try:
    if not mmdc_path:
        raise FileNotFoundError("Could not find mmdc executable")

    print(f"Executing: {mmdc_path}")
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Puppeteer config: {puppeteer_config_path}")
    print(f"Image size: {width}x{height}, Scale: {scale}")

    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"❌ Input file does not exist: {input_path}")
        exit(1)

    # Check if puppeteer config exists
    if not os.path.exists(puppeteer_config_path):
        print(f"❌ Puppeteer config file does not exist: {puppeteer_config_path}")
        exit(1)

    # Create command based on whether it's a .cmd file or .js file
    if mmdc_path.endswith('.cmd'):
        # For .cmd files, run directly
        command = [
            mmdc_path,
            "-i", input_path,
            "-o", output_path,
            "--backgroundColor", "transparent",
            "--puppeteerConfigFile", puppeteer_config_path,
            "--width", str(width),
            "--height", str(height),
            "--scale", str(scale)
        ]
    elif mmdc_path.endswith('.js'):
        # For .js files, run with node
        command = [
            "node",
            mmdc_path,
            "-i", input_path,
            "-o", output_path,
            "--backgroundColor", "transparent",
            "--puppeteerConfigFile", puppeteer_config_path,
            "--width", str(width),
            "--height", str(height),
            "--scale", str(scale)
        ]
    else:
        # For other executables
        command = [
            mmdc_path,
            "-i", input_path,
            "-o", output_path,
            "--backgroundColor", "transparent",
            "--puppeteerConfigFile", puppeteer_config_path,
            "--width", str(width),
            "--height", str(height),
            "--scale", str(scale)
        ]

    # Execute the command
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print(f"Command output: {result.stdout}")

    print(f"✅ High-resolution diagram successfully generated: {output_path}")

    # Optionally open the output file (Windows default image viewer)
    os.startfile(output_path)

except FileNotFoundError:
    print("❌ Could not find the mmdc executable.")
    print("Make sure you've installed Mermaid CLI correctly:")
    print("    npm install -g @mermaid-js/mermaid-cli")
    print("\nTry running these commands to troubleshoot:")
    print("    where mmdc")
    print("    npm list -g | findstr mermaid")
except subprocess.CalledProcessError as e:
    print(f"❌ Mermaid CLI failed with error code {e.returncode}:")
    print(f"Command: {' '.join(e.cmd)}")
    print(f"Output: {e.stdout}")
    print(f"Error: {e.stderr}")

    # Check for Chrome/Puppeteer error
    if "Could not find Chrome" in e.stderr:
        print("\n🔧 It looks like Puppeteer can't find Chrome. Try installing it with:")
        print("    npx puppeteer browsers install chrome-headless-shell")
        print("\nOr try using a different renderer with the --puppeteerConfigFile option:")
        print("    mmdc -i input.md -o output.png --puppeteerConfigFile puppeteer-config.json")
        print("\nExample puppeteer-config.json:")
        print("""
{
  "executablePath": "C:\\Users\\kevin\\.cache\\puppeteer\\chrome-headless-shell\\win64-135.0.7049.42\\chrome-headless-shell-win64\\chrome-headless-shell.exe",
  "args": ["--no-sandbox"]
}
        """)
except Exception as e:
    print(f"❌ Error: {str(e)}")
